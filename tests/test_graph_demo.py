"""Semantic checks for the learning demo; all source responses here are synthetic."""

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from demos.graph_demo.demo import (
    Client, DemoError, WETH, HOUR_FIELDS, POOL_FIELDS, flatten, run, select_pools, verify_schema,
)


def pool(address: str, weth_first: bool = True) -> dict:
    weth = {"id": WETH, "symbol": "WETH", "decimals": "18"}
    target = {"id": "0x" + "a" * 40, "symbol": "TEST", "decimals": "18"}
    return {"id": address, "token0": weth if weth_first else target,
            "token1": target if weth_first else weth, "feeTier": "3000",
            "totalValueLockedUSD": "123.45"}


class ClientTests(unittest.TestCase):
    def test_cache_replay_needs_neither_network_nor_key(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client("example", "secret", Path(directory), 3)
            response = unittest.mock.MagicMock()
            response.__enter__.return_value.read.return_value = b'{"data": {"answer": 42}}'
            with patch("demos.graph_demo.demo.urlopen", return_value=response) as network:
                self.assertEqual(client.query("{ answer }", {}), {"answer": 42})
                self.assertEqual(client.query("{ answer }", {}), {"answer": 42})
                self.assertEqual(network.call_count, 1)
                headers = dict(network.call_args.args[0].header_items())
                self.assertEqual(headers["User-agent"], "DeFiPulse-LearningDemo/0.1")
                self.assertEqual(headers["Accept"], "application/json")
            replay = Client("example", "", Path(directory), 1, offline=True)
            self.assertEqual(replay.query("{ answer }", {}), {"answer": 42})
            self.assertEqual(replay.requests, 0)
            raw = next(Path(directory).glob("*.json")).read_text()
            self.assertNotIn("secret", raw)
            self.assertEqual(json.loads(raw)["data"]["answer"], 42)

    def test_partial_graphql_error_is_rejected(self):
        with self.assertRaises(DemoError):
            Client.validate({"data": {"pools": []}, "errors": [{"message": "failure"}]})

    def test_budget_applies_to_retries(self):
        from urllib.error import URLError
        with tempfile.TemporaryDirectory() as directory:
            client = Client("example", "secret", Path(directory), 1)
            with patch("demos.graph_demo.demo.urlopen", side_effect=URLError("secret")) as network:
                with patch("demos.graph_demo.demo.time.sleep"):
                    with self.assertRaisesRegex(DemoError, "budget"):
                        client.query("{ example }", {})
                self.assertEqual(network.call_count, 1)
                self.assertFalse(list(Path(directory).glob("*.json")))

    def test_cloudflare_block_is_classified_without_echoing_secrets(self):
        from io import BytesIO
        from urllib.error import HTTPError
        with tempfile.TemporaryDirectory() as directory:
            client = Client("example", "private-token", Path(directory), 3)
            failure = HTTPError("https://example.invalid", 403, "Forbidden", {},
                                BytesIO(b"error code: 1010\nprivate-token"))
            with patch("demos.graph_demo.demo.urlopen", side_effect=failure) as network:
                with self.assertRaisesRegex(DemoError, "Cloudflare 1010") as result:
                    client.query("{ example }", {})
                self.assertNotIn("private-token", str(result.exception))
                self.assertEqual(network.call_count, 1)
                self.assertFalse(list(Path(directory).glob("*.json")))

    def test_offline_miss_never_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            client = Client("example", "", Path(directory), 1, offline=True)
            with patch("demos.graph_demo.demo.urlopen") as network:
                with self.assertRaisesRegex(DemoError, "cache miss"):
                    client.query("{ example }", {})
                network.assert_not_called()


class DataTests(unittest.TestCase):
    def test_both_weth_orientations_and_deduplication(self):
        p0, p1 = pool("0x" + "1" * 40), pool("0x" + "2" * 40, False)
        self.assertEqual(len(select_pools({"weth0": [p0], "weth1": [p0, p1]}, 10)), 2)
        rows = flatten([p0, p1], {"p0": [], "p1": []}, 0)
        self.assertEqual(rows[0]["target_token_address"], rows[1]["target_token_address"])
        self.assertEqual(rows[0]["quality"], "missing")
        self.assertIsNone(rows[0]["tvlUSD"])

    def test_wrong_or_duplicate_bucket_is_rejected(self):
        p = pool("0x" + "1" * 40)
        with self.assertRaises(DemoError):
            flatten([p], {"p0": [{"periodStartUnix": 3600}]}, 0)
        with self.assertRaises(DemoError):
            flatten([p], {"p0": [{"periodStartUnix": 0}] * 2}, 0)


class ExportTests(unittest.TestCase):
    def test_full_demo_exports_raw_csv_manifest_with_missing_pool(self):
        fields = lambda names: [{"name": name} for name in names]
        probe = {
            "_meta": {"deployment": "synthetic-deployment", "hasIndexingErrors": False,
                      "block": {"number": 123}},
            "__schema": {"queryType": {"fields": [
                {"name": name, "args": fields(["where", "first", "orderBy", "orderDirection", "block"])}
                for name in ["pools", "poolHourDatas"]]}},
            "poolType": {"fields": fields(set(POOL_FIELDS.split()) - {"{", "}"})},
            "tokenType": {"fields": fields(["id", "symbol", "decimals"])},
            "hourType": {"fields": fields(HOUR_FIELDS.split())},
            "poolFilter": {"inputFields": [
                {"name": n, "type": {"name": "Bytes"}}
                for n in ["token0", "token1", "createdAtTimestamp_lt"]]},
            "hourFilter": {"inputFields": fields(["pool", "periodStartUnix_gte", "periodStartUnix_lt"])},
        }
        self.assertEqual(verify_schema(probe), "Bytes")
        start = 1761998400  # 2025-11-01 12:00 UTC
        hourly = {f: "1.25" for f in HOUR_FIELDS.split()}
        hourly["periodStartUnix"] = start
        pools = [pool("0x" + "1" * 40), pool("0x" + "2" * 40, False)]
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(hour="2025-11-01T12:00:00Z", output=Path(directory),
                                      max_requests=10, offline=True, refresh=False, pools=2)
            with patch("demos.graph_demo.demo.Client.query", side_effect=[
                probe, {"weth0": pools[:1], "weth1": pools[1:]}, {"p0": [hourly], "p1": []}
            ]), patch("builtins.print"):
                manifest = run(args)
            self.assertEqual(manifest["observed_buckets"], 1)
            self.assertEqual(manifest["selected_pools"], 2)
            import csv
            with (Path(directory) / "pool_hours.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["tvlUSD"], "1.25")
            self.assertEqual(rows[1]["quality"], "missing")
            self.assertEqual(rows[1]["tvlUSD"], "")
            for filename in ["schema.json", "pools.json", "hours.json", "manifest.json"]:
                self.assertTrue((Path(directory) / filename).exists())
        probe["hourType"]["fields"] = []
        with self.assertRaisesRegex(DemoError, "Unsupported schema"):
            verify_schema(probe)


if __name__ == "__main__":
    unittest.main()
