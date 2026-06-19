# 🕷 ARACNIUM

Small helpful robot spiders that fetch, carry, and — yes — pass the butter.
Built for **absolute scale** and **absolute simplicity**: the design for *one*
spider and the design for *ten* are the same design. Building more is a number,
not a rewrite.

> _"You pass the butter."_ — but with real engineering rigor.

---

## The one principle

Everything in this repo obeys a single rule:

> **One design is the source of truth. A unit is that design built once.
> A fleet is that design built N times. Nothing redescribes the spider.**

```
   spec/aracnium.toml        ← THE spider. one file. one truth.
          │
          │  read by everything below (they never re-define geometry)
          ├──────────────┬───────────────┬──────────────┐
          ▼              ▼               ▼              ▼
     firmware/        hardware/         sim/         docs/
   (runs on MCU)   (PCB·CAD·BOM)   (digital twin)   (the "why")
          │
          │  × fleet/fleet.toml   (count = 1 … or 10 … same design)
          ▼
   tools/build_fleet.py  →  fleet/generated/  (per-unit cards + scaled BOM)
```

This is the same idea your sim already uses: `const P` / `SEG` define one
spider, and `SWARM` runs N of them from that one definition. This repo just
lifts that from one HTML file up to the whole project.

---

## Build one spider (or ten)

```bash
# 1 spider:
python tools/build_fleet.py

# 10 spiders — change ONE number in fleet/fleet.toml:
#   count = 10
python tools/build_fleet.py
```

The generator stamps the same design N times and **proves** every unit is
identical (a shared design fingerprint) — only the serial number differs.
The bill of materials scales ×N automatically.

---

## What's where

| Folder        | What lives here                                              |
|---------------|-------------------------------------------------------------|
| `spec/`       | **The single source of truth.** One spider, as data (TOML). |
| `fleet/`      | `fleet.toml` — the only place "how many" lives. The 1↔N knob.|
| `tools/`      | `build_fleet.py` — expands spec × fleet → per-unit artifacts.|
| `hardware/`   | The physical spider: `pcb/`, `cad/`, `bom/`, `assembly/`.    |
| `firmware/`   | What runs on the microcontroller in each real spider.       |
| `sim/`        | The digital twin — your `aracnium_v1_4_heave.html`.         |
| `docs/`       | The reasoning — `aracneBioMechanics.md` (the biology).      |
| `INVARIANTS.md` | The rules that must always hold (your K1/K2/K3, formalized).|
| `VERSION`     | Design codename. The git tag is the real version of record. |

---

## Rules of the repo (so it stays clean as it grows)

1. **Geometry is defined once, in `spec/`.** If you're typing a leg length
   anywhere else, stop — read it from the spec instead.
2. **Quantity lives only in `fleet/fleet.toml`.** Code never hard-codes "10".
3. **Invariants don't break silently.** See `INVARIANTS.md`; `build_fleet.py`
   checks the ones it can.
4. **One spider = ten spiders.** If a change makes those two cases diverge,
   it's a bug.

---

## Status

Currently at design **mk1**, lifted from sim milestone **v1.4 "THE HEAVE."**
The sim is the proving ground; hardware/firmware grow to match the spec it
already validates.
