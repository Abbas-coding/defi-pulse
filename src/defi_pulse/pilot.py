"""Bounded feasibility extraction; no features, labels, or models are fabricated."""

import argparse
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from demos.graph_demo.demo import (
    Client, DEFAULT_SUBGRAPH, DemoError, HOUR_FIELDS, POOL_FIELDS, PROBE, WETH,
    read_settings, save_json, verify_schema,
)

HOUR = 3600
DAY = 24 * HOUR
POLICY = "empty_hour_assumed_no_trades_v1"


def utc(value: int) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def date_seconds(value: str) -> int:
    return int(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def validate_hours(records: object, start: int, end: int) -> list[dict]:
    """Distinguish a valid empty collection from malformed or partial responses."""
    if not isinstance(records, list):
        raise DemoError("Hourly response must be a list; null is not inactivity.")
    seen = set()
    for record in records:
        if not isinstance(record, dict) or not set(HOUR_FIELDS.split()) <= record.keys():
            raise DemoError("Incomplete hourly record; cannot infer inactivity.")
        try:
            stamp = int(record["periodStartUnix"])
        except (TypeError, ValueError):
            raise DemoError("Invalid hourly timestamp.") from None
        if stamp % HOUR or not start <= stamp < end or stamp in seen:
            raise DemoError("Out-of-range, duplicate, or unaligned hourly bucket.")
        seen.add(stamp)
    return records


def window_rows(pool: dict, records: list[dict], hours: int) -> list[dict]:
    """Keep only completed buckets; a valid empty hour carries an assumption."""
    created = int(pool["createdAtTimestamp"])
    cutoff = created + hours * HOUR
    by_start = {int(record["periodStartUnix"]): record for record in records}
    rows = []
    # The creation bucket has no possible activity before the pool existed.
    for start in range(created // HOUR * HOUR, cutoff // HOUR * HOUR, HOUR):
        record = by_start.get(start)
        rows.append({
            "pool_address": pool["id"], "window_hours": hours,
            "cutoff_utc": utc(cutoff), "bucket_start_utc": utc(start),
            "bucket_end_utc": utc(start + HOUR),
            "quality": "observed" if record is not None else "missing",
            "assumed_no_trades": record is None, "missingness_policy": POLICY,
            **{field: record[field] if record is not None else None
               for field in HOUR_FIELDS.split()},
        })
    return rows


def endpoint(pool: dict, records: list[dict], elapsed: int) -> dict:
    """Expose candidate endpoint evidence without claiming an exact as-of state."""
    cutoff = int(pool["createdAtTimestamp"]) + elapsed
    safe = [r for r in records if int(r["periodStartUnix"]) + HOUR <= cutoff]
    last = max(safe, key=lambda r: int(r["periodStartUnix"]), default=None)
    return {
        "pool_address": pool["id"], "requested_as_of_utc": utc(cutoff),
        "bucket_start_utc": utc(int(last["periodStartUnix"])) if last else None,
        "bucket_end_utc": utc(int(last["periodStartUnix"]) + HOUR) if last else None,
        "tvl_usd": last["tvlUSD"] if last else None,
        "state_age_upper_bound_seconds": cutoff - int(last["periodStartUnix"]) if last else None,
        "quality": "candidate_bucket_state" if last else "missing",
        "label": None,
        "label_blocker": "Exact observation time and accepted staleness policy unresolved",
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def canonical_pool(data: dict) -> tuple[str | None, str | None]:
    """Require earliest WETH pool across both orientations, outside sampling dates too."""
    unique = {p["id"]: p for p in data["side0"] + data["side1"]}
    ordered = sorted(unique.values(), key=lambda p: (int(p["createdAtTimestamp"]), p["id"]))
    if not ordered:
        return None, "canonical_lookup_empty"
    if len(ordered) > 1 and ordered[0]["createdAtTimestamp"] == ordered[1]["createdAtTimestamp"]:
        return None, "earliest_creation_tie_requires_review"
    return ordered[0]["id"], None


def run(args: argparse.Namespace) -> dict:
    start, end = date_seconds(args.start), date_seconds(args.end)
    if not start < end or end + 9 * DAY > time.time():
        raise DemoError("Use a nonempty historical range with eight days plus a one-day buffer elapsed.")
    if not 1 <= args.pools <= 30 or not 1 <= args.max_requests <= 100:
        raise DemoError("Pilot requires 1–30 pools and 1–100 maximum network attempts.")
    settings = read_settings()
    client = Client(settings.get("GRAPH_SUBGRAPH_ID") or DEFAULT_SUBGRAPH,
        settings.get("GRAPH_API_KEY", ""), args.output / "cache",
        args.max_requests, args.offline)
    began = time.monotonic()
    probe = client.query(PROBE, {})
    scalar = verify_schema(probe)
    meta = probe["_meta"]
    if meta["hasIndexingErrors"]:
        raise DemoError("Source reports indexing errors.")
    block = int(meta["block"]["number"])
    discovery = '''query PilotDiscovery($weth: SCALAR!, $start: BigInt!, $end: BigInt!, $block: Int!) {
      weth0: pools(first: 100, block: {number: $block}, orderBy: id, orderDirection: asc,
        where: {token0: $weth, createdAtTimestamp_gte: $start, createdAtTimestamp_lt: $end}) { FIELDS }
      weth1: pools(first: 100, block: {number: $block}, orderBy: id, orderDirection: asc,
        where: {token1: $weth, createdAtTimestamp_gte: $start, createdAtTimestamp_lt: $end}) { FIELDS }
    }'''.replace("SCALAR", scalar).replace("FIELDS", POOL_FIELDS)
    available_filters = {f["name"] for f in probe["poolFilter"]["inputFields"]}
    if "createdAtTimestamp_gte" not in available_filters:
        raise DemoError("Source lacks bounded creation-date filtering.")
    found = client.query(discovery, {"weth": WETH, "start": str(start), "end": str(end), "block": block})
    if not all(isinstance(found.get(side), list) for side in ("weth0", "weth1")):
        raise DemoError("Malformed discovery response.")
    candidates = {p["id"]: p for p in found["weth0"] + found["weth1"]}
    for pool in candidates.values():
        if (not all(re.fullmatch(r"0x[0-9a-fA-F]{40}", pool[k]["id"]) for k in ("token0", "token1"))
                or not re.fullmatch(r"0x[0-9a-fA-F]{40}", pool["id"])
                or WETH not in {pool["token0"]["id"].lower(), pool["token1"]["id"].lower()}
                or not start <= int(pool["createdAtTimestamp"]) < end):
            raise DemoError("Unexpected pool identity or creation time.")
    selected, exclusions, tokens = [], [], set()
    for pool in sorted(candidates.values(), key=lambda p: p["id"]):
        token = pool["token1"] if pool["token0"]["id"].lower() == WETH else pool["token0"]
        if token["id"].lower() in tokens:
            exclusions.append({"pool_address": pool["id"], "reason": "token_already_selected"})
            continue
        query = '''query CanonicalPool {
          side0: pools(first: 2, block: {number: BLOCK}, orderBy: createdAtTimestamp, orderDirection: asc,
            where: {token0: "WETH", token1: "TOKEN"}) {id createdAtTimestamp}
          side1: pools(first: 2, block: {number: BLOCK}, orderBy: createdAtTimestamp, orderDirection: asc,
            where: {token1: "WETH", token0: "TOKEN"}) {id createdAtTimestamp}
        }'''.replace("BLOCK", str(block)).replace("WETH", WETH).replace("TOKEN", token["id"])
        canonical, reason = canonical_pool(client.query(query, {}))
        if reason or canonical != pool["id"]:
            exclusions.append({"pool_address": pool["id"], "reason": reason or "not_earliest_weth_pool"})
            continue
        tokens.add(token["id"].lower())
        selected.append(pool)
        if len(selected) == args.pools:
            break
    histories, rows, outcomes = {}, [], []
    for pool in selected:
        created = int(pool["createdAtTimestamp"])
        base = created // HOUR * HOUR
        # 25 buckets maximum for early history; endpoint searches look back 24h.
        query = '''query PilotHistory {
          early: poolHourDatas(first: 26, block: {number: BLOCK}, orderBy: periodStartUnix, orderDirection: asc,
            where: {pool: "POOL", periodStartUnix_gte: BASE, periodStartUnix_lt: EARLY_END}) {FIELDS}
          day8: poolHourDatas(first: 26, block: {number: BLOCK}, orderBy: periodStartUnix, orderDirection: asc,
            where: {pool: "POOL", periodStartUnix_gte: LATE_START, periodStartUnix_lt: LATE_END}) {FIELDS}
        }'''.replace("BLOCK", str(block)).replace("POOL", pool["id"]).replace("FIELDS", HOUR_FIELDS)
        for key, value in {"BASE": base, "EARLY_END": base + DAY + HOUR,
                           "LATE_START": base + 7 * DAY, "LATE_END": base + 8 * DAY + HOUR}.items():
            query = query.replace(key, str(value))
        data = client.query(query, {})
        early = validate_hours(data.get("early"), base, base + DAY + HOUR)
        late = validate_hours(data.get("day8"), base + 7 * DAY, base + 8 * DAY + HOUR)
        histories[pool["id"]] = data
        for hours in (1, 6, 24):
            rows.extend(window_rows(pool, early, hours))
        outcomes.extend([endpoint(pool, early, DAY), endpoint(pool, late, 8 * DAY)])
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in {"schema": probe, "pools": selected, "histories": histories,
                       "exclusions": exclusions, "outcome_states": outcomes}.items():
        save_json(args.output / f"{name}.json", data)
    write_csv(args.output / "pool_hours.csv", rows)
    write_csv(args.output / "outcome_states.csv", outcomes)
    summary = {str(hours): {
        "permitted_buckets": sum(r["window_hours"] == hours for r in rows),
        "observed_buckets": sum(r["window_hours"] == hours and r["quality"] == "observed" for r in rows),
        "pools_with_observations": len({r["pool_address"] for r in rows
                                        if r["window_hours"] == hours and r["quality"] == "observed"}),
    } for hours in (1, 6, 24)}
    manifest = {
        "purpose": "research feasibility pilot; no model training or final labels",
        "created_at_utc": utc(int(time.time())), "source_metadata": meta,
        "schema_sha256": hashlib.sha256(json.dumps(probe, sort_keys=True).encode()).hexdigest(),
        "candidate_start_utc": utc(start), "candidate_end_exclusive_utc": utc(end),
        "candidate_count": len(candidates), "selected_count": len(selected),
        "requested_pools": args.pools, "exclusions": exclusions,
        "discovery_capped": any(len(found[s]) == 100 for s in ("weth0", "weth1")),
        "selection": "Address order within up to 100 candidates per WETH side; globally earliest WETH pool per token",
        "missingness_policy": POLICY, "windows": summary,
        "endpoint_candidate_count": sum(r["tvl_usd"] is not None for r in outcomes),
        "valid_label_count": 0, "network_attempts": client.requests,
        "cache_hits": client.hits, "max_requests": args.max_requests,
        "elapsed_seconds": round(time.monotonic() - began, 3),
        "requests": client.records,
        "cache_bytes": sum(f.stat().st_size for f in client.cache.glob("*.json")),
        "limitations": ["No final labels until endpoint timing/staleness and zero-outcome policy are settled",
                        "Hourly absence means assumed no trades, not measured zero TVL or price",
                        "Snapshot lifetime TVL is metadata only; not a selection threshold or early feature",
                        "CSV normalization used during source probe; Parquet not yet implemented",
                        "Bounded address sample is not a representative population sample"],
    }
    manifest["artifact_sha256"] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                                  for f in args.output.iterdir() if f.is_file() and f.name != "manifest.json"}
    save_json(args.output / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-10-01")
    parser.add_argument("--end", default="2026-10-08")
    parser.add_argument("--pools", type=int, default=20)
    parser.add_argument("--max-requests", type=int, default=80)
    parser.add_argument("--output", type=Path, default=Path("data/pilot"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args)
    except DemoError as error:
        print(f"Pilot stopped: {error} No success claimed; successful responses remain cached.")
        raise SystemExit(1) from None
    except (KeyError, ValueError, TypeError) as error:
        # Do not echo external values or credentials in exceptions.
        print(f"Pilot stopped ({type(error).__name__}); inspect cached schema and request budget. No success claimed.")
        raise SystemExit(1) from None
    print(json.dumps({k: v for k, v in result.items() if k != "requests"}, indent=2))


if __name__ == "__main__":
    main()
