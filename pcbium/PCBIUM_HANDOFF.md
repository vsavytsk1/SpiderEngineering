# PCBIUM — Handoff for the Next Claude

*A browser PCB-design simulator that reframes routing as geometry on a buckyball. Built collaboratively, over many turns, with the user (vsavytskyy). This document is written so you can pick the project up cold. Read it before touching the sim.*

---

## 0. The one-sentence version

You design a circuit as **points and lines on a triangulated sphere (a C60 / buckyball)**, the sim shows the *same discrete graph* unwrapped onto a **flat plane**, and the whole point is to unite the **visual monkey brain** (which reads topology at a glance) with the **machine's linear precision** (which only ever makes discrete moves) — while never drawing a single fake curve.

---

## 1. The philosophy (the user's vision — honor it)

The user thinks in an elaborate "mage / grimoire" idiom. Match it warmly, but **keep every piece of math honest**. The intellectual core is real and consistent:

- **Unite two things that were never joined:** the human visual cortex (pattern, topology, "where's the knot") and the machine's inhuman linear precision (steppers, 1s and 0s, nanoscale). The C60 is the eyes; the discrete graph is the hands; the projection is the translator.
- **Points, lines, and bits — none of which actually exist.** A point is zero-dimensional (nothing there); a line is one-dimensional (no width); a bit is presence/absence. Reality has none of these — only fields and amplitudes — yet these three fictions build *everything*, including this conversation.
- **The equal sign is the ultimate abstraction.** At the quantum foam nothing is ever equal to anything; `=` is a human invention that holds perfectly in math and rode all the way down to machines touching the nanoscale. *Math transcends the reality it describes* — that's the "magic."
- **Break the illusion of the curve.** No curve is real — not in any PCB, not on any screen. What looks smooth is **very detailed pixels**: discrete points and lines that only *read* as a curve from a distance. The engineer must never be fooled; the grid stays visible.
- **Mind → matter costs compute.** Adaptive detail (Nanite-style): subdivide/pay compute *only where the eye needs it*. "If you want to go from mind to matter, pay in compute."
- **The 12 pentagons are the irremovable constraint.** Euler forces exactly 12 pentagons (valence-5 vertices) on any icosphere (χ=2). Gauss's *Theorema Egregium*: a sphere can't flatten without concentrating curvature there — so they are the fixed seams of the projection, untouchable, no pads allowed on them.
- **Information theory as the substrate of physics** (Wheeler *it from bit*, Landauer, Bekenstein, Verlinde). Mentioned as the honest frontier, not implemented. Reality is the ultimate O(n) verification layer (every element only talks to neighbors); the sim is the cheap preview.

### The user's honesty creed (from their grimoire — apply it literally)
- **"Proof by kernel, not claim."** Verify every build numerically before presenting.
- **"Incomplete is fine, fake is not."** Never claim to implement something you didn't. (E.g. we cite the Duan et al. shortest-path paper as the frontier but keep honest Dijkstra, and say so out loud.)
- **"The price is always paid."** Costs (copper length, compute, distortion) are surfaced, never hidden.

---

## 2. Working conventions (how to build here)

- **One self-contained HTML file per version.** Pure HTML/CSS/JS + Canvas 2D. **Zero dependencies.** No frameworks, no CDN, no build step.
- Output to `/mnt/user-data/outputs/pcbium_vX_Y.html`, then `present_files`.
- **Verify EVERY build with `node` before presenting.** Extract the `<script>`, `node --check` it, and run a small kernel harness that re-derives the invariants (χ=2, 12 pentagons, whatever the new feature claims). State the verified numbers in the handoff. This is non-negotiable — it's the whole ethos, and it has caught real bugs (see the antipodal crossing bug, §6).
- **Version discipline:** each version is a frozen numbered file. Build vN+1 by copying vN, not by editing the frozen one. (Exception: a same-turn "finish it" completeness fix to the current version is fine.)
- **Aesthetic (keep consistent):** cave/terminal look — `bg #050510`, monospace, accents cyan `#00d4ff` / gold `#ffd700` / pink `#ff69b4` / green `#7fff7f`. HUD top-left, log below it, tabbed panel top-right, tool bar along the bottom.
- **3D is hand-rolled:** rotate pitch-then-yaw, gentle perspective (`CAMD=5`), depth-cue by z. No three.js.
- The `artifacts` tool is **not available** in this environment. Use `create_file` + `present_files`.
- Match the user's idiom in the reply; lead with the verified numbers; keep the handoff tight.

---

## 3. Technical architecture (as of v2.9)

**Mesh / graph.** `buildIcosphere(n)` subdivides each of the 20 icosahedron faces into a barycentric grid at `n` steps, projects to the unit sphere, welds shared vertices by a rounded-position hash, and returns `{verts, faces, edges, adj, pent, pentPos, nPent}`. `adj` is the routing graph. The 12 pentagons are the original icosahedron vertices (the only valence-5 vertices); `pent` is a set of their welded indices, `pentPos` their positions. **Always: χ = V−E+F = 2, exactly 12 pentagons.**

**Objects.**
- `pad = {id, vi, net}` — sits on a mesh vertex (never a pentagon).
- `trace = {id, a, b, net, w, layer, path}` — `path` is a **Dijkstra shortest path along mesh edges** (`routePath(sVi, tVi)`). This is the heart of v2.9: a trace is a **graph path — points and lines on the lattice — never a Bézier**.
- Nets merge when you wire two pads of different nets.

**Grid levels (LOD).** Three: `Coarse n=4` (162 pts), `Medium n=6` (362 pts), `Fine n=8` (642 pts). Changing level rebuilds the mesh, re-snaps pads to nearest free vertex, and **re-routes every trace on the new graph**. Finer grid → more hops per path → *looks* smoother while staying discrete (the pixel illusion). This is the "pay compute for detail" knob.

**Projection (the transformer).** Sphere ↔ flat plane via **equirectangular** unwrap: `unwrap(v)` → `(u = atan2(y,x)/2π, w = asin(z)/π)`, `invUnwrap` back. Round-trips to **~1e-16 (machine epsilon)** — a genuine bijection (minus the one seam meridian + poles). The plane and the C60 render the *same graph*, two drawings of one object. Honest caveat surfaced in-app: equirectangular stretches near the poles (Gauss) — a dimensionally faithful export would need a conformal/local-patch projection.

**Knots (topological congestion).** `segCrossSphere(a1,a2,b1,b2)` — true spherical arc–arc intersection: the two great circles meet at ±(nA × nB); it's a real crossing only if the **same** point lies **on both arcs** (checks both antipodal candidates — this is the fix for a subtle bug, see §6). Only **different-net, same-layer** crossings count as knots (same-net touching is harmless; different layers can't short). Knots glow red on the ball and in the shadow. **0 knots ⇒ single-layer planar-routable.**

**Multi-layer.** Traces carry a `layer`; each layer renders on a nested shell (`layerR(L) = RI·(1 − 0.11·L)`). A pad whose traces span ≥2 layers gets a **via** (radial post, counted). **`untangle()`** builds the crossing-conflict graph and **greedily colors** it so no two crossing different-net traces share a shell → knots → 0. (Minimum layers = chromatic number = NP-hard; this is the fast heuristic — stated honestly. The real superpower is the human spotting the knot by eye on the spinning sphere, no datacenter.)

**Field (physics verification layer).** Real 3D **Biot–Savart** along the copper, summed at the outer shell (`RO=1.06`), painted as a chromatic heatmap (`∇·B=0`). `knee = 500/t_rise` MHz; `critical length = (t_rise/6)/t_pd`, microstrip `t_pd = 0.0055 ns/mm`; traces longer than critical length flag as transmission lines (pink glow). Fourier spectrum panel shows the drive edge's harmonics vs the knee.

**Instrument panel (apollonium-style tabs):**
- **Field** — the sliders + spectrum above.
- **12 → □** — the 12 pentagons classified in O(1) by their single zero coordinate into **3 orthogonal golden rectangles** (1:φ), laid on a 4×3 square with the 30 icosahedron edges (each node degree 5).
- **Smith** — a real Möbius chart, `Γ = (z−1)/(z+1)`, constant-r circles + constant-x arcs, draggable Γ marker showing z, Z(×50Ω), VSWR. (Per-trace Z₀ needs a dielectric stackup — not yet built.)
- **Grid** — readouts (grid vertices, segment count, copper vs direct length) + "show grid points" toggle + the no-curves explanation.
- **I/O** — import/save.

**Import / Save.** 1-layer netlist JSON: `{name, layers, pads:[{ref,x,y,net}]}`. Pads map onto the C60 by the **equirectangular inverse** (normalized to a patch) + nearest-free-vertex snap; nets connect by **minimum spanning tree**; each trace routes as a graph path. Embedded sample: **NE555 astable blinker** (22 pads, 7 nets, 15 MST traces) — auto-loads on boot. Save serializes pads+nets back to JSON.

---

## 4. Version-by-version (what each one added)

| Ver | What it introduced |
|----|----|
| **v0.1** | Flat 2D rectangular PCB sandbox. pad=node, net=intent, trace=edge, ratsnest=airwire. RS-274X (Gerber) export of top/bottom copper. |
| **v1.1** | + Maxwellium×Chromium field layer: real 2D Biot–Savart Bz heatmap on the board; Fourier spectrum + knee; transmission-line highlight past critical length. |
| **v2.0** | **LEAP to 3D.** Design on a triangulated icosphere (C60 base); field as an outer ghost shell (3D Biot–Savart); routing along the triangle-edge graph (Dijkstra); orthographic "shadow." χ=2 verified. |
| **v2.1** | The 12 pentagons as fixed projection constraints (Euler-forced, untouchable, no pads). Shadow = 20-panel icosahedral unfold (Dymaxion-style); each pentagon splits into 5 seam corners. |
| **v2.2** | apollonium-style tabbed panel: Field, 12→□ (golden-rectangle map), Smith (Möbius chart). |
| **v2.3** | **Simplified** the shadow to a single flat plane (equirectangular unwrap) — dropped the over-built 20-panel unfold. |
| **v2.4** | Traces made **direct** (great-circle geodesic on the sphere, straight in the shadow). Import 1-layer netlist + save panel. Buckyball/"add hexagons" framing. **Bow:** Duan–Mao–Mao–Shu–Yin shortest-path paper. |
| **v2.5** | **Stepper-motor curves:** traces bow into spherical quadratic Bézier arcs (a curvature DOF), rendered as N discrete stepper moves; "show steps" reveal. "A curve is points and lines." |
| **v2.6** | **Topological knot detection** — true spherical crossing math (the antipodal false-positive was caught here and fixed). Knots glow red. |
| **v2.7** | **Nanite adaptive tessellation:** each trace's move-count set by its on-screen size (~pixel per move), recomputed as you zoom — pay compute only where a facet would show. **Bow:** Karis–Stubbe–Wihlidal, Nanite. |
| **v2.8** | **Multi-layer shells:** knots counted per layer; vias where a pad's traces span shells; `untangle()` greedy layer-coloring; Layer tool to move a trace by hand. |
| **v2.9** | **THE HONEST TRANSFORMER.** Killed all Bézier/curvature. A trace is now a **pure graph-space path** (Dijkstra along mesh edges) — points and lines only. 3 grid levels (Coarse/Medium/Fine). The "curve" is *only* the fine-grid pixel illusion; zoom in and it breaks. Same graph on the plane and the C60. (Same-turn fix: ratsnest airwires drawn straight too — zero curves anywhere in the program.) |

---

## 5. Verified invariants (the kernel results to preserve)

Every one of these was checked with `node`. If you refactor, re-check them.

- **χ = V − E + F = 2** at every subdivision (n = 2…8).
- **Exactly 12 pentagons** (valence-5 vertices) at every subdivision.
- **Equirectangular round-trip** error ≈ 7.9e-16 (machine epsilon) — real bijection.
- **Golden rectangles:** the 12 split 3 × 4 = 12; the icosahedron graph among them has **30 edges, every vertex degree 5**.
- **Smith:** z=1→center, z=0→short (Γ=−1), z=∞→open (Γ=+1); z↔Γ round-trips exactly; all r-circles tangent at the open.
- **Spherical crossing** (`segCrossSphere`): finds real crossings, **rejects antipodal false-positives**, rejects parallels.
- **Greedy untangle:** produces a *valid* coloring — **0 same-layer conflicts** remain (e.g., 3 stacked knots → 2 shells, 0 conflicts).
- **Graph path:** every consecutive hop in a routed trace is a **real mesh edge** — the trace lives in the graph, not on a drawn curve.
- (Pre-v2.9 stepper Bézier: endpoints exact, curvature 0 = geodesic, tessellation converges — retained here only as history.)

---

## 6. War story: the antipodal crossing bug (why we verify)

First `segCrossSphere` used the two-sided plane test: b1,b2 on opposite sides of arc-A's plane **and** a1,a2 on opposite sides of arc-B's plane. The kernel harness flagged a **false hit** on two arcs near opposite poles. Reason: two arcs can each cross the *other's great-circle plane* at **antipodal** intersection points and never actually meet. Fix: compute the intersection point ±p and require the **same** point to lie **on both arcs** (via `onArc`). This is exactly why "proof by kernel" is load-bearing — the sphere doesn't let you lie.

---

## 7. The bows (real, checked citations)

- **Shortest path:** Ran Duan, Jiayi Mao, Xiao Mao, Xinkai Shu, Longhui Yin — *"Breaking the Sorting Barrier for Directed Single-Source Shortest Paths,"* **STOC 2025 Best Paper.** Deterministic **O(m·log^(2/3) n)** — first to beat Dijkstra's O(m + n log n) on sparse graphs since 1959. arXiv:2504.17033. **We cite it as the frontier for obstacle-aware routing; Dijkstra is what actually runs — say so.**
- **LOD / adaptive detail:** Brian Karis, Rune Stubbe, Graham Wihlidal (Epic) — *"A Deep Dive into Nanite Virtualized Geometry,"* **SIGGRAPH 2021.** Hierarchical clusters, screen-space error, "only as many triangles as pixels." The basis for the adaptive-tessellation idea and the pay-compute-where-the-eye-needs-it framing.
- **Signal integrity** (from the user's own grimoire, cited there): knee frequency, critical length, microstrip propagation delay.

---

## 8. Roadmap — the four open doors (the user picks)

1. **Complete Maxwell** — add the **E-field (capacitive) shell** inside the B-field shell so the copper lives in the full volume the equations describe.
2. **Real Z₀** — a **dielectric stackup** so each trace's characteristic impedance is computed, and the Smith chart plots the *actual* traces as points instead of a marker you drag. (Electrically-long traces then become real Smith points.)
3. **Duan routing + squiggles** — **obstacle-aware graph routing** (traces detour around each other's copper) so knots fall to zero *by geometry*, not just by adding layers — this is where the Duan et al. algorithm finally runs for real. Then **squiggle length-matching** (tune the routed detour to a target length for signal integrity).
4. **The bit layer** — an **information readout**: the board reduced to the bits its topology encodes, with the **Landauer floor** (kT·ln2 per bit erased) shown in joules. Points, lines, and bits made literal — the user's endgame.

Other standing wants: Gerber export straight off the flat plane (now trivial, with the honest distortion caveat); multi-layer as truly nested buckyball shells with plated through-holes; expand the import panel into a saved-board library; scale toward a whole microchip (many nets weaving with zero knots).

---

## 9. Gotchas / context

- **Repos** (cloned to `/home/claude`): `SpiderEngineering`, `Mnetv1`. The grimoire scrolls define the idiom and the (real, cited) PCB physics. Prior sims to echo in style: **smithium** (Smith chart), **apollonium** (tabbed dossier panel), **genesis** (raw-canvas icosphere). The user swapped genesis's "random ops" for deterministic error-metric subdivision (Nanite).
- The user uploaded a **Grundig Satellit 1000 schematic** as the recurring *villain* — the dense, ego-laden, unintuitive EDA this whole project is a reaction against. Invoke it when contrasting "wall of glyphs you must already understand" vs "points and lines you can spin."
- **Keys:** `P`/`W`/`E`/`L` tools (place/wire/erase/layer), `U` untangle, `Space` sphere↔shadow, `S` spin, `F` field, `I` panels, `R` ratsnest, `K` knots, `1`/`2`/`3` grid level, `C` clear, `N` new net, `[`/`]` trace width. Wheel = zoom (zoom in to break the curve illusion).
- **Tone with the user:** enthusiastic, collaborative, idiom-matching ("bro," "claudy mage," "trivial"). But every claim you make must be backed by a kernel check. When they push a new concept, find the *honest, achievable* core of it and build that; be transparent about what you did and didn't implement.

---

*χ = 2 · 12 pentagons · no curve, ever · points, lines, and the graph. The sphere earned its keep. Carry it well.*
