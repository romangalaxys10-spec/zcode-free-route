# Free Route

A latency scoreboard for your model endpoints: probe, rank, and know which
free provider is actually fastest right now.

## Why

Free-model users juggle routers and providers, and "which one is slow today"
is a daily question answered by vibes. Free Route answers it with TTFB and
total-time probes, EWMA-smoothed over runs.

## How it works

| Step | What happens |
|------|--------------|
| Setup | One 0600 config listing endpoints; auth header NAMES only |
| Probe | Small request per endpoint, max 4 concurrent, TTFB + total timed |
| History | EWMA per endpoint across runs in a local JSONL |
| Rank | Fastest-first table, degraded (2x own history) and errored providers flagged |

## Install

1. Clone or download this repo to a folder.
2. In ZCode: Plugin Marketplace, Add, Add Plugin Marketplace, paste that folder path.
3. Install *Free Route*, then list your endpoints in the config.

## Try it

```
/free-route
```

Expected: a ranked table with EWMA latencies and a recommendation.

## Honest limits

Latency is measured from this machine on this network; your app's users may see
different numbers. One small probe per run is a smoke test, not a benchmark.


<p align="center">
  <a href="https://z.ai/subscribe?ic=R0K78RJKNW"><img alt="z.ai coding plans - 10% OFF coupon" src="https://img.shields.io/badge/z.ai%20coding%20plans-10%25%20OFF%20coupon-blueviolet" /></a>
  <a href="https://zcode.z.ai/invite/ALWM9JUA"><img alt="Try ZCode free" src="https://img.shields.io/badge/Try%20ZCode-free%20invite-0969da" /></a>
</p>


## License

MIT.
