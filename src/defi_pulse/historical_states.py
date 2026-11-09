"""Retrieve historical indexed pool states for the existing pilot cohort."""

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from demos.graph_demo.demo import Client, DEFAULT_SUBGRAPH, DemoError, read_settings, save_json
from .pilot import DAY, utc, write_csv


def anchor(before: object, after: object, cutoff: int, head: int) -> dict:
    """Locate an indexed transaction at/before cutoff and require later source coverage."""
    if not isinstance(before, list) or not isinstance(after, list) or len(before) != 1 or len(after) != 1:
        raise DemoError("Expected one transaction on each side of the cutoff.")
    left, right = before[0], after[0]
    block, stamp = int(left["blockNumber"]), int(left["timestamp"])
    next_block, next_stamp = int(right["blockNumber"]), int(right["timestamp"])
    if not 0 < block < next_block <= head or not stamp <= cutoff < next_stamp:
        raise DemoError("Transaction anchors do not bracket the cutoff.")
    return {
        "block_number": block, "block_timestamp_utc": utc(stamp),
        "cutoff_gap_seconds": cutoff - stamp,
        "next_indexed_block_number": next_block, "next_indexed_timestamp_utc": utc(next_stamp),
        "timing_quality": "exact_cutoff_timestamp" if stamp == cutoff else "earlier_indexed_transaction_block",
    }


def assess_pair(left: dict, right: dict) -> tuple[int | None, str]:
    """Produce a timing-qualified candidate only; pricing is a separate quality gate."""
    if left.get("tvl_usd") is None or right.get("tvl_usd") is None:
        return None, "missing_pool_state"
    a, b = Decimal(left["tvl_usd"]), Decimal(right["tvl_usd"])
    if not a.is_finite() or not b.is_finite() or a <= 0 or b < 0:
        return None, "invalid_or_zero_hour24_tvl"
    if b == 0:
        return None, "zero_day8_policy_pending"
    if any(r["timing_quality"] != "exact_cutoff_timestamp" for r in (left, right)):
        return None, "earlier_indexed_block_requires_timing_policy"
    return int(b <= Decimal("0.20") * a), "candidate_only_usd_pricing_unverified"


def run(args: argparse.Namespace) -> dict:
    pilot = args.pilot
    manifest_path = pilot / "manifest.live.json"
    if not manifest_path.exists():
        manifest_path = pilot / "manifest.json"
    original = json.loads(manifest_path.read_text())
    pools = json.loads((pilot / "pools.json").read_text())
    if not 1 <= len(pools) <= 200 or not 1 <= args.max_requests <= 200:
        raise DemoError("Bound this check to at most 200 pools and 200 attempts.")
    head = int(original["source_metadata"]["block"]["number"])
    deployment = original["source_metadata"]["deployment"]
    settings = read_settings()
    client = Client(settings.get("GRAPH_SUBGRAPH_ID") or DEFAULT_SUBGRAPH,
                    settings.get("GRAPH_API_KEY", ""), args.output / "cache",
                    args.max_requests, args.offline)
    targets = [{"pool_address": pool["id"], "endpoint": name,
                "cutoff": int(pool["createdAtTimestamp"]) + elapsed}
               for pool in pools for name, elapsed in (("hour24", DAY), ("day8", 8 * DAY))]
    for start in range(0, len(targets), 5):
        group = targets[start:start + 5]
        parts = [f'_meta(block: {{number: {head}}}) {{deployment hasIndexingErrors block {{number}}}}']
        for i, target in enumerate(group):
            for side, operator, direction in (("before", "lte", "desc"), ("after", "gt", "asc")):
                parts.append(f'''{side}{i}: transactions(first: 1, block: {{number: {head}}},
                  orderBy: timestamp, orderDirection: {direction},
                  where: {{timestamp_{operator}: "{target['cutoff']}"}}) {{id timestamp blockNumber}}''')
        data = client.query("query CutoffAnchors {\n" + "\n".join(parts) + "\n}", {})
        if data["_meta"]["deployment"] != deployment or data["_meta"]["hasIndexingErrors"]:
            raise DemoError("Source changed or reported indexing errors.")
        for i, target in enumerate(group):
            target.update(anchor(data[f"before{i}"], data[f"after{i}"], target["cutoff"], head))
    rows = []
    for start in range(0, len(targets), 5):
        group = targets[start:start + 5]
        parts = []
        for i, target in enumerate(group):
            block = target["block_number"]
            # Addresses originate from the locally preserved, validated pilot cohort.
            if not re.fullmatch(r"0x[0-9a-fA-F]{40}", target["pool_address"]):
                raise DemoError("Malformed preserved pool address.")
            parts.extend([
                f'm{i}: _meta(block: {{number: {block}}}) {{deployment hasIndexingErrors block {{number}}}}',
                f'''p{i}: pool(id: "{target['pool_address']}", block: {{number: {block}}}) {{
                  id totalValueLockedUSD totalValueLockedToken0 totalValueLockedToken1 liquidity txCount }}''',
            ])
        data = client.query("query HistoricalPoolStates {\n" + "\n".join(parts) + "\n}", {})
        for i, target in enumerate(group):
            meta, state = data[f"m{i}"], data[f"p{i}"]
            if (meta["deployment"] != deployment or meta["hasIndexingErrors"]
                    or int(meta["block"]["number"]) != target["block_number"]):
                raise DemoError("Historical snapshot identity mismatch.")
            if state is not None and state["id"] != target["pool_address"]:
                raise DemoError("Historical pool identity mismatch.")
            rows.append({
                "pool_address": target["pool_address"], "endpoint": target["endpoint"],
                "requested_as_of_utc": utc(target["cutoff"]),
                **{k: v for k, v in target.items() if k not in {"pool_address", "endpoint", "cutoff"}},
                "tvl_usd": state["totalValueLockedUSD"] if state else None,
                "token0_balance": state["totalValueLockedToken0"] if state else None,
                "token1_balance": state["totalValueLockedToken1"] if state else None,
                "in_range_liquidity": state["liquidity"] if state else None,
                "quality": "historical_indexed_state" if state else "missing_pool_state",
                "pricing_quality": "unverified_indexed_usd_valuation",
            })
    pairs = []
    for left, right in zip(rows[::2], rows[1::2]):
        label, status = assess_pair(left, right)
        pairs.append({"pool_address": left["pool_address"], "hour24_tvl_usd": left["tvl_usd"],
                      "day8_tvl_usd": right["tvl_usd"], "candidate_label": label,
                      "final_label": None, "status": status})
    args.output.mkdir(parents=True, exist_ok=True)
    save_json(args.output / "states.json", rows)
    save_json(args.output / "label_candidates.json", pairs)
    write_csv(args.output / "states.csv", rows)
    write_csv(args.output / "label_candidates.csv", pairs)
    manifest = {
        "purpose": "Historical-state feasibility; final labels await pricing and policy review",
        "deployment": deployment, "source_snapshot_block": head,
        "cohort_sha256": hashlib.sha256((pilot / "pools.json").read_bytes()).hexdigest(),
        "network_attempts": client.requests, "cache_hits": client.hits,
        "max_requests": args.max_requests, "pools": len(pools),
        "retrieved_or_replayed_at_utc": datetime.now(timezone.utc).isoformat(),
        "states_returned": sum(r["tvl_usd"] is not None for r in rows),
        "timing_counts": dict(Counter(r["timing_quality"] for r in rows)),
        "candidate_status_counts": dict(Counter(r["status"] for r in pairs)),
        "candidate_label_counts": dict(Counter(str(r["candidate_label"]) for r in pairs)),
        "final_labels": 0, "requests": client.records,
        "limitations": ["Historical USD TVL is the indexer's stored valuation, potentially stale or unreliable",
                        "A latest indexed transaction is not necessarily the immediately preceding chain block",
                        "Only exact-cutoff timestamps receive candidate labels; no staleness tolerance adopted",
                        "Verified zero day-8 outcome treatment remains pending"],
    }
    manifest["artifact_sha256"] = {name: hashlib.sha256((args.output / name).read_bytes()).hexdigest()
                                  for name in ("states.json", "states.csv", "label_candidates.json", "label_candidates.csv")}
    save_json(args.output / "manifest.json", manifest)
    if client.requests:
        save_json(args.output / "manifest.live.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, default=Path("data/pilot"))
    parser.add_argument("--output", type=Path, default=Path("data/pilot/historical_states"))
    parser.add_argument("--max-requests", type=int, default=20)
    parser.add_argument("--offline", action="store_true")
    try:
        result = run(parser.parse_args())
    except (DemoError, ValueError, KeyError, TypeError, InvalidOperation):
        print("Historical check stopped: invalid source data, unsupported query, or request budget. No success claimed.")
        raise SystemExit(1) from None
    print(json.dumps({k: v for k, v in result.items() if k != "requests"}, indent=2))


if __name__ == "__main__":
    main()
