#!/usr/bin/env python3
"""Load test: concurrent users against the identity and panel endpoints (SYS-NFR-02).

    make perf                      # 50 users for 20 seconds, p95 must stay within 300 ms

Every user is a thread that signs in as a seeded student and keeps asking `/me`, `/panel`,
`/panel/services` in turn over one connection. The report gives the count, errors and the 50th,
95th and 99th percentile per endpoint. Exit status 1 when any request failed or a p95 is over
the limit. The result depends on the machine and on the server (Django's development server
is slower than a production one), so record it with the setup it was measured on.
"""

import argparse
import http.client
import sys
import threading
import time
import urllib.parse
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import requests
from envfile import setting as env_setting

ROOT = Path(__file__).resolve().parent.parent
ENDPOINTS = ("/api/v1/me", "/api/v1/panel", "/api/v1/panel/services")
TIMEOUT_SECONDS = 30


@dataclass
class Samples:
    latencies_ms: list[float] = field(default_factory=list)
    errors: int = 0


def percentile(values: Sequence[float], q: float) -> float:
    """The q-th percentile (0 to 100) by the nearest-rank method; 0 for no values."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, -(-len(ordered) * q // 100))
    return ordered[int(rank) - 1]


@dataclass(frozen=True)
class Summary:
    endpoint: str
    count: int
    errors: int
    p50: float
    p95: float
    p99: float


def summarize(results: dict[str, Samples]) -> list[Summary]:
    return [
        Summary(
            endpoint,
            len(samples.latencies_ms) + samples.errors,
            samples.errors,
            percentile(samples.latencies_ms, 50),
            percentile(samples.latencies_ms, 95),
            percentile(samples.latencies_ms, 99),
        )
        for endpoint, samples in sorted(results.items())
    ]


def verdict(summaries: Sequence[Summary], limit_ms: float) -> list[str]:
    """What is wrong, as readable lines. Empty means the run met the target."""
    problems: list[str] = []
    if not summaries or not any(item.count for item in summaries):
        return ["no request was made"]
    for item in summaries:
        if item.errors:
            problems.append(f"{item.endpoint}: {item.errors} of {item.count} requests failed")
        if item.p95 > limit_ms:
            problems.append(f"{item.endpoint}: p95 {item.p95:.0f} ms is over {limit_ms:.0f} ms")
    return problems


def worker(
    base: str,
    token: str,
    deadline: float,
    results: dict[str, Samples],
    lock: threading.Lock,
    start: threading.Barrier,
) -> None:
    parts = urllib.parse.urlsplit(base)
    connection = http.client.HTTPConnection(parts.hostname or "", parts.port or 80, TIMEOUT_SECONDS)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    start.wait()
    turn = 0
    while time.perf_counter() < deadline:
        endpoint = ENDPOINTS[turn % len(ENDPOINTS)]
        turn += 1
        began = time.perf_counter()
        try:
            connection.request("GET", endpoint, headers=headers)
            response = connection.getresponse()
            response.read()
            ok = response.status == 200
        except (OSError, http.client.HTTPException):
            ok = False
            connection.close()
            connection = http.client.HTTPConnection(
                parts.hostname or "", parts.port or 80, TIMEOUT_SECONDS
            )
        elapsed = (time.perf_counter() - began) * 1000
        with lock:
            samples = results.setdefault(endpoint, Samples())
            if ok:
                samples.latencies_ms.append(elapsed)
            else:
                samples.errors += 1


def run_load(base: str, tokens: Sequence[str], users: int, seconds: float) -> dict[str, Samples]:
    results: dict[str, Samples] = {}
    lock = threading.Lock()
    start = threading.Barrier(users)
    deadline = time.perf_counter() + seconds
    threads = [
        threading.Thread(
            target=worker,
            args=(base, tokens[number % len(tokens)], deadline, results, lock, start),
        )
        for number in range(users)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def student_tokens(count: int) -> list[str]:
    import seed_generate

    password = env_setting(ROOT, "SEED_DEFAULT_PASSWORD")
    if not password:
        raise SystemExit("error: SEED_DEFAULT_PASSWORD is not set (see .env)")
    url = env_setting(ROOT, "KEYCLOAK_URL", "http://keycloak:8080").rstrip("/")
    realm = env_setting(ROOT, "KEYCLOAK_REALM", "gradian")
    students = [
        p.mobile
        for p in sorted(seed_generate.load_seed(ROOT).people, key=lambda p: p.mobile)
        if p.role == "student"
    ][:count]
    tokens: list[str] = []
    for mobile in students:
        response = requests.post(
            f"{url}/realms/{realm}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "gradian-test",
                "username": mobile,
                "password": password,
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        tokens.append(str(response.json()["access_token"]))
    return tokens


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://core:8000", help="base URL of the Core Service")
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--p95-limit", type=float, default=300, help="milliseconds")
    parser.add_argument("--distinct-users", type=int, default=10, help="seeded students to sign in")
    args = parser.parse_args()

    tokens = student_tokens(min(args.distinct_users, args.users))
    for endpoint in ENDPOINTS:  # first requests create the profile, so they are not measured
        requests.get(
            args.url + endpoint, headers={"Authorization": f"Bearer {tokens[0]}"}, timeout=30
        )
    print(f"{args.users} users for {args.seconds:.0f} s against {args.url}")
    results = run_load(args.url, tokens, args.users, args.seconds)
    summaries = summarize(results)
    print(f"{'endpoint':28} {'requests':>9} {'errors':>7} {'p50':>7} {'p95':>7} {'p99':>7}  (ms)")
    for item in summaries:
        print(
            f"{item.endpoint:28} {item.count:9d} {item.errors:7d} "
            f"{item.p50:7.0f} {item.p95:7.0f} {item.p99:7.0f}"
        )
    problems = verdict(summaries, args.p95_limit)
    for problem in problems:
        print(f"FAIL {problem}")
    print("\nthe run met the target" if not problems else f"\n{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
