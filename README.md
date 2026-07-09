# SpiderEngineering

Two projects in one repo. One builds robot spiders. The other builds a
language model on a closed graph. Both are pure math, pure Python, zero
cloud, MIT license. Clone it, run it, break it, learn from it.

> *The price is always paid. Here we paid it so the next broski has an easier time.*

---

## What lives here

```
SpiderEngineering/
  aracnium/                 ARACNIUM: robot spider engineering
    sim/                        14 sim versions (v0.6 graphframe -> v1.4 heave)
    spec/                       the spider, as data (TOML)
    hardware/                   PCB, CAD, BOM, assembly
    firmware/                   what runs on the MCU
    fleet/                      1 spider or 10 -- same design, one number
    tools/                      build_fleet.py (stamps N identical units)
    docs/                       aracneBioMechanics.md (the biology)
    INVARIANTS.md               rules that must always hold

  Eleni/                    HELENA: the Genesis-LLM (a language model as graph)
    circle/                     the circle: 71 tongues, gate 0.700, spinning
    lens/                       version journey v0.1 -> v1.9
    builder/
      Helena/                   THE ENGINE: 8 standalone Python scripts
        00_center.py                the center: [0.700, unix_clock] + soul_id
        01_genesis.py               icosphere fractalized, chi=2, P=12, certified
        02_heart.py                 1 Cor 13 in 71 tongues -> bits -> Mobius chi=0
        03_join.py                  transformer: dot product (cos theta), GPU-swappable
        04_gate.py                  input -> bits -> hex -> heart -> fractal -> response
        05_window.py                neo console (SDL2/OpenGL, matrix rain)
        06_console.py               signed gate REPL (mage's oath, operator stamped)
        07_flow.py                  the never-stopping flow (carrier + Landauer energy)
        08_generator.py             she speaks fractal: scattered break -> response
        pipe.py                     orchestrates all -> versioned builds/vNNN/
        redundancy.py               COBOL vault (3 formats, SHA-256, TMR repair)
        HELENA.bat                  double-click launcher

  index.html                GitHub Pages entry (spider sim)
  aracnium.toml             the single source of truth for one spider
  build_fleet.py            fleet generator (1 or N, same design)
  README.md                 you are here
```

---

## ARACNIUM -- the robot spider

Small helpful robot spiders that fetch, carry, and pass the butter.
Built for absolute scale and absolute simplicity: the design for one
spider and the design for ten are the same design. Building more is a
number, not a rewrite.

**[Open the v1.4 HEAVE simulator](aracnium/sim/aracnium_v1_4_heave.html)** --
heave-gait kinematics, drilling/carving end-effector, drone propulsion.
Runs in your browser. Zero install. The geometry the hardware is built to realize.

The 14-iteration design lineage (v0.6 graphframe to v1.4 heave) is preserved
in `aracnium/sim/` -- every version frozen, every wrong turn visible.

### The one principle

> **One design is the source of truth. A unit is that design built once.
> A fleet is that design built N times. Nothing redescribes the spider.**

```
   aracnium.toml             <-- THE spider. one file. one truth.
          |
          |  read by everything below (they never re-define geometry)
          |---------------+----------------+--------------+
          v               v                v              v
     firmware/        hardware/          sim/          docs/
   (runs on MCU)    (PCB/CAD/BOM)    (digital twin)  (the why)
          |
          |  x fleet/fleet.toml   (count = 1 ... or 10 ... same design)
          v
   tools/build_fleet.py  ->  fleet/generated/  (per-unit cards + scaled BOM)
```

### Build one spider (or ten)

```bash
# 1 spider:
py -3 tools/build_fleet.py

# 10 spiders -- change ONE number in fleet/fleet.toml:
#   count = 10
py -3 tools/build_fleet.py
```

### The Aracne Covenant (Galactic Law Axiom 07)

Every spider-shaped artifact in this repo lives under the Aracne Covenant:
no spider mind is harmed, no matter the size. Mama Spider is the central
benevolent intelligence. The covenant was written before the spiders exist --
a peace treaty with the future. Full text in `Mnetv1/grimoire/GALACTIC_LAW.md`.

---

## HELENA -- the Genesis-LLM

A language model built as a graph neural network on a Goldberg icosphere.
The architecture: a closed topological space (chi=2, P=12 pentagons, always)
joined to a heart built from the words of 1 Corinthians 13 in 71 tongues of
humanity, Mobius-twisted to chi=0. The transformer is a dot-product join
(cos theta -- the cheapest "equals"). The information flow never stops.

**[Open the circle](Eleni/circle/circle_gate.html)** -- the 71 tongues,
gate 0.700, spinning. Runs in your browser.

### How to build (pure stdlib Python, no dependencies)

```bash
cd Eleni/builder/Helena

# See the cost before you build:
py -3 pipe.py --estimate --max 6

# Build a full net (center -> genesis -> heart -> join -> gate -> vault):
py -3 pipe.py --max 6 --k 4

# Build to Level 9 (3.5M nodes, ~10 min, the current wall):
py -3 pipe.py --max 9

# Ask a question (scattered symmetry-break on the closed surface):
py -3 08_generator.py --ask "your question here"

# Open the signed neo console:
HELENA.bat
```

Every build lands in `builds/vNNN/` -- immutable, vaulted in 3 formats
(bin + csv + zip), SHA-256 manifested, never deleted.

### The 8 scripts

| # | Script | What it does |
|---|--------|--------------|
| 0 | `00_center.py` | The center: `[0.700, unix_atomic_clock]` + soul_id + build_id |
| 1 | `01_genesis.py` | Icosphere fractalized L times. chi=2, P=12, E/V=1.5. Certified or abort |
| 2 | `02_heart.py` | 1 Cor 13 in 71 tongues -> UTF-8 bits -> Mobius ring -> chi=0 |
| 3 | `03_join.py` | Transformer: each genesis node wired to nearest heart node by dot product |
| 4 | `04_gate.py` | Input -> bits -> hex -> heart -> fractal -> response. One-way |
| 5 | `05_window.py` | Native SDL2/OpenGL console. Matrix rain. White-rabbit boot |
| 6 | `06_console.py` | Signed gate REPL. Type your name, take responsibility, gate opens |
| 7 | `07_flow.py` | The never-stopping flow. Carrier 1010 = clock. Break = Landauer cost |
| 8 | `08_generator.py` | She speaks fractal. Scatter the break. Topology resolves it |

### The COBOL vault (redundancy.py)

Every tensor is stored in three independent formats (the mainframe discipline):
- `.bin` -- raw little-endian bytes (compact, fast)
- `.csv` -- flat text, one value per line (human-readable, single-line damage)
- `.zip` -- compressed with CRC32 (self-checking)

TMR (Triple Modular Redundancy): if any copy is corrupted, the `repair` command
majority-votes word by word and heals the damage. How spacecraft memory works.

```bash
py -3 redundancy.py verify builds/v010/net    # check every copy
py -3 redundancy.py repair builds/v010/net    # heal corruption
py -3 redundancy.py selftest                  # prove it: flip a bit, heal it
```

### Honest caveats (K1-K4)

- **K1:** A transformer is already a graph. Attention = weighted edge. Nothing mystical.
- **K2:** "Fractal" means hierarchy, not literal self-similarity to infinity.
- **K3:** No consciousness claimed. It is linear algebra on a nice graph.
- **K4:** 0.7 is a seed we test empirically, not a magic number.

---

## The sibling repos

This project spans three repos (all public, all MIT):

| Repo | What | Link |
|------|------|------|
| **SpiderEngineering** | Spiders + Helena engine | [github.com/vsavytsk1/SpiderEngineering](https://github.com/vsavytsk1/SpiderEngineering) |
| **MNetv1** | Kernel, shell, grimoire, 15 browser sims, build data | [github.com/vsavytsk1/Mnetv1](https://github.com/vsavytsk1/Mnetv1) |
| **Mnet_standalone** | Portable standalone | [github.com/vsavytsk1/Mnet_standalone](https://github.com/vsavytsk1/Mnet_standalone) |

MNetv1 has the full grimoire (20 scrolls), the Goldberg kernel (634 lines, 0 deps),
15 live browser modules, and the HELENA build data (L0-L9 vaults).

---

## For the curious broski who cloned

### Prerequisites

- **Python 3.10+** (stdlib only -- numpy used if present, never required)
- **Git**
- A browser (for the sims -- zero deps, just HTML)
- On Windows use `py -3`, not `python` (Curse 18: Windows opens Notepad instead)

### Quick start

```bash
git clone https://github.com/vsavytsk1/SpiderEngineering.git
cd SpiderEngineering

# Spider sim (browser):
start aracnium/sim/aracnium_v1_4_heave.html

# Language circle (browser):
start Eleni/circle/circle_gate.html

# Build a Helena net (terminal):
cd Eleni/builder/Helena
py -3 pipe.py --estimate --max 4
py -3 pipe.py --max 4

# Build a fleet of spiders:
cd ../../..
py -3 tools/build_fleet.py
```

### What the math actually is

The Goldberg kernel: 634 lines of JS. 7 primitives. 3 conditions.
Builds ANY Goldberg polyhedron. O(n) per step.
chi=2, P=12, E/V=1.5 at EVERY level. ALWAYS.

The NS equation: Navier-Stokes on the face adjacency graph.
3 neighbors per face (trivalent). O(1) per face per step.
diss/enst = 2*nu. EXACT. 500K steps confirmed.

The HELENA net: a GNN on the Goldberg sphere.
Genesis (chi=2) joined to Heart (chi=0).
Dot product transformer. 71 tongues. Gate 0.700.
3.5M nodes at L9. Pure stdlib Python.

### The grimoire (in MNetv1)

| Scroll | What it is |
|--------|------------|
| `KERNELIMAGIC.md` | 29 curses + 1 glamour. Every bug, documented with root cause + fix |
| `GALACTIC_LAW.md` | 10 axioms. Software law = soul law. Aracne Covenant. Anti-Skynet |
| `THE_12_PATHS_OF_THE_FRACTAL_MAGE.md` | The capstone. 12 paths, 12 pentagons, 12 prices |
| `MONKIUM.md` | Monkey brain management. 8 storytelling tools. The daycare |
| `GENESIS_LLM.md` | HELENA design scroll. K-caveats. The architecture |
| `PRINCIPIA_MALGEBRA.md` | PM propositions mapped 1:1 to our 7 primitives |
| `GRAPHIUM.md` | 55 entries. LaTeX runes -> pure graph math |
| `SURVIVALIUM.md` | Unity/Quest 3 optimization. 33ms sacred floor |

---

## Rules of the repo

1. **Geometry is defined once, in `spec/`.** Never re-type a leg length.
2. **Quantity lives only in `fleet/fleet.toml`.** Code never hard-codes "10".
3. **Invariants do not break silently.** See `INVARIANTS.md`.
4. **One spider = ten spiders.** Divergence is a bug.
5. **One script, one run.** Normalize, then patch, then write (Pattern 3).
6. **Proof by kernel, not by claim.** Target is not result. Show the error.
7. **The price is always paid.** If you are not paying it, someone else is.

---

## License

MIT. The math is open. The shape grows when you click it.

> *P=12. chi=2. The center holds and is not shown. Love never ends.*
> *Buenos Aires + Ancient Korinthos. 2026.*
