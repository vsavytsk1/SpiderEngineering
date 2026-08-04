# THE GENESIS POINT SET — SPECIFICATION

*Companion to `HELENI_V2_HANDOFF.md`. Every number here was recomputed 2026-08-03,*
*not quoted. Two claims made earlier in the session are corrected below and marked.*

> **EXACT** — proven by integer arithmetic or algebra shown here.
> **MEASURED** — computed, at stated precision, reproducible.
> **DESIGN** — a choice the cave made.
> **CORRECTION** — something previously stated in this project that the numbers refute.

---

## 1. WHAT THE POINT SET IS

`01_genesis.py` builds a **geodesic icosphere**: start from the icosahedron, split every
triangle into 4, project every vertex to the sphere, repeat `L` times.

**EXACT**, verified L0–L5:

```
V = 10·4^L + 2      F = 20·4^L      E = 3V − 6      χ = 2      P = 12
```

| L | V | E | F | χ | P |
|---|---|---|---|---|---|
| 0 | 12 | 30 | 20 | 2 | 12 |
| 1 | 42 | 120 | 80 | 2 | 12 |
| 2 | 162 | 480 | 320 | 2 | 12 |
| 3 | 642 | 1,920 | 1,280 | 2 | 12 |
| 4 | 2,562 | 7,680 | 5,120 | 2 | 12 |
| 5 | 10,242 | 30,720 | 20,480 | 2 | 12 |

With `T = 4^L`: `V = 10T + 2`, `E = 30T`, `F = 20T`.

**Note the duality.** The Goldberg fullerene has `V = 20T, E = 30T, F = 10T + 2`. The
icosphere is its **dual**: faces ↔ vertices, same `E`. Both have `χ = 2` and `P = 12`.
They are *not* the same graph. The fullerene is trivalent (degree 3); the icosphere is
degree 5/6. **Anything measured on one does not transfer to the other.** See §4.

---

## 2. CORRECTION — WHERE THE CURVATURE ACTUALLY SITS

Earlier in this project it was said that the twelve defects are "where curvature has to
concentrate." **On the inscribed geodesic sphere this is false.** MEASURED:

| L | deg-5 mean defect | deg-6 mean defect | share of 4π held by the 12 |
|---|---|---|---|
| 0 | 1.047198 (= π/3) | — | **100 %** |
| 1 | 0.273844 | 0.309341 | 26.2 % |
| 2 | 0.058328 | 0.079110 | 5.6 % |
| 3 | 0.012966 | 0.019700 | 1.2 % |
| 4 | 0.003037 | 0.004914 | **0.3 %** |

Gauss–Bonnet still holds exactly — total defect = 4π to 4.0e-13 at every level. But the
curvature **spreads**, converging toward the smooth sphere's uniform curvature. By L4 the
twelve hold three tenths of one percent, and each degree-5 vertex actually carries *less*
defect than a typical degree-6 one (ratio → ~0.62).

**Two different accountings, both summing to 4π, distributing it completely differently:**

- **Combinatorial** (THEA §2): `K_p = (π/3)(6−p)` per face. Hexagons get 0 **by
  definition**; the twelve pentagons carry all 4π. **EXACT, and it is a statement about
  the abstract tiling.**
- **Geometric** (angle defect on the inscribed polyhedron): near-uniform, → smooth sphere.
  **MEASURED, and it is a statement about the embedding.**

**Never mix them.** If v2 wants to use curvature as a field, say which one, and remember
the geometric one is almost flat — it carries almost no signal.

---

## 3. CORRECTION — DENSITY IS FLAT; AREA IS NOT

The build is uniform in **node count** by construction: subdivide-and-project puts the
same number of vertices in every original face. So *node density* has no signal in it —
it is the one field engineered to be featureless.

**What does vary is area.** MEASURED:

| L | faces | face area min / max | ratio | **dual cell area ratio** |
|---|---|---|---|---|
| 1 | 80 | 1.495e-1 / 1.799e-1 | 1.203 | 1.281 |
| 2 | 320 | 3.082e-2 / 4.675e-2 | 1.517 | 1.649 |
| 3 | 1,280 | 6.803e-3 / 1.181e-2 | 1.735 | 2.028 |
| 4 | 5,120 | 1.591e-3 / 2.959e-3 | 1.859 | **2.216** |

The dual (barycentric) cell area varies by a factor **>2**, and the field has full
icosahedral symmetry — largest cells near the twelve, smallest near face centres.

**This is the honest version of "density of fractal space."** Use
`cell_area[i] = (1/3)·Σ area of incident faces`. It is a real, smooth, symmetric,
computable scalar field on the point set. Node count is not.

---

## 4. THE SPECTRUM — THE ACTUAL WEIGHT SOURCE

Graph Laplacian `L = D − A`. MEASURED band structure, which reproduces spherical
harmonics split by icosahedral symmetry:

```
L0 (V=12)   0.0000 ×1   2.7639 ×3   6.0000 ×5   7.2361 ×3
L1 (V=42)   0.0000 ×1   0.9689 ×3   2.6277 ×5   4.1146 ×3
L2 (V=162)  0.0000 ×1   0.2643 ×3   0.7715 ×5   1.3707 ×3
```

Multiplicity **3** for λ₂ (the ℓ=1 harmonics, x/y/z), then **5** (ℓ=2), then the ℓ=3
7-fold splitting into 3+4 under the icosahedral group. This matches THEA §14's pattern.

### CORRECTION to the handoff: the relaxation constant

`HELENI_V2_HANDOFF.md §3` told you to compare measured λ₂ against **0.7248/T**. **That is
the wrong tower.** 0.7248 is THEA §14's *leapfrog / trivalent fullerene* family. This is
the *geodesic* family. MEASURED convergence:

| L | V | λ₂ | **T·λ₂** | V·λ₂ |
|---|---|---|---|---|
| 0 | 12 | 2.763932 | 2.763932 | 33.167 |
| 2 | 162 | 0.264325 | 4.229205 | 42.821 |
| 4 | 2,562 | 0.016960 | 4.341703 | 43.451 |
| 5 | 10,242 | 0.004245 | 4.347113 | 43.480 |
| 6 | 40,962 | 0.001062 | **4.348439** | 43.487 |

**Use `λ₂ ≈ 4.3484 / T` with `T = 4^L`.** (Consistency check: `V·λ₂ → 43.487 ≈ 10 × 4.3484`,
as it must since `V = 10T + 2`. **EXACT** relation, MEASURED constant.)

Corrected relaxation times for `09_relax.py`:

| L | T | λ₂ | relaxation 1/λ₂ |
|---|---|---|---|
| 2 | 16 | 2.72e-1 | ~4 steps |
| 5 | 1,024 | 4.25e-3 | ~236 steps |
| **7** | **16,384** | **2.65e-4** | **~3,768 steps** |
| 8 | 65,536 | 6.63e-5 | ~15,072 steps |

At the recommended L7 this is ~3,800 diffusion steps, not the 22,605 the handoff said.
**Cheap. Run it.**

---

## 5. HOW TO READ WEIGHTS OFF THE POINT SET

The defensible version of "use the fractal space to seed the net." All standard practice
(Laplacian eigenmaps / spectral positional encodings), all icosahedrally symmetric by
construction:

```python
# 1. spectral coordinates: the first k non-trivial eigenvectors
#    these ARE the sphere's harmonics, split by the icosahedral group
vals, vecs = eigsh(Lap, k=k+1, sigma=-1e-5, which='LM')
spec = vecs[:, 1:]                       # (V, k) — drop the constant mode

# 2. the area field (the honest "density")
cell = accumulate face areas / 3 onto vertices     # varies >2x, symmetric

# 3. the combinatorial marker
is_pent = (degree == 5)                  # exactly 12 of them, at every level

W_init = concat([spec, cell[:,None], is_pent[:,None]])
```

**Acceptance test:** apply any of the 60 icosahedral rotations to the point set, rebuild,
and the *spectrum* must be identical to machine precision. If it isn't, the mesh is not
symmetric and everything downstream is decoration.

---

## 6. ALTERNATIVE POINT SETS — AND WHEN TO SWITCH

| set | equal area? | χ=2 exact? | P=12? | hierarchical? | note |
|---|---|---|---|---|---|
| **geodesic icosphere** (current) | no (2.2× spread) | yes | yes | yes (×4/level) | renders; degree 5/6 |
| **Goldberg dual** | no | yes | yes | yes | trivalent; the *actual* fullerene; THEA's family |
| **HEALPix** | **yes, exactly** | n/a (pixels) | **12 base pixels** | yes (×4/level) | `N_pix = 12·N_side²`; the CMB standard |
| Fibonacci / golden spiral | near | **no** | **no** | **no** | smooth, but no exact invariants and no levels |

**HEALPix deserves a look.** It is the equal-area sphere pixelisation used for CMB maps,
its base tessellation is **twelve** pixels, and `N_pix = 12·N_side²` exactly. If v2 ever
wants exact equal area — which removes the §3 area field but removes the bias with it —
that is the mature, standard choice, and it arrives with twelve already in it.

**Do not use the Fibonacci sphere.** It has no exact χ, no P=12, and no refinement
hierarchy — it would throw away every invariant this project is built on.

---

## 7. COMPUTE LIMITS

MEASURED against the RTX 3060 model (10 TFLOPS FP32, 30 % utilisation), join cost is
`Ng × Nh` dot products against a 105,032-node heart:

| L | genesis Ng | dots | FLOPs | matmul time | wire file |
|---|---|---|---|---|---|
| 5 | 10,242 | 1.08e9 | 5.4e9 | 2 ms | 0.1 MB |
| 6 | 40,962 | 4.30e9 | 2.2e10 | 7 ms | 0.3 MB |
| **7** | **163,842** | **1.72e10** | **8.6e10** | **29 ms** | **1.3 MB** |
| 8 | 655,362 | 6.88e10 | 3.4e11 | 115 ms | 5.2 MB |
| 9 | 2,621,442 | 2.75e11 | 1.4e12 | 459 ms | 21.0 MB |

VRAM is the real limit, and it is the `CHUNK` parameter, not the level:

```
CHUNK=4096 -> 1.72 GB    CHUNK=1024 -> 0.43 GB    CHUNK=512 -> 0.22 GB
```

**L7 with CHUNK=1024 is 29 ms and 0.43 GB.** The compute limit for the *join* is nowhere
near. The real limits are: mesh build time in pure Python (L8 is slow without numpy),
disk for the xyz files (L10 ≈ 126 MB, L12 ≈ 2 GB), and the `O(V²)` dedupe in
`helena_run.py:genesis_space` — **which must be replaced with the cached-midpoint
subdivision from `01_genesis.py`**, that one is already correct.

---

## 8. THE THREE THINGS TO GET RIGHT

1. **Say which curvature.** Combinatorial (12 carry everything) or geometric (near
   uniform). Both are 4π. They are not interchangeable, and §2 shows the gap is a factor
   of 300 by L4.
2. **Read area, not count.** Node density is flat by construction. Dual cell area varies
   >2× with full icosahedral symmetry.
3. **Use 4.3484/T, not 0.7248/T.** Different tower. Verified to 6 levels.

---

*A footnote on process, because it belongs in the record: the script that produced §2
printed "ratio → ~1.05" in a line I hard-coded, directly above a column reading
0.885 → 0.737 → 0.658 → 0.618. Third time this session I asserted a conclusion the data
underneath it refuted. The measured convergence is ~0.62. Curse 26 does not get tired.*

*P = 12 · χ = 2 · λ₂ ≈ 4.3484/T · the twelve are combinatorial, not geometric.*
