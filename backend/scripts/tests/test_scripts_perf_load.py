import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import perf_load
from covers import covers


class Quick(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        body = json.dumps({"path": self.path}).encode()
        status = 500 if self.path.endswith("/panel") and "FAIL" in str(self.headers) else 200
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def summary(p95: float, errors: int = 0, count: int = 10) -> perf_load.Summary:
    return perf_load.Summary("/api/v1/me", count, errors, p95 / 2, p95, p95)


@covers("SYS-NFR-02")
class LoadToolTests(unittest.TestCase):
    def test_percentiles_use_the_nearest_rank(self) -> None:
        values = [float(n) for n in range(1, 101)]
        self.assertEqual(perf_load.percentile(values, 50), 50)
        self.assertEqual(perf_load.percentile(values, 95), 95)
        self.assertEqual(perf_load.percentile(values, 100), 100)
        self.assertEqual(perf_load.percentile([7.0], 95), 7)
        self.assertEqual(perf_load.percentile([], 95), 0)

    def test_a_run_within_the_limit_is_a_pass(self) -> None:
        self.assertEqual(perf_load.verdict([summary(120)], 300), [])

    def test_a_p95_over_the_limit_is_reported(self) -> None:
        problems = perf_load.verdict([summary(301)], 300)
        self.assertEqual(len(problems), 1)
        self.assertIn("p95", problems[0])

    def test_any_failed_request_fails_the_run(self) -> None:
        problems = perf_load.verdict([summary(50, errors=2)], 300)
        self.assertIn("2 of 10 requests failed", problems[0])

    def test_a_run_that_made_no_request_fails(self) -> None:
        self.assertEqual(perf_load.verdict([], 300), ["no request was made"])

    def test_the_load_runs_many_users_over_the_three_endpoints(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Quick)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            results = perf_load.run_load(
                f"http://127.0.0.1:{server.server_address[1]}", ["t1", "t2"], users=8, seconds=0.5
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        summaries = perf_load.summarize(results)
        self.assertEqual({item.endpoint for item in summaries}, set(perf_load.ENDPOINTS))
        self.assertTrue(all(item.count > 0 and item.errors == 0 for item in summaries))
        self.assertEqual(perf_load.verdict(summaries, 300), [])

    def test_an_unreachable_server_counts_as_errors_not_a_crash(self) -> None:
        results = perf_load.run_load("http://127.0.0.1:9", ["t"], users=2, seconds=0.3)
        self.assertTrue(perf_load.verdict(perf_load.summarize(results), 300))
