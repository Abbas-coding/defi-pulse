"""Compare separate elapsed days for the frozen diagnostic cohort; no model changes."""

import argparse
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

from demos.graph_demo.demo import Client, DemoError, read_settings, save_json
from .diagnostic import SWAP_PAGE, collect_page, validate_pool
from .pilot import DAY, HOUR, utc, write_csv


def day_summary(pool: dict, day: int, events: list[dict], complete: bool) -> dict:
    """Summarize one separate elapsed day; incomplete data never becomes exact zero."""
    start = int(pool["createdAtTimestamp"]) + (day - 1) * DAY
    with localcontext() as context:
        context.prec = 100
        volume = str(sum((Decimal(e["amountUSD"]) for e in events), Decimal(0)))
    return {
        "pool_address": pool["id"], "period": pool["period"], "day": day,
        "start_utc": utc(start), "end_exclusive_utc": utc(start + DAY),
        "history_complete": complete, "swap_count": len(events) if complete else None,
        "swap_count_lower_bound": len(events),
        "swap_transaction_count": len({e["transaction"]["id"] for e in events}) if complete else None,
        "volume_usd": volume if complete else None,
        "active_hours": len({(int(e["timestamp"]) - start) // HOUR for e in events}) if complete else None,
        "pricing_quality": "unverified_source_usd_valuation",
    }


def pool_comparison(rows: list[dict]) -> dict:
    """Contrast daily increments; cumulative increases alone cannot imply acceleration."""
    rows = sorted(rows, key=lambda r: r["day"])
    if len(rows) != 3 or [r["day"] for r in rows] != [1, 2, 3] or len({r["pool_address"] for r in rows}) != 1:
        raise DemoError("Expected exactly three distinct days for one pool.")
    result = {"pool_address": rows[0]["pool_address"], "period": rows[0]["period"],
              "complete_72h": all(r["history_complete"] for r in rows)}
    for r in rows:
        for field in ("swap_count", "swap_transaction_count", "volume_usd", "active_hours"):
            result[f"day{r['day']}_{field}"] = r[field]
    complete = result["complete_72h"]
    first = next((r["day"] for r in rows if r["swap_count"] is not None and r["swap_count"] > 0), None)
    result["first_trading_day"] = (first or "none") if complete else "unknown_incomplete"
    for a, b in ((1, 2), (2, 3), (1, 3)):
        left, right = rows[a - 1], rows[b - 1]
        known = left["history_complete"] and right["history_complete"]
        result[f"swaps_increased_day{b}_vs_day{a}"] = right["swap_count"] > left["swap_count"] if known else None
        result[f"volume_increased_day{b}_vs_day{a}"] = Decimal(right["volume_usd"]) > Decimal(left["volume_usd"]) if known else None
    for last in (1, 2, 3):
        known = all(r["history_complete"] for r in rows[:last])
        result[f"cumulative_swap_count_{last * 24}h"] = sum(r["swap_count"] for r in rows[:last]) if known else None
    return result


def aggregate(daily: list[dict], comparisons: list[dict]) -> dict:
    result = {"days": {}, "first_trading_day_counts": dict(Counter(str(r["first_trading_day"]) for r in comparisons))}
    for day in (1, 2, 3):
        rows = [r for r in daily if r["day"] == day and r["history_complete"]]
        with localcontext() as context:
            context.prec = 100
            volume = str(sum((Decimal(r["volume_usd"]) for r in rows), Decimal(0)))
        result["days"][str(day)] = {
            "complete_pools": len(rows), "total_swaps": sum(r["swap_count"] for r in rows),
            "total_volume_usd": volume, "median_swaps": statistics.median(r["swap_count"] for r in rows) if rows else None,
            "zero_swap_pools": sum(r["swap_count"] == 0 for r in rows),
            "pools_1_to_9_swaps": sum(1 <= r["swap_count"] < 10 for r in rows),
            "pools_at_least_10_swaps": sum(r["swap_count"] >= 10 for r in rows),
            "total_active_pool_hours": sum(r["active_hours"] for r in rows),
        }
    for a, b in ((1, 2), (2, 3), (1, 3)):
        for measurement in ("swaps", "volume"):
            field = f"{measurement}_increased_day{b}_vs_day{a}"
            result[field] = sum(r[field] is True for r in comparisons)
    result["day1_under10_later_reaches10_in_a_single_day"] = sum(
        r["complete_72h"] and r["day1_swap_count"] < 10
        and max(r["day2_swap_count"], r["day3_swap_count"]) >= 10 for r in comparisons)
    result["pools_at_least10_cumulative_72h"] = sum(
        r["complete_72h"] and r["cumulative_swap_count_72h"] >= 10 for r in comparisons)
    return result


def run(args: argparse.Namespace) -> dict:
    if not 1 <= args.max_requests <= 500 or not 1 <= args.max_swap_pages <= 100:
        raise DemoError("Use 1–500 request attempts and 1–100 pages per pool/day.")
    source = args.source
    original = json.loads((source / "manifest.live.json").read_text())
    pool_bytes = (source / "pools.json").read_bytes()
    if hashlib.sha256(pool_bytes).hexdigest() != original["artifact_sha256"]["pools.json"]:
        raise DemoError("Frozen cohort hash mismatch.")
    pools = json.loads(pool_bytes)
    if len(pools) != 200 or len({p["id"] for p in pools}) != 200:
        raise DemoError("Expected the same 200 unique pools.")
    for pool in pools:
        validate_pool(pool)
    head = int(original["source_metadata"]["block"]["number"])
    settings = read_settings()
    # Preserve the original subgraph and snapshot, rather than selecting a newer deployment.
    client = Client(original["subgraph"], settings.get("GRAPH_API_KEY", ""),
                    args.output / "cache", args.max_requests, args.offline)
    meta = client.query(f'''query ThreeDaySource {{ _meta(block: {{number: {head}}}) {{
        deployment hasIndexingErrors block {{number}} }} }}''', {})["_meta"]
    if (meta["deployment"] != original["source_metadata"]["deployment"] or meta["hasIndexingErrors"]
            or int(meta["block"]["number"]) != head):
        raise DemoError("Source deployment, snapshot, or indexing status mismatch.")
    daily, pagination, day1_hashes = [], [], {}
    for pool in pools:
        path = source / "swaps" / f"{pool['id']}.json"
        day1_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        saved = json.loads(path.read_text())
        events, cursor, seen = saved["events"], "", set()
        for start in range(0, len(events), SWAP_PAGE):
            cursor = collect_page(events[start:start + SWAP_PAGE], cursor, pool, seen)
        daily.append(day_summary(pool, 1, events, saved["complete"]))
    # Two independent ranges preserve day-specific completeness and daily changes.
    for day in (2, 3):
        for pos in range(0, len(pools), 5):
            group = pools[pos:pos + 5]
            collected, seen, cursors = [[] for _ in group], [set() for _ in group], ["" for _ in group]
            pages, pending = [0 for _ in group], list(range(len(group)))
            for _ in range(args.max_swap_pages):
                parts = []
                for i in pending:
                    pool = group[i]
                    start = int(pool["createdAtTimestamp"]) + (day - 1) * DAY
                    parts.append(f'''p{i}: swaps(first: {SWAP_PAGE}, block: {{number: {head}}}, orderBy: id,
                      orderDirection: asc, where: {{pool: "{pool['id']}", timestamp_gte: "{start}",
                      timestamp_lt: "{start + DAY}", id_gt: {json.dumps(cursors[i])}}}) {{
                      id timestamp amountUSD transaction {{id}} }}''')
                data = client.query("query LaterDaySwaps {\n" + "\n".join(parts) + "\n}", {})
                again = []
                for i in pending:
                    page = data[f"p{i}"]
                    cursors[i] = collect_page(page, cursors[i], group[i], seen[i], (day - 1) * DAY, day * DAY)
                    pages[i] += 1
                    collected[i].extend(page)
                    if len(page) == SWAP_PAGE:
                        again.append(i)
                pending = again
                if not pending:
                    break
            for i, pool in enumerate(group):
                complete = i not in pending
                save_json(args.output / "swaps" / f"day{day}" / f"{pool['id']}.json",
                          {"complete": complete, "events": collected[i]})
                daily.append(day_summary(pool, day, collected[i], complete))
                pagination.append({"pool_address": pool["id"], "day": day, "pages": pages[i], "complete": complete})
            if (pos + len(group)) % 50 == 0:
                print(f"Day {day}: {pos + len(group)}/200 pools; {client.requests} network attempts.", flush=True)
    comparisons = [pool_comparison([r for r in daily if r["pool_address"] == pool["id"]]) for pool in pools]
    summary = aggregate(daily, comparisons)
    args.output.mkdir(parents=True, exist_ok=True)
    save_json(args.output / "daily_activity.json", daily)
    save_json(args.output / "pool_comparison.json", comparisons)
    save_json(args.output / "summary.json", summary)
    write_csv(args.output / "daily_activity.csv", daily)
    write_csv(args.output / "pool_comparison.csv", comparisons)
    manifest = {
        "purpose": "Separate day-1/day-2/day-3 diagnostic; no prediction-window or target change",
        "retrieved_or_replayed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_metadata": meta, "subgraph": client.subgraph,
        "cohort_sha256": hashlib.sha256(pool_bytes).hexdigest(), "day1_artifact_sha256": day1_hashes,
        "network_attempts": client.requests, "cache_hits": client.hits, "max_requests": args.max_requests,
        "max_swap_pages": args.max_swap_pages, "pools": len(pools), "pool_day_rows": len(daily),
        "summary": summary, "pagination": pagination, "requests": client.records,
        "limitations": ["USD volumes remain unverified indexer valuations",
                        "Complete means all matching indexed pages were retrieved, not independent chain verification",
                        "Incomplete days have lower bounds, not exact counts or volumes",
                        "Day-2/day-3 inputs overlap the current future outcome period; excluded from existing models"],
    }
    manifest["artifact_sha256"] = {name: hashlib.sha256((args.output / name).read_bytes()).hexdigest()
                                  for name in ("daily_activity.json", "daily_activity.csv", "pool_comparison.json",
                                               "pool_comparison.csv", "summary.json")}
    save_json(args.output / "manifest.json", manifest)
    if client.requests:
        save_json(args.output / "manifest.live.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/diagnostic_200"))
    parser.add_argument("--output", type=Path, default=Path("data/diagnostic_200/three_day_activity"))
    parser.add_argument("--max-requests", type=int, default=200)
    parser.add_argument("--max-swap-pages", type=int, default=50)
    parser.add_argument("--offline", action="store_true")
    try:
        result = run(parser.parse_args())
    except DemoError as error:
        print(f"Comparison stopped: {error} Successful responses remain cached.")
        raise SystemExit(1) from None
    except (ValueError, KeyError, TypeError, ArithmeticError):
        print("Comparison stopped: malformed external data; no success claimed.")
        raise SystemExit(1) from None
    print(json.dumps({k: result[k] for k in ("network_attempts", "cache_hits", "pool_day_rows", "summary")}, indent=2))


if __name__ == "__main__":
    main()
