# `reddit/data/` — generated, not written by hand

`tools/fetch_reddit.py` writes one file here per subreddit, plus `manifest.js` recording
what the last run produced. Everything in this directory is overwritten on each refresh.

They are `.js`, not `.json`, for one reason: a `<script src="…">` tag loads from `file://`
and `fetch()` does not. That is what lets `reddit/index.html` open by double-click on a
laptop with no server and no network — which is the point of mirroring the subreddits in
the first place, since reddit is blocked in China.

Each file assigns into a global:

```js
window.REDDIT_MIRROR["chinatravel"] = {
  subreddit: "chinatravel",
  fetched_at: "2026-09-15T09:21:04+00:00",
  window: "year",
  posts: [ { id, title, author, created_utc, score, upvote_ratio, num_comments,
             permalink, url, domain, is_self, selftext, flair, over_18, stickied,
             comments: [ { id, author, created_utc, score, body, is_op,
                           distinguished, replies: [ … ] } ],
             comments_omitted: 0 } ]
};
```

`comments_omitted` is reddit's own count of what sits behind "load more comments" plus
anything cut by `--comments` / `--depth`; the page shows it next to the comment count so
a thin thread is never mistaken for a quiet one.
