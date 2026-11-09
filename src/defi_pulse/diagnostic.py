"""Fixed-cohort, 200-pool activity diagnostic with bounded, cached extraction."""

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from demos.graph_demo.demo import Client, DEFAULT_SUBGRAPH, HOUR_FIELDS, POOL_FIELDS, DemoError, read_settings, save_json, verify_schema
from .historical_states import run as historical_run
from .pilot import DAY, HOUR, canonical_pool, date_seconds, utc, validate_hours, window_rows, write_csv

PERIODS = [("2026-01-01", "2026-01-08"), ("2026-04-01", "2026-04-08"),
           ("2026-07-01", "2026-07-08"), ("2026-10-01", "2026-10-08")]
SEED = "defi-pulse-diagnostic-200-v1"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
POOL_PAGE = 200
SWAP_PAGE = 1000


def rank(pool: dict) -> str:
    return hashlib.sha256(f"{SEED}:{pool['id']}".encode()).hexdigest()


def validate_pool(pool: dict) -> None:
    for value in (pool["id"], pool["token0"]["id"], pool["token1"]["id"]):
        if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-f]{40}", value):
            raise DemoError("Unexpected pool or token identity.")
    if WETH not in (pool["token0"]["id"], pool["token1"]["id"]):
        raise DemoError("Non-WETH pool returned.")


def collect_page(records: object, cursor: str, pool: dict, seen: set,
                 start_offset: int = 0, end_offset: int = DAY) -> str:
    """Reject repeated or out-of-window events instead of silently undercounting."""
    if not isinstance(records, list) or len(records) > SWAP_PAGE:
        raise DemoError("Swap page must be a list; null is not zero activity.")
    created = int(pool["createdAtTimestamp"])
    for event in records:
        if (not isinstance(event, dict) or event["id"] <= cursor or event["id"] in seen
                or not created + start_offset <= int(event["timestamp"]) < created + end_offset
                or not event.get("transaction", {}).get("id")):
            raise DemoError("Malformed, duplicate, unsorted, or out-of-window swap page.")
        amount = Decimal(event["amountUSD"])
        if not amount.is_finite() or amount < 0:
            raise DemoError("Invalid swap USD volume.")
        cursor = event["id"]
        seen.add(cursor)
    return cursor


def activity(pool: dict, swaps: list[dict], hourly: list[dict], complete: bool) -> dict:
    """One pool summary; swap and transaction counts are explicitly distinct."""
    created = int(pool["createdAtTimestamp"])
    token = pool["token1"] if pool["token0"]["id"] == WETH else pool["token0"]
    result = {"pool_address": pool["id"], "target_token_address": token["id"],
              "symbol": token["symbol"], "created_at_utc": utc(created), "period": pool["period"],
              "swap_history_complete": complete, "usd_pricing_quality": "unverified_source_valuation"}
    for hours in (1, 6, 24):
        events = [e for e in swaps if int(e["timestamp"]) < created + hours * HOUR]
        permitted = window_rows(pool, hourly, hours)
        result.update({
            f"swap_count_{hours}h": len(events) if complete else None,
            f"swap_count_lower_bound_{hours}h": len(events),
            f"swap_transaction_count_{hours}h": len({e["transaction"]["id"] for e in events}) if complete else None,
            f"active_elapsed_hours_{hours}h": len({(int(e["timestamp"]) - created) // HOUR for e in events}) if complete else None,
            f"swap_volume_usd_{hours}h": str(sum((Decimal(e["amountUSD"]) for e in events), Decimal(0))) if complete else None,
            f"observed_hourly_records_{hours}h": sum(r["quality"] == "observed" for r in permitted),
            f"completed_bucket_tx_count_{hours}h": sum(int(r["txCount"]) for r in permitted if r["quality"] == "observed"),
        })
    present = {int(r["periodStartUnix"]) for r in hourly}
    safe_end = (created + DAY) // HOUR * HOUR
    result["absent_completed_buckets_with_swaps"] = len({
        int(e["timestamp"]) // HOUR * HOUR for e in swaps
        if int(e["timestamp"]) // HOUR * HOUR not in present and int(e["timestamp"]) < safe_end})
    return result


def run(args: argparse.Namespace) -> dict:
    if not 200 <= args.max_requests <= 1000:
        raise DemoError("Use a bounded request cap of 200–1000 attempts.")
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    settings = read_settings()
    client = Client(settings.get("GRAPH_SUBGRAPH_ID") or DEFAULT_SUBGRAPH,
                    settings.get("GRAPH_API_KEY", ""), out / "cache", args.max_requests, args.offline)
    began = time.monotonic()
    # This query is shared with the initial schema verification.
    from demos.graph_demo.demo import PROBE
    query = PROBE.replace("query DemoSchema", "query DiagnosticSchema").replace(
        "\n}", '\n swapType: __type(name: "Swap") {fields {name}}\n swapFilter: __type(name: "Swap_filter") {inputFields {name}}\n}')
    schema = client.query(query, {})
    verify_schema(schema)
    if not {"pool", "timestamp_gte", "timestamp_lt", "id_gt"} <= {f["name"] for f in schema["swapFilter"]["inputFields"]}:
        raise DemoError("Required swap pagination filters unavailable.")
    if not {"id", "timestamp", "amountUSD", "transaction"} <= {f["name"] for f in schema["swapType"]["fields"]}:
        raise DemoError("Required swap fields unavailable.")
    meta = schema["_meta"]
    if meta["hasIndexingErrors"]:
        raise DemoError("Indexing errors reported.")
    head = int(meta["block"]["number"])
    selected, exclusions, funnel, used_tokens = [], [], [], set()
    for start_date, end_date in PERIODS:
        start, end = date_seconds(start_date), date_seconds(end_date)
        if end + 9 * DAY > time.time():
            raise DemoError("Cohort outcome is not mature.")
        candidates = {}
        for side in ("token0", "token1"):
            cursor = ""
            for _ in range(30):
                query = f'''query DiscoverPeriod {{ pools(first: {POOL_PAGE}, block: {{number: {head}}},
                  orderBy: id, orderDirection: asc, where: {{{side}: "{WETH}", id_gt: "{cursor}",
                  createdAtTimestamp_gte: "{start}", createdAtTimestamp_lt: "{end}"}}) {{ {POOL_FIELDS} }} }}'''
                page = client.query(query, {})["pools"]
                if not isinstance(page, list):
                    raise DemoError("Discovery returned a non-list.")
                for pool in page:
                    validate_pool(pool)
                    if not start <= int(pool["createdAtTimestamp"]) < end or pool["id"] <= cursor:
                        raise DemoError("Invalid discovery pagination.")
                    cursor = pool["id"]
                    candidates[pool["id"]] = pool
                if len(page) < POOL_PAGE:
                    break
            else:
                raise DemoError("Discovery page cap reached; do not claim an exhaustive period.")
        save_json(out / f"candidates_{start_date}.json", list(candidates.values()))
        chosen = 0
        ranked = sorted(candidates.values(), key=rank)
        for pos in range(0, len(ranked), 10):
            group = ranked[pos:pos + 10]
            parts = []
            for i, pool in enumerate(group):
                token = pool["token1"]["id"] if pool["token0"]["id"] == WETH else pool["token0"]["id"]
                for side in (0, 1):
                    parts.append(f'''p{i}s{side}: pools(first: 2, block: {{number: {head}}},
                    orderBy: createdAtTimestamp, orderDirection: asc,
                    where: {{token{side}: "{WETH}", token{1-side}: "{token}"}}) {{id createdAtTimestamp}}''')
            data = client.query("query EarliestPools {\n" + "\n".join(parts) + "\n}", {})
            for i, pool in enumerate(group):
                earliest, reason = canonical_pool({"side0": data[f"p{i}s0"], "side1": data[f"p{i}s1"]})
                token = pool["token1"]["id"] if pool["token0"]["id"] == WETH else pool["token0"]["id"]
                reason = reason or ("not_earliest_weth_pool" if earliest != pool["id"] else None)
                reason = reason or ("target_token_already_selected" if token in used_tokens else None)
                if reason:
                    exclusions.append({"pool_address": pool["id"], "period": start_date, "reason": reason})
                    continue
                selected.append({**pool, "period": start_date})
                used_tokens.add(token)
                chosen += 1
                if chosen == 50:
                    break
            if chosen == 50:
                break
        funnel.append({"period": start_date, "candidates": len(candidates), "selected": chosen})
        print(f"Selected {chosen}/50 pools from {start_date}; {client.requests} network attempts.", flush=True)
        if chosen != 50:
            raise DemoError("Insufficient eligible pools; date ranges must be reviewed, not silently changed.")
    # Freeze the cohort before any early-activity or outcome query.
    save_json(out / "pools.json", selected)
    save_json(out / "exclusions.json", exclusions)
    save_json(out / "cohort_manifest.json", {"source_metadata": meta, "seed": SEED, "periods": funnel})
    # Historical tool reads source identity, not activity-derived selection.
    save_json(out / "manifest.json", {"source_metadata": meta})
    save_json(out / "schema.json", schema)
    hourly_by_pool, hourly_rows = {}, []
    for pos in range(0, len(selected), 5):
        group, parts = selected[pos:pos + 5], []
        for i, pool in enumerate(group):
            created = int(pool["createdAtTimestamp"])
            base = created // HOUR * HOUR
            parts.append(f'''p{i}: poolHourDatas(first: 26, block: {{number: {head}}}, orderBy: periodStartUnix,
              orderDirection: asc, where: {{pool: "{pool['id']}", periodStartUnix_gte: {base},
              periodStartUnix_lt: {base + DAY + HOUR}}}) {{ {HOUR_FIELDS} }}''')
        data = client.query("query EarlyHours {\n" + "\n".join(parts) + "\n}", {})
        for i, pool in enumerate(group):
            base = int(pool["createdAtTimestamp"]) // HOUR * HOUR
            hourly = validate_hours(data[f"p{i}"], base, base + DAY + HOUR)
            hourly_by_pool[pool["id"]] = hourly
            for row in window_rows(pool, hourly, 24):
                row.pop("window_hours")
                hourly_rows.append(row)
    write_csv(out / "pool_hours.csv", hourly_rows)
    summaries, page_counts = [], []
    for pos in range(0, len(selected), 5):
        group = selected[pos:pos + 5]
        collected = [[] for _ in group]
        seen = [set() for _ in group]
        cursors = ["" for _ in group]
        pending = list(range(len(group)))
        pages = [0 for _ in group]
        for _ in range(args.max_swap_pages):
            parts = []
            for i in pending:
                pool = group[i]
                created = int(pool["createdAtTimestamp"])
                parts.append(f'''p{i}: swaps(first: {SWAP_PAGE}, block: {{number: {head}}}, orderBy: id,
                  orderDirection: asc, where: {{pool: "{pool['id']}", timestamp_gte: "{created}",
                  timestamp_lt: "{created + DAY}", id_gt: {json.dumps(cursors[i])}}}) {{id timestamp amountUSD transaction {{id}}}}''')
            data = client.query("query EarlySwaps {\n" + "\n".join(parts) + "\n}", {})
            again = []
            for i in pending:
                page = data[f"p{i}"]
                cursors[i] = collect_page(page, cursors[i], group[i], seen[i])
                pages[i] += 1
                collected[i].extend(page)
                if len(page) == SWAP_PAGE:
                    again.append(i)
            pending = again
            if not pending:
                break
        for i, pool in enumerate(group):
            complete = i not in pending
            save_json(out / "swaps" / f"{pool['id']}.json", {"complete": complete, "events": collected[i]})
            summaries.append(activity(pool, collected[i], hourly_by_pool[pool["id"]], complete))
            page_counts.append({"pool_address": pool["id"], "pages": pages[i], "complete": complete})
        if (pos + len(group)) % 50 == 0:
            print(f"Counted swaps for {pos + len(group)}/200 pools; {client.requests} network attempts.", flush=True)
    write_csv(out / "activity_summary.csv", summaries)
    save_json(out / "activity_summary.json", summaries)
    remaining = min(200, args.max_requests - client.requests)
    if remaining < 1:
        raise DemoError("Budget exhausted before historical outcomes; activity evidence preserved.")
    historical = historical_run(argparse.Namespace(pilot=out, output=out / "historical_states",
                                                   max_requests=remaining, offline=args.offline))
    manifest = {
        "purpose": "200-pool activity diagnostic; not model training", "source_metadata": meta,
        "subgraph": client.subgraph, "retrieved_or_replayed_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED, "periods": funnel, "pools": len(selected), "exclusions": dict(Counter(r["reason"] for r in exclusions)),
        "network_attempts": client.requests + historical["network_attempts"],
        "cache_hits": client.hits + historical["cache_hits"], "max_requests": args.max_requests,
        "elapsed_seconds": round(time.monotonic() - began, 3),
        "unique_pool_hours": len(hourly_rows), "observed_pool_hours": sum(r["quality"] == "observed" for r in hourly_rows),
        "pools_with_complete_swap_history": sum(r["swap_history_complete"] for r in summaries),
        "pools_with_no_swaps_24h": sum(r["swap_count_24h"] == 0 for r in summaries),
        "pools_with_at_least_10_swaps_24h": sum(r["swap_count_24h"] is not None and r["swap_count_24h"] >= 10 for r in summaries),
        "absent_completed_buckets_with_swaps": sum(r["absent_completed_buckets_with_swaps"] for r in summaries),
        "historical": {k: v for k, v in historical.items() if k != "requests"},
        "swap_pagination": page_counts, "requests": client.records,
        "limitations": ["Equal-period deterministic sample, not proportional population sampling",
                        "USD volumes and TVL are source valuations pending pricing review",
                        "Candidate outcomes are not final labels; zero outcomes/timing policies remain open",
                        "Incomplete swap pages produce lower bounds, never exact counts",
                        "Hourly absence assumption is separately checked against indexed swaps"],
    }
    manifest["artifact_sha256"] = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                  for name in ("pools.json", "pool_hours.csv", "activity_summary.csv", "activity_summary.json")}
    save_json(out / "manifest.json", manifest)
    if manifest["network_attempts"]:
        save_json(out / "manifest.live.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/diagnostic_200"))
    parser.add_argument("--max-requests", type=int, default=600)
    parser.add_argument("--max-swap-pages", type=int, default=50)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_swap_pages <= 100:
        parser.error("--max-swap-pages must be 1–100")
    try:
        result = run(args)
    except DemoError as error:
        print(f"Diagnostic stopped: {error} Cached responses remain available.")
        raise SystemExit(1) from None
    except (ValueError, KeyError, TypeError, ArithmeticError):
        print("Diagnostic stopped: malformed external data; no success claimed.")
        raise SystemExit(1) from None
    print(json.dumps({k: v for k, v in result.items() if k not in {"requests", "swap_pagination"}}, indent=2))


if __name__ == "__main__":
    main()
