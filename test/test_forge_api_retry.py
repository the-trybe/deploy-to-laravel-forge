"""
Retry behaviour of ForgeApi against a local fake Forge server.

Run from the repository root:

    PYTHONPATH=src python -m unittest discover -s test -v
"""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from urllib3.exceptions import MaxRetryError, NewConnectionError, SSLError

import forge_api
from forge_api import ForgeApi


class FakeForge(BaseHTTPRequestHandler):
    # Each test sets the statuses to answer with, in order; the last one repeats.
    statuses: list[int] = []
    headers_by_status: dict[int, dict[str, str]] = {}
    hits: list[str] = []

    def _answer(self):
        FakeForge.hits.append(self.command)
        index = min(len(FakeForge.hits) - 1, len(FakeForge.statuses) - 1)
        status = FakeForge.statuses[index]
        body = json.dumps({"data": {"id": 1, "attributes": {"status": "finished"}}}).encode()

        self.send_response(status)
        for name, value in FakeForge.headers_by_status.get(status, {}).items():
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _answer
    do_POST = _answer
    do_PUT = _answer

    def log_message(self, *args):
        pass


class ForgeApiRetryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeForge)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        # No waiting between attempts, so the suite stays fast; the retry
        # rules themselves are the real ones.
        cls.real_strategy = forge_api.RETRY_STRATEGY
        forge_api.RETRY_STRATEGY = cls.real_strategy.new(backoff_factor=0)

    @classmethod
    def tearDownClass(cls):
        forge_api.RETRY_STRATEGY = cls.real_strategy
        cls.server.shutdown()

    def setUp(self):
        FakeForge.hits = []
        FakeForge.headers_by_status = {}
        self.api = ForgeApi("token", "org")
        # Ignore HTTP(S)_PROXY on a CI runner: the fake server is local.
        self.api.session.trust_env = False
        self.api.forge_uri = f"http://127.0.0.1:{self.server.server_address[1]}"

    def test_a_502_while_polling_a_deployment_is_retried(self):
        FakeForge.statuses = [502, 502, 200]

        deployment = self.api.get_deployment(1, 2, 3)

        self.assertEqual("finished", deployment["attributes"]["status"])
        self.assertEqual(3, len(FakeForge.hits))

    def test_503_504_and_429_are_retried_too(self):
        FakeForge.statuses = [503, 504, 429, 200]
        FakeForge.headers_by_status = {429: {"Retry-After": "0"}}

        self.api.get_deployment(1, 2, 3)

        self.assertEqual(4, len(FakeForge.hits))

    def test_it_gives_up_after_five_retries_and_reports_the_real_status(self):
        FakeForge.statuses = [502]

        with self.assertRaises(Exception) as raised:
            self.api.get_deployment(1, 2, 3)

        self.assertIn("Failed to get deployment status", str(raised.exception))
        self.assertIn("502", str(raised.exception.__cause__))
        self.assertEqual(6, len(FakeForge.hits))  # 1 attempt + 5 retries

    def test_a_post_is_never_retried_so_nothing_is_deployed_twice(self):
        FakeForge.statuses = [502, 200]

        with self.assertRaises(Exception):
            self.api.deploy_site(1, 2)

        self.assertEqual(["POST"], FakeForge.hits)

    def test_a_put_is_retried_because_it_is_idempotent(self):
        FakeForge.statuses = [502, 200]

        self.api.update_site_environment(1, 2, "APP_ENV=testing")

        self.assertEqual(["PUT", "PUT"], FakeForge.hits)

    def test_a_404_is_not_retried(self):
        FakeForge.statuses = [404]

        self.assertIsNone(self.api.get_deployment_log(1, 2, 3))
        self.assertEqual(1, len(FakeForge.hits))

    def test_a_500_is_not_retried(self):
        # A 500 is usually a real error; retrying would only delay the report.
        FakeForge.statuses = [500, 200]

        with self.assertRaises(Exception):
            self.api.get_deployment(1, 2, 3)

        self.assertEqual(1, len(FakeForge.hits))


class RetryRulesTest(unittest.TestCase):
    """Errors a fake server cannot easily produce, checked on the rules directly."""

    def test_a_tls_error_on_a_post_is_not_retried(self):
        # Forge may already have queued the deployment when the TLS error hits.
        with self.assertRaises(MaxRetryError):
            forge_api.RETRY_STRATEGY.increment(method="POST", url="/deployments", error=SSLError("bad record mac"))

    def test_a_long_retry_after_is_capped(self):
        # A maintenance page answering "Retry-After: 3600" must not stall a deploy for hours.
        strategy = forge_api.RETRY_STRATEGY

        self.assertEqual(forge_api.MAX_RETRY_AFTER_SECONDS, strategy.get_retry_after(_Headers({"Retry-After": "3600"})))
        self.assertEqual(3, strategy.get_retry_after(_Headers({"Retry-After": "3"})))
        self.assertIsNone(strategy.get_retry_after(_Headers({})))

    def test_a_connect_error_on_a_post_is_retried_because_nothing_was_sent(self):
        retried = forge_api.RETRY_STRATEGY.increment(
            method="POST", url="/deployments", error=NewConnectionError(None, "refused")
        )

        self.assertEqual(4, retried.total)


class _Headers:
    """The slice of an HTTP response that Retry.get_retry_after reads."""

    def __init__(self, headers):
        self.headers = headers


if __name__ == "__main__":
    unittest.main()
