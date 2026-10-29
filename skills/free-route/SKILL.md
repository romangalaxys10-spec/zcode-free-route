---
name: free-route
description: Probe OpenAI-compatible endpoints for latency, keep EWMA history across runs, and recommend the currently fastest provider. Use when juggling free providers or diagnosing which router is slow today.
---

# Free Route

## Setup (once)

`~/.config/zcode-free-route/config.json` (0600):

    {"endpoints": [
      {"name": "provider-a", "base_url": "https://api.example.com/v1",
       "model": "model-x", "auth_header_env": "PROVIDER_A_KEY"}]}

Auth is a header env var NAME; the script reads the value from the environment
at run time and never stores or prints it.

## Procedure

1. PROBE: `python3 skills/free-route/scripts/probe_endpoints.py` (or --json).
   Each endpoint gets a small request; TTFB and total are recorded; history
   accumulates in `~/.local/share/zcode-free-route/history.jsonl`.
2. RANK: present the fastest-first table. Flag providers whose EWMA degraded
   more than 2x against their own history, and any that errored.
3. ROUTE: recommend the current best and note the second best as failover.
   The plugin never rewrites any harness config by itself; switching is a
   human decision (or use config-sync).

## Hard rules

- Never print or persist secret values.
- Probe concurrency max 4; be polite to free endpoints.
