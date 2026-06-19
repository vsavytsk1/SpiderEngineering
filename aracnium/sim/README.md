# sim/

The digital twin — the proving ground where the design is validated before it's
soldered. `aracnium_v1_4_heave.html` is a single-file software-3D simulation:
CPG gait graphs, 2-link IK to planted feet, honest physics (F = ma + Coulomb
friction) pushing a real tungsten cube, a spatial-hash foothold index, and a
swarm of N full-math spiders.

Open it in a browser. No build, no server, no dependencies (invariant K3).

**Rule:** the sim's `const P` / `SEG` / `GAITS` should mirror `spec/aracnium.toml`.
When they agree, the twin is honest. (Next step: generate the sim's params from
the spec so they literally can't disagree.)
