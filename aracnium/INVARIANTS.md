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

## Adding an invariant

Give it the next number (K4, R4, …), state it as a promise in one sentence,
and note whether it's human-enforced or tool-checked. Keep it short. An
invariant nobody can state simply is an invariant nobody will keep.
