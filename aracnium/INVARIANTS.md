# INVARIANTS

The rules ARACNIUM must never quietly violate. You already started this in the
sim with `K1 / K2 / K3` tags — this is their permanent home. Each invariant is
a promise; if a change breaks one, that's not a new feature, it's a regression.

Where a tool can mechanically check an invariant, it says so.

---

### K1 — One leg is a 2-link bow
The 7 anatomical segments collapse to **two IK links** (one bend at the "knee").
No full per-segment dynamics in the control path.

- `link1 = coxa + trochanter + femur + patella`
- `link2 = tibia + metatarsus + tarsus`
- *Checked:* `build_fleet.py` derives both from `spec/` so they can't drift.

### K2 — A leg is seven named segments
Rendering and CAD keep the full hierarchy of **coxa, trochanter, femur, patella,
tibia, metatarsus, tarsus** (real spider anatomy, `docs/aracneBioMechanics.md §2`).
The 2-link reduction (K1) is for *control*, not for *describing* the leg.

### K3 — The sim stays dependency-light and honest
Single HTML file, software 3D, no GPU/WebGL. Physics is the real model
(F = ma + Coulomb friction), not a fake. If a number is shown, it's computed.

---

## Invariants for the repo as a whole

### R1 — Single source of truth
Geometry, gait, and limits are defined **once**, in `spec/aracnium.toml`.
Firmware, CAD, BOM, and sim read from it; they never redefine it.

### R2 — Scale invariance (build 1 == build N)
The design is identical across every unit in a fleet. Quantity lives only in
`fleet/fleet.toml`.
- *Checked:* `build_fleet.py` hashes the design and asserts every generated
  unit shares one fingerprint. Run `python tools/build_fleet.py --check`.

### R3 — Derived numbers are derived, never re-entered
Anything computable from the spec (leg reach, servo count, scaled BOM) is
computed by a tool — never typed a second time where it can fall out of sync.

---

### R4 — The truth has exactly one file
There is **one** `aracnium.toml` in the repository, at `aracnium/spec/`. Not a
copy "for convenience", not a mirror at the root, not a symlink.

- *Checked:* `git ls-files | grep -c aracnium.toml` must print `1`.

**Why this needed its own number.** On 2026-08-18 the repo held **two**
byte-identical `aracnium.toml` files — one at `aracnium/spec/` and one at the
repository root — with nothing keeping them in sync. R1 was not violated,
because only the `spec/` copy was ever read. But R1 was one careless edit away
from being violated *silently*, and the whole point of R1 is that the failure
must not be silent.

Alongside it sat a second copy of `build_fleet.py` at the root, byte-identical
to `aracnium/tools/build_fleet.py`. It could never run: the script resolves its
own spec with `ROOT = Path(__file__).resolve().parent.parent`, which from the
root copy pointed *outside the repository entirely*. Verified: `exit=1,
ERROR: missing specracnium.toml`. The README also documented
`py -3 tools/build_fleet.py`, and no root `tools/` existed — verified `exit=2`.

All three came from one event: files were moved into `aracnium/` and the
originals were never deleted, while the README kept the old paths. **A
duplicate is not a backup. It is a second place for the truth to live, and
truth does not survive having two addresses.**

Fixed the same day. Deleting both root copies left the design fingerprint
unchanged at `fda403b08801`, which is the proof they were dead rather than
load-bearing.

---

## Adding an invariant

Give it the next number (K4, R4, …), state it as a promise in one sentence,
and note whether it's human-enforced or tool-checked. Keep it short. An
invariant nobody can state simply is an invariant nobody will keep.
