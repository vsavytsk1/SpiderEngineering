# fleet/

How many spiders, and nothing else.

- **`fleet.toml`** — `count = N`. The single knob that turns one design into a
  fleet. Per-unit overrides go here too (only when a physical unit *must* differ).
- **`generated/`** — output of `tools/build_fleet.py`: one card per unit + a
  scaled BOM. Reproducible, so it's git-ignored — regenerate any time.

Build 1, build 10, build 100: same design, same command, different number.
