# clawidth-bridge

A tiny PC service that reads your **local Claude Code logs** and serves your token
usage as JSON on your LAN, so the [Clawidth](../README.md) watch (or anything else) can
show it at a glance.

- **Stdlib only.** No `pip install`, no dependencies. Python 3.8+.
- **Nothing personal, nothing hardcoded.** It auto-discovers whatever Claude logs exist
  for the current user on whatever machine you run it on.
- **No API key. No cloud.** It only reads local logs and only serves aggregate numbers
  on your own network.

## Run it

```bash
python clawidth_bridge.py
# -> serving on http://0.0.0.0:8088/usage
```

Open <http://localhost:8088/usage> (or the index page at <http://localhost:8088/>) to
see it working. Then point the watch at `http://<your-PC-LAN-IP>:8088/usage` in
[`../src/config.py`](../src/config.py).

### Handy flags

```bash
python clawidth_bridge.py --once               # print the JSON once and exit (testing)
python clawidth_bridge.py --port 9000          # change the port
python clawidth_bridge.py --token-limit 20000000   # enable window_pct vs your own budget
python clawidth_bridge.py --include-cache-read     # fold cheap cache-reads into the headline
python clawidth_bridge.py --window-hours 5     # size of the rolling usage window
```

## What it serves

```json
{
  "status": "OK",
  "updated": 1749200000,
  "tokens_today": 44829390,
  "tokens_window": 22678392,
  "out_tokens_today": 4117591,
  "cache_read_today": 298560770,
  "window_min_left": 154,
  "window_pct": null,
  "window_limit": null,
  "burn_tpm": 156172,
  "model": "claude-opus-4-8",
  "cost_today_cents": null
}
```

| Field | Meaning |
|-------|---------|
| `tokens_today` / `tokens_window` | input + output + cache-creation tokens (the real work) for today / the last 5 h |
| `cache_read_today` | cheap cached-context re-reads, reported separately (huge, mostly free) |
| `out_tokens_today` | output tokens generated today |
| `window_min_left` | minutes left in the current rolling 5-hour window (**local estimate**) |
| `burn_tpm` | recent burn rate, tokens/minute |
| `window_pct` / `window_limit` | only set if you pass `--token-limit`; a **local estimate**, not the official figure |
| `model` | the most recent model id |
| `status` | `OK`, `NO-LOGS`, or `ERROR` |

## Where it looks for logs

In order: `$CLAUDE_CONFIG_DIR/projects`, then `~/.claude/projects`, then
`~/.config/claude/projects`. If none exist it warns and serves zeros.

## Honesty notes

- The official Claude.ai **5-hour / weekly limit %** has no public API — it's in-app
  only. Any `window_pct` here is a **local estimate** derived from your logs and will
  diverge from Settings → Usage.
- Cost is **tokens-first**: `cost_today_cents` is `null`. Pricing changes per model and
  is best handled by a dedicated tool like [ccusage](https://github.com/ryoppippi/ccusage)
  if you want dollars.

See [`../docs/USAGE_WATCH.md`](../docs/USAGE_WATCH.md) for the full architecture.
