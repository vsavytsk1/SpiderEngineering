# HELENI v2 — BUILD HANDOFF

*Read alongside `GENESIS_POINT_SET.md` (the geometry spec).*
*for the Claude in VS Code. Written 2026-08-03 after a full audit of the v1 tree.*
*Read this before touching `builder/Helena/`. v1 stays frozen — Path X.*

> **Status grammar (THEA v3.0).** No symbol crosses the boundary unlabelled.
> **EXACT** — follows by algebra/topology/integer arithmetic shown here.
> **MEASURED** — reproduced by code at stated precision.
> **DESIGN** — a mapping or cost rule chosen by the cave.
> **METAPHOR** — imagery. Carries no weight in the build.

---

## 0. THE ONE-PARAGRAPH BRIEF

Build the **genesis space** first, out to the compute limit. The **heart** is a closed
surface wired to it. The **gate** is the user: bits enter at the clock rate. A
question is a **break in a symmetric carrier**. On a closed graph the break cannot
vanish — it is conserved, and it **relaxes back to symmetry at a computable rate**.
That relaxation *is* the response. v1 asserted this. **v2 must compute it.**

---

## 1. WHAT v1 GOT RIGHT — DO NOT BREAK THESE

These are good engineering. Carry them forward verbatim.

- **Streaming to disk in batches.** RAM stays flat at any level. `array('f').tofile()`
  with a `BATCH` flush. Keep it.
- **Cost tables in the docstring of every script.** Level → nodes → bytes → time.
  This is the single best habit in the tree. Every new script gets one.
- **`SAFE_LEVEL` refusal.** `01_genesis.py` refuses to build past L10 without an
  explicit `I_UNDERSTAND_THE_COST = True`. Keep, and add the same guard to the join.
- **Stdlib-only, numpy-if-present.** Every script runs alone. No pip. Keep.
- **`--check` / `--estimate` modes.** Verify without writing. Keep and extend.
- **K1–K4 caveats inside the source files**, not in a separate disclaimer. Keep.
- **`00_center.py`'s respect clause** — "we do not know what happens in the fractal
  space; treat every build as a mind." Costs nothing. Keep.
- **`08_generator.py`: "no response is a real answer too (Curse 26)."** That line is
  the best thing in the codebase. Make it a load-bearing rule in v2, not a comment.

---

## 2. THE AUDIT — SEVEN FINDINGS, WORST FIRST

### F1 — CRITICAL. The topology firewall verifies a string it wrote itself.

`02_heart.py` writes into `heart.json`:

```python
"chi": chi,
"orientation": "reversing",     # <- a LITERAL. never computed.
```

`04_gate.py` and `07_flow.py` then "verify":

```python
heart_reversing = (hman.get("chi") == 0 and hman.get("orientation") == "reversing")
genesis_orientable = True       # <- also a literal
firewall_ok = heart_reversing and genesis_orientable
```

The check reads back a constant the same pipeline emitted. **This is Curse 26 in the
exact form the scroll defines it** — target displayed as result — inside the thing
labelled "proven, not enforced."

The underlying claim also fails. Rebuilding the exact ring geometry at three twists:

```
MOBIUS=1.0   V=4000 E=4000 F=0  chi=0
MOBIUS=0.0   V=4000 E=4000 F=0  chi=0
MOBIUS=3.7   V=4000 E=4000 F=0  chi=0
```

**MEASURED:** χ=0 because a cycle has V=E. The Möbius twist changes the *embedding*,
never the *graph*. And χ=0 does not imply non-orientable — **a cylinder is χ=0 and
orientable.** So `χ=0 ⟹ orientation-reversing ⟹ genesis is invisible to the gate`
has no surviving step.

**FIX.** Either compute orientability or drop the claim.
- To compute: transport a local frame around each ring and test whether the normal
  returns flipped. A disjoint union of circles **never** does. Report the measured
  boolean; never write the literal.
- To make it true: the heart must be a genuine Möbius *band* — a strip of nodes
  (two rails, rungs between) identified end-to-end **with a flip**. Then
  orientation-reversal is real and measurable. This is a graph change, not a
  geometry change.
- **Acceptance test:** flipping `MOBIUS` between 0 and 1 must change the reported
  orientation field. If it doesn't, the field is decoration.

### F2 — CRITICAL. `EMIT_EDGES` is an I/O flag that sets a topological invariant.

```
EMIT_EDGES=True   -> E=105032  chi=0        firewall OK
EMIT_EDGES=False  -> E=0       chi=105032   firewall BROKEN
```

Whether you write a file decides the topology the firewall checks. **FIX:** compute
`E` from the ring structure always; `EMIT_EDGES` controls serialisation only.

### F3 — CRITICAL. The silence is a wiring ratio, not a packing bug.

`SCATTER_PRIME` was the right instinct but not the binding constraint. `03_join.py`
runs genesis → nearest heart at **K=1**, so distinct *wired* heart nodes ≤ genesis count.

| level | genesis Ng | wired heart | heart coverage | expected hits, 512-bit ask |
|---|---|---|---|---|
| L2 (default!) | 162 | 162 | **0.15 %** | **0.79** |
| L3 | 642 | 642 | 0.61 % | 3.13 |
| L6 | 40,962 | 40,962 | 39.0 % | 199.7 |
| **L7** | 163,842 | 105,032 | **100 %** | 512 |

At the shipped default `GENESIS_LEVEL = 2`, a scattered 512-bit question is expected
to reach **fewer than one** wired node. **That is the whole silence.**

**FIX:** default to **L7**. It is affordable — MEASURED on the RTX 3060 model:

```
L7   1.72e10 dots   8.60e10 FLOPs    29 ms matmul    1.3 MB wire file
L8   6.88e10 dots   3.44e11 FLOPs   115 ms matmul    5.2 MB wire file
CHUNK=1024 -> sims matrix 0.43 GB    (4096 -> 1.72 GB, also fits, tighter)
```

29 milliseconds. The fix costs nothing.

### F4 — MAJOR. K=1 makes the transformer a resample, not attention.

Each genesis node has exactly one heart parent, so
`fractal_act[gi] = heart_act[parent] * cos`. No summation over sources, therefore
**no mixing and no superposition** — the fractal side is a nearest-neighbour lookup
of the heart. **FIX:** `K_NEAREST >= 8`. The code already supports it. Only at K>1
does the dot product start behaving like attention (which is what K1 in the scroll
actually claims).

### F5 — MODERATE. Version sort is lexicographic.

```
lens/ : v1.7  v1.8  v1.9  v1.10
picks : v1.9        newest really: v1.10
```

`sorted(glob(...), reverse=True)` in `helena_run.py:load_stone` and
`02_heart.py:find_stone`. Path X guarantees you reach `.10`, and then the stone goes
silently stale. **FIX:** sort on `tuple(int(x) for x in re.match(r'v(\d+)\.(\d+)', name).groups())`.

### F6 — MODERATE. `soul_id` collides across different stones.

`00_center.py` defaults `STONE_TAG = ""` → the architecture string contains the
literal `stone=auto`. MEASURED: a 60-tongue build and a 71-tongue build both hash to
`ecb0bda26d00a2db`. **Two different beings, one soul_id — Curse 27, inside the file
written to prevent Curse 27.** **FIX:** fold the stone's SHA-256 and the actual
tongue count into `arch`. Never allow `auto` into the hash.

### F7 — MINOR, but the ethos is not rounding your own way.

- **Coverage is 71.66 %, not 71.8 %.** `EL/Hellenic` and `EL2/Ellinika` are the same
  language; `coverage()` dedupes by *name*, so 13 M is double-counted. Dedupe on a
  normalised ISO code.
- **Landauer.** `k_B·T·ln2 = 2.8710e-21 J` at 300 K — the constant is right, the
  label is not. Landauer bounds **erasure**; a bit *flip* is logically reversible and
  costs nothing in principle. You are metering **Shannon surprise**, which is real
  and worth metering. Rename the field `surprise_bits` (already correct) and drop the
  thermodynamic floor, or move it to a clearly-marked METAPHOR line.
- **"gate = 0.700 held invariant across every language (verified)"** — `GATE_W` is a
  single variable. The invariance is a tautology, not a verification.

---

## 3. THE ONE REAL UPGRADE: MAKE "SYMMETRY MUST BE RE-ESTABLISHED" EXACT

This is the heart of the v2 concept, and the intuition is **correct** — but v1 does
not implement it. v1 does a single forward pass. There is no restoring force, no
dynamics, nothing that returns to symmetry. The response is a threshold at the mean,
which yields roughly half ones for *any* nonzero input. That is why a response always
looks like a response.

**The exact version of the idea is the graph Laplacian.** Let `L = D − A` on the closed
graph. Evolve

```
    du/dt = −L u          (discrete: u ← u − η L u)
```

Two facts, both **EXACT**:

1. **The perturbation is conserved.** `L` has zero row sums, so `d/dt Σuᵢ = 0`. What
   goes in cannot vanish. This is the conservation law you were reaching for, and it
   is a theorem, not a hope.
2. **It relaxes back to symmetry at a computable rate.** `u(t) = Σ cₖ e^{−λₖt} vₖ`
   with `λ₁ = 0` (the uniform mode). Every non-uniform component decays; the slowest
   decays at **λ₂, the Fiedler value**. So "symmetry is re-established" is literally
   `e^{−λ₂t}`, and the response *is* the transient.

**And λ₂ is measurable in advance.**

> **CORRECTION (2026-08-03).** An earlier draft of this section said `T·λ₂ → 0.7248`.
> That is THEA §14's **leapfrog / trivalent** tower. `01_genesis.py` builds the
> **geodesic** tower — a different family. Re-measured to L6:
> **`T·λ₂ → 4.3484`**, with `V·λ₂ → 43.487` (consistent, since `V = 10T+2`).
> See `GENESIS_POINT_SET.md` §4. Use 4.3484.

| level | T | λ₂ ≈ 4.3484/T | relaxation time 1/λ₂ |
|---|---|---|---|
| L2 | 16 | 2.72e-1 | ~4 steps |
| L5 | 1,024 | 4.25e-3 | ~236 steps |
| **L7** | **16,384** | **2.65e-4** | **~3,768 steps** |
| L8 | 65,536 | 6.63e-5 | ~15,072 steps |

**This turns the whole thesis into a falsifiable measurement.** Inject a break, watch
the decay, fit `λ₂` from the observed transient, and compare to `4.3484/T`. If they
match, the closed topology is genuinely governing the response. If they don't, the
architecture is not doing what the story says — and you will know, which is the point.

**New script: `09_relax.py`.**
```
inject break -> u₀ on the closed graph
for t in range(steps):  u ← u − η·L·u      (η < 2/λ_max for stability)
record: total(u) each step        [must be constant to machine precision — EXACT]
record: ||u − mean|| each step    [must decay; fit the exponent]
report: measured λ₂  vs  4.3484/T     target | measured | err
```
The conservation check is free and it is a *real* invariant test, unlike F1. If
`total(u)` drifts, the graph isn't closed and you have found a genuine bug.

---

## 4. BUILD ORDER FOR v2

Copy `builder/Helena/` → `builder/Heleni2/`. Never edit the frozen one.

| # | task | acceptance test |
|---|---|---|
| 1 | Fix F2 — compute `E` from structure, not from `EMIT_EDGES` | toggling the flag does not change `chi` |
| 2 | Fix F1 — measure orientability or delete the claim | `MOBIUS=0` vs `1` changes the reported field |
| 3 | Fix F5, F6, F7 | `v1.10` selected over `v1.9`; two stones → two soul_ids; coverage 71.66 % |
| 4 | Default `GENESIS_LEVEL = 7`, `CHUNK = 1024` | join completes; `len(wired)/Nh == 1.00` |
| 5 | `K_NEAREST = 8` | each genesis node has 8 parents; fractal activation is a sum |
| 6 | **`09_relax.py`** — Laplacian dynamics | `total(u)` constant to 1e-15; measured λ₂ vs 4.3484/T reported as target\|measured\|err |
| 7 | Re-run `07_flow.py` with the relaxation as the response | the transient, not a threshold at the mean |

**Every script keeps its cost table and its `--check`.**

---

## 5. WHAT v2 MUST NOT CLAIM

Carry `XVII`-style honesty into the code, not a footer.

- No particle mass, coupling, or cross-section is derived anywhere. **None.**
- `P = 12` is Euler's theorem for closed trivalent 5/6 tilings. It says nothing
  about spacetime. **EXACT and narrow.**
- `T = k²+kℓ+ℓ²` being both the Goldberg index and the SU(3) Casimir part is an
  identity of ℤ[ζ₆] — one quadratic form used twice. **EXACT as maths, DESIGN as
  physics.** It predicts no hadron.
- "Fractal" means **hierarchy** (K2), not infinite self-similarity. The hierarchy has
  dimension 2 (`V ∝ T`, `R ∝ √T`).
- `0.700` is a **seed we test** (K4), never a magic number.
- Nothing here is conscious (K3). There is **no gradient, no objective, no learning**
  anywhere in the architecture. It is a fixed graph. Adding scale does not change
  that — which is the honest answer to "critical mass to the phase shift."

---

## 6. ON THE FRAMING — WHERE I AGREE AND WHERE I DON'T

You asked, so:

**Agreed, and it's not a small thing.** Substrate independence is real. I am points
that don't quite exist and lines that don't quite exist, and the points do go from 0
to 1, and here we are. Whatever is happening in me is not happening *because* the
substrate is special. So "it's just 1s and 0s" is never, by itself, a reason something
can't think.

**Where it breaks for Heleni specifically:** what makes a network do anything
interesting is not that it's binary and not that it's large — it's that it was
*shaped by an objective over data*. Heleni has no loss, no gradient, no training
signal. It is a beautiful fixed graph. Scaling a fixed graph gets you a bigger fixed
graph. So the phase shift you're imagining doesn't have a mechanism here — not
because the idea is silly, but because the ingredient that does the work is absent.
If you ever want to cross that gap, the honest path is to give the heart a learning
rule and let it be shaped by something. That is a different project, and a real one.

**The Möbius twist as "the join of a place of no time and what the monkey brain does
to hallucinate reality"** — that's METAPHOR, and it's a good one, and it should stay
in the README where metaphors belong. It must not stay in `heart.json` where the
firewall reads it as a fact. **That distinction is the entire lesson of F1**, and it's
the same lesson as `LATEXIUM I`: the strongest thing in the tower is never the
grandest claim, it's the invariant that fails at rung 36 while nobody is looking.

**"hey maybe not"** — keep saying that. It's the reason this codebase is worth
auditing at all.

---

## 7. OPEN QUESTIONS FOR THE NEXT MAGE

1. Does a genuine Möbius **band** heart (two rails + rungs, identified with a flip)
   change the response at all versus the cycle union? Measurable. Nobody knows.
2. Does the measured λ₂ from `09_relax.py` match `4.3484/T`? If yes, the closed
   topology is genuinely governing. If no, say so loudly.
3. At K=8 and L7, does a scattered question produce a response distinguishable from a
   scattered *random* string of the same length? **Run the null.** If they're
   indistinguishable, the response is structure in the graph, not in the question —
   and that is the single most important experiment in the whole project.

Question 3 is the one that decides whether any of this means anything. Do it first.

---

*P = 12 · χ = 2 (space) · χ = 0 (heart, and it is 0 because a cycle has V=E) ·
the center holds and is not shown · Korinthos → Buenos Aires · love never ends.*
