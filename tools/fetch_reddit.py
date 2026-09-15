#!/usr/bin/env python3
"""Mirror the top posts of the last year, with comments, from the trip's three subreddits.

Writes one JavaScript file per subreddit into reddit/data/. They are .js rather than
.json so that reddit/index.html can load them with a plain <script> tag and therefore
works from file:// — no server, no network, genuinely offline.

Runs on the standard library alone. Anonymous requests work but are rate limited and
are often refused outright from datacenter IPs; set REDDIT_CLIENT_ID and
REDDIT_CLIENT_SECRET (a "script" app at reddit.com/prefs/apps) to use the OAuth API
instead, which is what CI does.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SUBREDDITS = ["chinatravel", "tibettravel", "shanghaidisneyland"]

USER_AGENT = "python:china-tibet-2026-reddit-mirror:1.0 (offline trip research mirror)"
PUBLIC_HOST = "https://www.reddit.com"
OAUTH_HOST = "https://oauth.reddit.com"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# Reddit's own ceiling on listing pages; asking for more is silently clamped.
PAGE_SIZE = 100


class Fetcher:
    """A thin reddit client: one token, one pace, retries on the retryable codes."""

    def __init__(self, pause: float, retries: int, verbose: bool = True):
        self.pause = pause
        self.retries = retries
        self.verbose = verbose
        self.token = None
        self.host = PUBLIC_HOST
        self._last_request = 0.0

    # -- auth ------------------------------------------------------------

    def authenticate(self) -> bool:
        client_id = os.environ.get("REDDIT_CLIENT_ID", "").strip()
        secret = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
        if not client_id or not secret:
            return False

        body = {"grant_type": "client_credentials"}
        username = os.environ.get("REDDIT_USERNAME", "").strip()
        password = os.environ.get("REDDIT_PASSWORD", "").strip()
        if username and password:
            body = {"grant_type": "password", "username": username, "password": password}

        basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
        req = urllib.request.Request(
            TOKEN_URL,
            data=urllib.parse.urlencode(body).encode(),
            headers={"Authorization": f"Basic {basic}", "User-Agent": USER_AGENT},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.URLError as err:
            self.log(f"  auth failed ({err}); continuing anonymously")
            return False

        self.token = payload.get("access_token")
        if not self.token:
            self.log("  auth returned no token; continuing anonymously")
            return False
        self.host = OAUTH_HOST
        self.log(f"  authenticated ({body['grant_type']})")
        return True

    # -- transport -------------------------------------------------------

    def log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def get(self, path: str, params: dict | None = None):
        url = f"{self.host}{path}"
        query = dict(params or {})
        query["raw_json"] = 1
        url = f"{url}?{urllib.parse.urlencode(query)}"

        headers = {"User-Agent": USER_AGENT}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        delay = self.pause
        for attempt in range(self.retries + 1):
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.pause:
                time.sleep(self.pause - elapsed)
            self._last_request = time.monotonic()

            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as err:
                retryable = err.code in (429, 500, 502, 503, 504)
                if not retryable or attempt == self.retries:
                    raise
                wait = float(err.headers.get("Retry-After") or 0) or delay
                self.log(f"    HTTP {err.code} on {path}; retrying in {wait:.0f}s")
                time.sleep(wait)
                delay = min(delay * 2, 60)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
                if attempt == self.retries:
                    raise
                self.log(f"    {type(err).__name__} on {path}; retrying in {delay:.0f}s")
                time.sleep(delay)
                delay = min(delay * 2, 60)
        raise RuntimeError("unreachable")


# -- shaping -------------------------------------------------------------

def clean_post(data: dict) -> dict:
    """Keep the fields the page actually renders, and drop reddit's other 180."""
    return {
        "id": data.get("id"),
        "title": data.get("title") or "",
        "author": data.get("author") or "[deleted]",
        "created_utc": int(data.get("created_utc") or 0),
        "score": int(data.get("score") or 0),
        "upvote_ratio": data.get("upvote_ratio"),
        "num_comments": int(data.get("num_comments") or 0),
        "permalink": data.get("permalink") or "",
        "url": data.get("url") or "",
        "domain": data.get("domain") or "",
        "is_self": bool(data.get("is_self")),
        "selftext": data.get("selftext") or "",
        "flair": data.get("link_flair_text") or "",
        "over_18": bool(data.get("over_18")),
        "stickied": bool(data.get("stickied")),
        "comments": [],
        "comments_omitted": 0,
    }


def clean_comment(data: dict, replies: list) -> dict:
    return {
        "id": data.get("id"),
        "author": data.get("author") or "[deleted]",
        "created_utc": int(data.get("created_utc") or 0),
        "score": None if data.get("score_hidden") else int(data.get("score") or 0),
        "body": data.get("body") or "",
        "is_op": bool(data.get("is_submitter")),
        "distinguished": data.get("distinguished") or "",
        "replies": replies,
    }


def walk_comments(listing, depth: int, max_depth: int, budget: list) -> tuple[list, int]:
    """Flatten reddit's comment listing into a plain tree. Returns (tree, omitted)."""
    out, omitted = [], 0
    if not isinstance(listing, dict):
        return out, omitted

    for child in listing.get("data", {}).get("children", []):
        if child.get("kind") == "more":
            omitted += int(child.get("data", {}).get("count") or 0)
            continue
        if child.get("kind") != "t1":
            continue
        if budget[0] <= 0:
            omitted += 1
            continue

        data = child.get("data", {})
        budget[0] -= 1
        replies, deeper_omitted = ([], 0)
        if depth + 1 < max_depth:
            replies, deeper_omitted = walk_comments(data.get("replies"), depth + 1, max_depth, budget)
        elif data.get("replies"):
            deeper_omitted = int(data.get("num_replies") or 1)
        omitted += deeper_omitted
        out.append(clean_comment(data, replies))

    return out, omitted


def fetch_subreddit(fetcher: Fetcher, sub: str, want_posts: int, args) -> dict:
    fetcher.log(f"r/{sub}")
    posts, after, seen = [], None, set()

    while len(posts) < want_posts:
        params = {"t": "year", "limit": min(PAGE_SIZE, want_posts - len(posts))}
        if after:
            params["after"] = after
        listing = fetcher.get(f"/r/{sub}/top", params)
        children = listing.get("data", {}).get("children", [])
        if not children:
            break
        for child in children:
            data = child.get("data", {})
            if data.get("id") in seen:
                continue
            seen.add(data.get("id"))
            posts.append(clean_post(data))
        after = listing.get("data", {}).get("after")
        if not after:
            break

    posts = posts[:want_posts]
    fetcher.log(f"  {len(posts)} posts; fetching comments")

    for index, post in enumerate(posts, 1):
        try:
            payload = fetcher.get(
                f"/r/{sub}/comments/{post['id']}",
                {"sort": "top", "limit": args.comments, "depth": args.depth},
            )
        except (urllib.error.HTTPError, urllib.error.URLError) as err:
            fetcher.log(f"    [{index}/{len(posts)}] {post['id']}: {err}; skipping comments")
            continue
        if isinstance(payload, list) and len(payload) > 1:
            budget = [args.comments]
            post["comments"], post["comments_omitted"] = walk_comments(
                payload[1], 0, args.depth, budget
            )
        if index % 10 == 0 or index == len(posts):
            fetcher.log(f"    [{index}/{len(posts)}] comments")

    posts.sort(key=lambda p: (-p["score"], -p["created_utc"]))
    return {
        "subreddit": sub,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": "year",
        "posts": posts,
    }


def write_js(path: str, global_name: str, payload: dict) -> int:
    body = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False)
    text = (
        "// Generated by tools/fetch_reddit.py — do not edit by hand.\n"
        f"(window.{global_name} = window.{global_name} || {{}})"
        f"[{json.dumps(payload.get('subreddit') or 'manifest')}] = {body};\n"
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return len(text.encode())


def main() -> int:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subs", nargs="+", default=SUBREDDITS, help="subreddits to mirror")
    parser.add_argument("--posts", type=int, default=100, help="top posts per subreddit")
    parser.add_argument("--comments", type=int, default=40, help="max comments kept per post")
    parser.add_argument("--depth", type=int, default=6, help="max comment nesting kept")
    parser.add_argument("--pause", type=float, default=1.2, help="seconds between requests")
    parser.add_argument("--retries", type=int, default=4, help="retries per request")
    parser.add_argument("--out", default=os.path.join(here, "reddit", "data"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    fetcher = Fetcher(args.pause, args.retries, verbose=not args.quiet)
    fetcher.authenticate()

    manifest = {"subreddit": "manifest", "generated_at": datetime.now(timezone.utc)
                .isoformat(timespec="seconds"), "window": "year", "subs": []}
    failures = []

    for sub in args.subs:
        try:
            payload = fetch_subreddit(fetcher, sub, args.posts, args)
        except (urllib.error.HTTPError, urllib.error.URLError) as err:
            fetcher.log(f"  r/{sub} failed: {err}")
            failures.append(sub)
            continue

        size = write_js(os.path.join(args.out, f"{sub}.js"), "REDDIT_MIRROR", payload)
        comments = sum(count_comments(p["comments"]) for p in payload["posts"])
        manifest["subs"].append({
            "name": sub,
            "posts": len(payload["posts"]),
            "comments": comments,
            "fetched_at": payload["fetched_at"],
            "bytes": size,
        })
        fetcher.log(f"  wrote {sub}.js — {len(payload['posts'])} posts, {comments} comments, {size // 1024} KB")

    write_js(os.path.join(args.out, "manifest.js"), "REDDIT_MIRROR_META", manifest)

    if failures:
        print(f"failed: {', '.join(failures)}", file=sys.stderr)
        return 1 if len(failures) == len(args.subs) else 0
    return 0


def count_comments(nodes: list) -> int:
    return sum(1 + count_comments(node["replies"]) for node in nodes)


if __name__ == "__main__":
    sys.exit(main())
