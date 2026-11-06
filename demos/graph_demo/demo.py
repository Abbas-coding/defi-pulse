"""Small standard-library-only GraphQL demo. Run from the repository root."""

import argparse
import csv
import hashlib
import json
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
DEFAULT_SUBGRAPH = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
TYPE_REF = "kind name ofType { kind name ofType { kind name } }"
PROBE = """query DemoSchema {
  _meta { deployment hasIndexingErrors block { number } }
  __schema { queryType { fields { name args { name } } } }
  poolType: __type(name: "Pool") { fields { name } }
  tokenType: __type(name: "Token") { fields { name } }
  hourType: __type(name: "PoolHourData") { fields { name } }
  poolFilter: __type(name: "Pool_filter") { inputFields { name type { TYPE_REF } } }
  hourFilter: __type(name: "PoolHourData_filter") { inputFields { name } }
}""".replace("TYPE_REF", TYPE_REF)
POOL_FIELDS = """id createdAtTimestamp feeTier totalValueLockedUSD
  token0 { id symbol decimals } token1 { id symbol decimals }"""
HOUR_FIELDS = """id periodStartUnix tvlUSD volumeUSD txCount
  open high low close token0Price token1Price liquidity"""


class DemoError(Exception):
    """Actionable failure that is safe to display without credential leakage."""


def save_json(path: Path, value: object) -> None:
    """Atomically replace an artifact so interrupted writes do not poison caches."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_settings(path: Path = Path(".env")) -> dict[str, str]:
    """Read only supported literal settings; never evaluate shell expressions."""
    settings = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() in {"GRAPH_API_KEY", "GRAPH_SUBGRAPH_ID"}:
                settings[key.strip()] = value.strip().strip("\"'")
    for key in ("GRAPH_API_KEY", "GRAPH_SUBGRAPH_ID"):
        if key in os.environ:
            settings[key] = os.environ[key]
    return settings


class Client:
    """Cache successful responses; count every network attempt, including retries."""

    def __init__(self, subgraph: str, key: str, cache: Path, max_requests: int,
                 offline: bool = False, refresh: bool = False) -> None:
        if not re.fullmatch(r"[A-Za-z0-9]+", subgraph):
            raise DemoError("Subgraph ID must be an alphanumeric ID, not a URL.")
        self.subgraph, self.key, self.cache = subgraph, key, cache
        self.max_requests, self.offline, self.refresh = max_requests, offline, refresh
        self.requests = 0
        self.hits = 0
        self.records: list[dict] = []

    def query(self, query: str, variables: dict) -> dict:
        body = {"query": query, "variables": variables}
        fingerprint = hashlib.sha256(json.dumps(
            {"subgraph": self.subgraph, **body}, sort_keys=True
        ).encode()).hexdigest()
        path = self.cache / f"{fingerprint}.json"
        if path.exists() and not self.refresh:
            payload = json.loads(path.read_text())
            self.hits += 1
        else:
            if self.offline:
                raise DemoError("Offline cache miss. Replay the same hour, pool count and source.")
            if not self.key:
                raise DemoError("Set GRAPH_API_KEY in local .env; see docs/graph_demo.md.")
            for attempt in range(3):
                if self.requests >= self.max_requests:
                    raise DemoError("Request budget exhausted; increase only after reviewing usage.")
                self.requests += 1
                request = Request(
                    f"https://gateway.thegraph.com/api/subgraphs/id/{self.subgraph}",
                    data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json",
                             "Accept": "application/json",
                             "User-Agent": "DeFiPulse-LearningDemo/0.1",
                             "Authorization": f"Bearer {self.key}"},
                    method="POST",
                )
                try:
                    with urlopen(request, timeout=30) as response:
                        payload = json.load(response)
                    break
                except HTTPError as error:
                    retryable = error.code == 429 or 500 <= error.code < 600
                    if not retryable or attempt == 2:
                        # Inspect only a bounded body for a known error code. Never echo it:
                        # upstream bodies may contain credentials or request details.
                        try:
                            detail = error.read(8192).decode("utf-8", errors="replace")
                        except OSError:
                            detail = ""
                        if error.code == 403 and re.search(r"error code:\s*1010\b", detail):
                            message = (
                                "HTTP 403 / Cloudflare 1010: client signature rejected. "
                                "This is not evidence of an invalid API key. "
                                "The demo sends an application User-Agent; if it persists, "
                                "contact the gateway provider."
                            )
                        elif error.code in {401, 403}:
                            message = (
                                f"Gateway HTTP {error.code}: access denied. Check the key's "
                                "status, allowed domains/subgraphs and account limits in Studio. "
                                "A 403 alone does not establish which check failed."
                            )
                        else:
                            message = f"Gateway HTTP {error.code}. Check source availability and quota."
                        raise DemoError(message) from None
                except (URLError, TimeoutError):
                    if attempt == 2:
                        raise DemoError("Network request failed after bounded retries.") from None
                except (ValueError, UnicodeError):
                    raise DemoError("Gateway returned invalid JSON.") from None
                time.sleep(2 ** attempt + random.random())
            self.validate(payload)
            # No headers, endpoint credentials or environment values are persisted.
            save_json(path, {"data": payload["data"]})
        self.validate(payload)
        self.records.append({"fingerprint": fingerprint, "cache_file": str(path),
                             "query": query, "variables": variables})
        return payload["data"]

    @staticmethod
    def validate(payload: object) -> None:
        if not isinstance(payload, dict) or payload.get("errors"):
            # External error text can echo request details. Keep it out of logs/cache.
            raise DemoError("GraphQL errors returned; partial data rejected. Check schema/access in Explorer.")
        if not isinstance(payload.get("data"), dict):
            raise DemoError("Response has no GraphQL data object.")


def verify_schema(probe: dict) -> str:
    """Check the selected live schema before constructing collection queries."""
    required = {
        "poolType": set(POOL_FIELDS.split()) - {"{", "}", "symbol", "decimals"},
        "tokenType": {"id", "symbol", "decimals"},
        "hourType": set(HOUR_FIELDS.split()),
    }
    for alias, names in required.items():
        fields = {f["name"] for f in (probe.get(alias) or {}).get("fields", [])}
        if not names <= fields:
            raise DemoError(f"Unsupported schema: {alias} missing {sorted(names - fields)}.")
    root = {f["name"]: {a["name"] for a in f["args"]}
            for f in probe["__schema"]["queryType"]["fields"]}
    for name in ("pools", "poolHourDatas"):
        if not {"where", "first", "orderBy", "orderDirection", "block"} <= root.get(name, set()):
            raise DemoError(f"Unsupported root arguments for {name}.")
    hour_filters = {f["name"] for f in probe["hourFilter"]["inputFields"]}
    if not {"pool", "periodStartUnix_gte", "periodStartUnix_lt"} <= hour_filters:
        raise DemoError("Unsupported hour filters.")
    filters = {f["name"]: f["type"] for f in probe["poolFilter"]["inputFields"]}
    if not {"token0", "token1", "createdAtTimestamp_lt"} <= filters.keys():
        raise DemoError("Unsupported pool filters.")
    type_ref = filters["token0"]
    while not type_ref.get("name"):
        type_ref = type_ref["ofType"]
    scalar = type_ref["name"]
    if scalar not in {"Bytes", "String", "ID"}:
        raise DemoError("Unsupported address filter scalar.")
    return scalar


def select_pools(data: dict, count: int) -> list[dict]:
    """Choose convenience examples, explicitly not a research sampling policy."""
    unique = {}
    for pool in data["weth0"] + data["weth1"]:
        if WETH not in {pool["token0"]["id"].lower(), pool["token1"]["id"].lower()}:
            raise DemoError("Source returned a pool without canonical WETH.")
        unique[pool["id"]] = pool
    return sorted(unique.values(), key=lambda p: (-Decimal(p["totalValueLockedUSD"]), p["id"]))[:count]


def flatten(pools: list[dict], histories: dict, start: int) -> list[dict]:
    """Preserve missing buckets explicitly and keep numeric decimal strings intact."""
    rows = []
    for i, pool in enumerate(pools):
        hours = histories[f"p{i}"]
        if len(hours) > 1 or any(int(h["periodStartUnix"]) != start for h in hours):
            raise DemoError("Unexpected or duplicate hourly bucket returned.")
        token = pool["token1"] if pool["token0"]["id"].lower() == WETH else pool["token0"]
        rows.append({"pool_address": pool["id"], "target_token_address": token["id"],
                     "symbol": token["symbol"], "fee_tier_raw": pool["feeTier"],
                     "hour_start_utc": datetime.fromtimestamp(start, timezone.utc).isoformat(),
                     "hour_end_utc": datetime.fromtimestamp(start + 3600, timezone.utc).isoformat(),
                     "quality": "observed" if hours else "missing",
                     **{f: hours[0][f] if hours else None for f in HOUR_FIELDS.split()}})
    return rows


def run(args: argparse.Namespace) -> dict:
    settings = read_settings()
    if args.hour:
        start_dt = datetime.fromisoformat(args.hour.replace("Z", "+00:00"))
        if start_dt.utcoffset() != timedelta(0) or start_dt.minute or start_dt.second or start_dt.microsecond:
            raise DemoError("--hour must be a UTC hour boundary, e.g. 2026-11-01T12:00:00Z.")
    else:
        start_dt = (datetime.now(timezone.utc) - timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    start = int(start_dt.timestamp())
    if start < 0 or start + 3600 > time.time():
        raise DemoError("Choose a completed historical UTC hour.")
    args.output.mkdir(parents=True, exist_ok=True)
    client = Client(settings.get("GRAPH_SUBGRAPH_ID") or DEFAULT_SUBGRAPH,
                    settings.get("GRAPH_API_KEY", ""), args.output / "cache",
                    args.max_requests, args.offline, args.refresh)
    began = time.monotonic()
    probe = client.query(PROBE, {})
    scalar = verify_schema(probe)
    meta = probe["_meta"]
    if meta["hasIndexingErrors"]:
        raise DemoError("Subgraph reports indexing errors; demo stopped.")
    block = int(meta["block"]["number"])
    discovery = """query DemoPools($weth: SCALAR!, $n: Int!, $start: BigInt!, $block: Int!) {
      weth0: pools(first: $n, block: {number: $block}, orderBy: totalValueLockedUSD,
        orderDirection: desc, where: {token0: $weth, createdAtTimestamp_lt: $start}) { FIELDS }
      weth1: pools(first: $n, block: {number: $block}, orderBy: totalValueLockedUSD,
        orderDirection: desc, where: {token1: $weth, createdAtTimestamp_lt: $start}) { FIELDS }
    }""".replace("SCALAR", scalar).replace("FIELDS", POOL_FIELDS)
    pools = select_pools(client.query(discovery, {
        "weth": WETH, "n": args.pools, "start": str(start), "block": block,
    }), args.pools)
    if not pools:
        raise DemoError("No candidate pools found; check source and chosen hour.")
    # Literal addresses come only from validated source IDs; scalar types vary by deployment.
    if any(not re.fullmatch(r"0x[0-9a-fA-F]{40}", p["id"]) for p in pools):
        raise DemoError("Malformed pool address returned by source.")
    selections = [
        f'p{i}: poolHourDatas(first: 2, block: {{number: $block}}, '
        'orderBy: periodStartUnix, orderDirection: asc, '
        f'where: {{pool: "{p["id"]}", periodStartUnix_gte: $start, '
        'periodStartUnix_lt: $end}) { ' + HOUR_FIELDS + ' }'
        for i, p in enumerate(pools)
    ]
    query = "query DemoHours($start: Int!, $end: Int!, $block: Int!) {\n" + "\n".join(selections) + "\n}"
    histories = client.query(query, {"start": start, "end": start + 3600, "block": block})
    rows = flatten(pools, histories, start)
    save_json(args.output / "schema.json", probe)
    save_json(args.output / "pools.json", pools)
    save_json(args.output / "hours.json", histories)
    with (args.output / "pool_hours.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "purpose": "educational demo; not the research cohort or model inputs",
        "retrieved_or_replayed_at_utc": datetime.now(timezone.utc).isoformat(),
        "subgraph": client.subgraph, "source_metadata": meta,
        "hour_start_utc": start_dt.isoformat(), "requested_pools": args.pools,
        "selected_pools": len(pools), "observed_buckets": sum(r["quality"] == "observed" for r in rows),
        "network_attempts": client.requests, "cache_hits": client.hits,
        "elapsed_seconds": round(time.monotonic() - began, 3),
        "requests": client.records,
        "cache_bytes": sum(p.stat().st_size for p in client.cache.glob("*.json")),
        "selection": "highest snapshot TVL among WETH-side candidates existing before chosen hour",
        "limitations": ["one clock-hour aggregate, not transaction history",
                        "missing buckets remain missing, not zero",
                        "pool ranking uses snapshot TVL, not historical-hour TVL",
                        "schema probe metadata is cached; use --refresh for a new snapshot"],
    }
    save_json(args.output / "manifest.json", manifest)
    for row in rows:
        print(f'{row["pool_address"]}  {row["quality"]:8}  TVL_USD={row["tvlUSD"]}  volume_USD={row["volumeUSD"]}')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pools", type=int, default=10, choices=range(1, 11), metavar="1..10")
    parser.add_argument("--hour", help="Completed UTC clock-hour start, ISO 8601 with Z or +00:00")
    parser.add_argument("--output", type=Path, default=Path("data/demo"))
    parser.add_argument("--max-requests", type=int, default=10)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true", help="Use cached responses only; no API key required")
    mode.add_argument("--refresh", action="store_true", help="Replace cached source snapshot using live requests")
    args = parser.parse_args()
    try:
        if args.max_requests < 1:
            raise DemoError("--max-requests must be positive.")
        manifest = run(args)
        print(f'Saved to {args.output}: {manifest["selected_pools"]} pools, '
              f'{manifest["observed_buckets"]} observed buckets, '
              f'{manifest["network_attempts"]} network attempts, {manifest["cache_hits"]} cache hits.')
        return 0
    except (DemoError, ValueError, KeyError, TypeError, OSError):
        # Only our controlled errors are safe to display; avoid leaking external payloads.
        import sys
        error = sys.exc_info()[1]
        print(f"Demo stopped: {error}" if isinstance(error, DemoError)
              else "Demo stopped: malformed data/configuration or local file error.")
        return 1
