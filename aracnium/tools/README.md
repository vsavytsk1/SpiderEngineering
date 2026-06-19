# tools/

The self-reference machinery — the small amount of code that makes "build 1 ==
build N" a fact instead of a hope.

- **`build_fleet.py`** — reads `spec/aracnium.toml` × `fleet/fleet.toml`,
  derives the computed numbers (leg reach, servo count), scales the BOM, writes
  per-unit build cards, and **proves** every unit shares one design fingerprint.

```bash
python tools/build_fleet.py          # generate fleet/generated/
python tools/build_fleet.py --check  # verify only, write nothing (good for CI)
```

Stdlib only (Python 3.11+). Keep it that way — no dependency a novice has to
chase down.
