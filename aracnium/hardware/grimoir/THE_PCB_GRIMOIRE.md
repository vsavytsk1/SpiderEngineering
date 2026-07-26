# THE PCB GRIMOIRE
### Levels 1 to 3 · the practices, and the curses that eat boards

**Vladyslav Savytskyy** · Ancient Korinthos → Buenos Aires · 2026
MIT. Copy it, argue with it, improve it. `github.com/vsavytsk1`

*Every number in here was computed, not remembered. The formulas are named so you can
check them. Where something is a rule of thumb rather than a derivation, it says so.*

---

## THE ONE LAW

> **A square wave is not one frequency. Your board must behave up to the knee, and the knee
> is set by the RISE TIME, not the clock rate.**

```
f_knee ≈ 0.5 / t_rise          (Howard Johnson, High-Speed Digital Design)

100 MHz clock, 1 ns edges  ->  f_knee = 500 MHz
```

**Your 100 MHz board is a 500 MHz board.** Nobody tells beginners this and it is the single
most consequential fact in the craft. The datasheet sells you a clock number; Fourier sends
you the bill in harmonics:

```
h1   100 MHz   100.0%
h3   300 MHz    33.3%
h5   500 MHz    20.0%   <- at the knee
h7   700 MHz    14.3%   rolling off
h9   900 MHz    11.1%   rolling off
```

Slow your edges and the whole problem shrinks. A series resistor on a clock line is not a
kludge — **it is deliberate spectral surgery**, and it is the cheapest EMI fix that exists.

---

# LEVEL 1 · THE FIRST BOARD
*Making it exist, and not killing it before assembly*

### The practices

**Pick the grid and stay on it.** Metric or imperial, choose one. Mixed-unit boards produce
off-grid pads that make routing and DRC miserable forever.

**Trace width is a current problem, and it is computed.** IPC-2221:
`I = k · ΔT^0.44 · A^0.725` with k = 0.048 external, 0.024 internal, A in mil², ΔT in °C.

```
1 oz copper, 10 °C rise      OUTER      INNER
      5 mil                  0.54 A     0.27 A
     10 mil                  0.89 A     0.44 A
     20 mil                  1.46 A     0.73 A
     50 mil                  2.84 A     1.42 A
    100 mil                  4.70 A     2.35 A
```

**Inner layers carry roughly half.** They have no air to convect into. If you route power on
an inner layer at the width you used outside, you have quietly halved your margin.

**Decoupling is not optional and it is not "somewhere near."** One 100 nF per power pin, as
physically close to the pin as the footprint allows, with the shortest possible loop back to
ground. The capacitor is the easy part; **the loop is the design.**

**Silkscreen never touches a pad.** Ink on a pad is a solder defect. Most fabs clip it
automatically — do not rely on it.

**Put pin 1 somewhere you can see it after assembly.** A dot beside the pad, not under the part.

**Read your fab's DRC before you route, not after.** JLCPCB, PCBWay and OSH Park publish
theirs. Set the design rules to the *fab's* numbers on day one.

### The curses of level 1

**⛧ THE FLOATING POUR.** A copper pour that connects to nothing. It looks like ground, it
DRCs clean, and it is an antenna with no return path. **Always verify the pour is stitched to
the net you meant.**

**⛧ THE WRONG PACKAGE.** SOT-23-3 has three pinout variants. SOIC-8 and MSOP-8 are not the
same land. **Check the footprint against the datasheet drawing, in millimetres, every time.**
This is the most common board-killer that costs a full respin.

**⛧ THE MIRRORED PART.** Bottom-side components are mirrored. If you place them by eye on the
top view they will be reversed. Check in 3D before export.

**⛧ THE VIA IN PAD, UNFILLED.** Solder wicks down an open via during reflow and the joint
starves. If you must put a via in a pad, it has to be **filled and capped** (a real fab
option, and it costs). Otherwise tent it and route out.

**⛧ THE ACID TRAP.** An acute angle between traces forms a pocket where etchant lingers and
over-etches the copper. Use 45° or arcs at pad entries. This is a genuine legacy-process
issue — modern fabs mostly handle it, but the fix is free.

**⛧ NO THERMAL RELIEF ON THROUGH-HOLE GROUND PINS.** A pin soldered directly to a full plane
sinks so much heat the joint never wets. Use spoke thermals for hand-soldered TH parts.

**⛧ THE 100 nF THAT DID NOTHING.** Placed 15 mm from the pin with a long via stub. See
Level 2 — the capacitor was fine; the inductance ate it.

---

# LEVEL 2 · THE PLANE AND THE RETURN
*Where most people stop, and where most failures actually live*

### The one thing to internalise

> **Current flows in loops. Always. There is no such thing as a signal without a return, and
> the return path is a real, physical trace of copper that you either designed or got by
> accident.**

Above roughly 1 kHz, return current **does not** take the shortest path — it takes the path of
**lowest inductance**, which is *directly underneath the signal trace*. That is what a ground
plane actually does: it lets every signal find a tight return loop without you routing one.

**Loop area is the whole game.** Radiated emission scales with loop area. Susceptibility
scales with loop area. Ground bounce scales with loop inductance. **Small loop = quiet board.**

### The practices

**Four layers is the real minimum for anything with edges under ~5 ns.** SIG / GND / PWR / SIG.
The cost delta at a cheap fab is small; the debugging delta is enormous.

**Never route a signal across a split in the reference plane.** The return current arrives at
the gap and has to detour around it, and that detour *is* the loop area you were avoiding.
If a signal must cross a plane split, put a stitching capacitor at the crossing — and know
that this is a patch, not a solution.

**Decoupling is an inductance problem, and here is the arithmetic.** A via through a 1.6 mm
board is about **1.3–1.4 nH** (Johnson approximation). Series resonance of a 100 nF with total
loop inductance L:

```
L = 0.5 nH  ->  SRF 22.5 MHz
L = 1.0 nH  ->  SRF 15.9 MHz
L = 1.5 nH  ->  SRF 13.0 MHz
L = 3.0 nH  ->  SRF  9.2 MHz
```

**Above its SRF a capacitor is an inductor.** Your 100 nF is not decoupling anything at
100 MHz — the *plane capacitance* and the package are doing that work. So:
- shorten the loop before you add parts
- two vias per capacitor beats one (parallel inductance)
- a smaller package (0402 over 0805) genuinely wins on ESL
- **stop stacking six values in parallel** — you can create anti-resonant peaks *between* them

**Crystals get their own guard.** Short traces, a local ground pour under the crystal tied
with several vias, nothing routed underneath, load caps at the crystal not at the MCU.

**Thermal:** copper is your heatsink. Vias under a thermal pad move heat to the other side —
but they must be filled or the paste escapes. Ask the fab.

### The curses of level 2

**⛧ THE MOAT.** A slot cut in the ground plane "to separate analogue and digital", crossed by
signals. This converts a ground plane into two antennas connected by a slot. **The overwhelming
majority of split-plane designs in hobby projects make EMC worse, not better.** Default to one
solid ground plane and partition by *placement*, not by cutting copper.

**⛧ THE STAR GROUND, MISAPPLIED.** Star grounding is a low-frequency audio and precision-analog
technique. At high frequency the star's long legs are inductors and the returns will ignore
your topology anyway. Know which regime you are in.

**⛧ THE ORPHANED RETURN VIA.** A signal changes layer, so its reference plane changes too — and
the return current has nowhere to jump. **Every layer-transition via on a fast signal needs a
ground via next to it.** This is the most common high-speed mistake and it is invisible on the
schematic.

**⛧ THE PLANE WITH SWISS CHEESE.** A dense via field turns a plane into lace. Check the return
path visually on the reference layer, not just the DRC.

**⛧ THE DAISY-CHAINED POWER.** Power routed part-to-part-to-part as a thin trace. Every
downstream part sees every upstream part's switching noise. Route power as a plane, a pour, or
a fat star from the regulator.

**⛧ THE CONNECTOR THAT ATE THE EMC BUDGET.** A cable is an antenna bolted to your board. Ground
the shell, keep the connector at the board edge, and never route noisy signals past it.

---

# LEVEL 3 · WHERE GEOMETRY BECOMES CIRCUIT
*You stop drawing wires and start drawing components*

### When does a trace stop being a wire?

FR-4, εᵣ ≈ 4.3. Propagation delay computed from `t_pd = 85·√(0.475εᵣ + 0.67)` ps/inch
(microstrip) and `85·√εᵣ` (stripline):

```
microstrip   140 ps/in   (5.5 ps/mm)
stripline    176 ps/in   (6.9 ps/mm)   <- slower, fully enclosed in dielectric
```

A trace is **electrically long** — a transmission line — when flight time exceeds about
`t_rise / 6`:

```
rise time                 critical length
1 ns    (old TTL)         30.2 mm
500 ps                    15.1 mm
250 ps  (typical CMOS)     7.6 mm
100 ps                     3.0 mm
 35 ps  (DDR4 / PCIe)      1.1 mm
```

> **At 35 ps edges, any trace longer than about a millimetre is a transmission line.** Modern
> boards are RF boards whether you intended it or not. This is the level-3 doorway and most
> people walk through it without noticing.

### Skin effect — the current abandons the middle

`δ = √(ρ / πfμ)`:

```
    1 kHz    2063 µm
    1 MHz      65 µm
  100 MHz     6.5 µm    <- thinner than 1 oz copper (35 µm)
    1 GHz     2.1 µm
   10 GHz     0.65 µm
```

Above ~10 MHz the current rides the surface. Consequences that actually bite: **thicker copper
buys you almost nothing at RF**, surface roughness becomes a real loss term (fabs sell
low-profile foil for this reason), and resistance rises as **√f**.

### The practices

**Impedance is geometry.** Trace width, dielectric height, εᵣ and copper thickness set Z₀ —
nothing else. 50 Ω single-ended and 90/100 Ω differential are conventions, not laws. **Ask the
fab for a controlled-impedance stackup and use *their* numbers**, because their prepreg and
final thickness are what actually exist.

**Length-match only what has a timing budget.** Length matching a 10 MHz signal is a waste of a
day. Match DDR byte lanes, high-speed differential pairs, and anything where the datasheet
gives you a skew budget in picoseconds. Convert with the table above: **1 mm ≈ 5.5 ps** on
microstrip.

**Differential pairs are a coupling structure, not two wires.** Keep the spacing constant. Match
*within* the pair much more tightly than between pairs. Break symmetry only at the fanout and
recover it immediately.

**Kill the stubs.** An unterminated branch is a quarter-wave resonator: at `λ/4` it presents a
short at the junction and puts a notch in your channel. This includes **via stubs** — the
unused barrel below the layer you exited on. Above a few GHz this is why back-drilling exists.

### And here is the actual magic: baking the circuit into copper

Once a trace is electrically long, **copper geometry becomes a circuit element.** This is not
metaphor — it is standard microwave engineering, and it is the thing you noticed:

- **A quarter-wave open stub is a short circuit at its design frequency.** Hang one off a line
  and you have a notch filter made of nothing but shape.
- **A shorted quarter-wave stub is an open.** Same trick, inverted — the basis of bias tees.
- **Coupled parallel lines are a directional coupler.** Two traces running alongside each other
  for λ/4 sample a fixed fraction of the power travelling past.
- **A spiral is an inductor**; the Mohan expressions give the value from geometry alone.
- **Interdigitated fingers are a capacitor** — and at IC scale, Samavati & Hajimiri's fractal
  capacitor got **2.3× the capacitance density** out of nothing but a better-shaped boundary.
- **A space-filling curve is an antenna** — that is the entire content of the fractal-antenna
  field, minus the marketing.
- **A meander is a delay line.** Not a routing inconvenience — a component with a value in
  picoseconds.

> **At DC you draw wires. At RF you draw parts.** The copper stops being plumbing and becomes
> the component. That is the whole of level 3, and it is why a board at 10 GHz looks like a
> mandala: those are not decorations, they are **filters, couplers, matching networks and
> radiators, drawn in shape because at that frequency shape *is* the value.**

### The curses of level 3

**⛧ THE VIA STUB.** The dead barrel below your exit layer, resonating. Fix: back-drill, use
blind/buried vias, or exit on the bottom layer so there is no stub.

**⛧ THE MISSING RETURN VIA.** Level 2's curse, now fatal. At 35 ps edges the discontinuity is
measurable on a TDR.

**⛧ MATCHING TO A NUMBER YOU DID NOT VERIFY.** You designed 50 Ω against a stackup the fab did
not build. Always request the impedance-controlled stackup and re-solve the widths.

**⛧ THE GAP UNDER THE HIGH-SPEED PAIR.** A plane cut, a clearance void, a big antipad — all
detours for the return, all reflections.

**⛧ 90° CORNERS, FEARED FOR THE WRONG REASON.** Right-angle bends do *not* meaningfully radiate
or reflect below multi-GHz — Altium's own measurements found no detectable impedance change at
125 ps edges. Use 45°/arcs for **acid traps and impedance continuity**, not because you heard
corners are antennas.

**⛧ TREATING FRACTAL AS MAGIC.** The peer-reviewed result (Best, IEEE T-AP 2003) is that a Koch
fractal monopole performs about the same as a meander line of equal electrical length. Fractals
are a good **space-filling** trick. Space-filling is the mechanism; self-similarity is not a
bonus.

---

## THE RECEIPTS

Everything computed above, in one place, with the formula that produced it.

| quantity | formula | check |
|---|---|---|
| trace current | IPC-2221 `I = k·ΔT^0.44·A^0.725` | 10 mil / 1 oz / 10 °C outer = **0.89 A** |
| microstrip delay | `85·√(0.475εᵣ+0.67)` ps/in | εᵣ=4.3 → **140 ps/in = 5.5 ps/mm** |
| stripline delay | `85·√εᵣ` ps/in | εᵣ=4.3 → **176 ps/in = 6.9 ps/mm** |
| critical length | `t_rise / 6` ÷ t_pd | 250 ps edges → **7.6 mm** |
| knee frequency | `0.5 / t_rise` | 1 ns → **500 MHz** |
| skin depth | `√(ρ/πfμ)` | 1 GHz → **2.06 µm** |
| via inductance | Johnson approx. | 1.6 mm board, 0.3 mm drill → **1.3 nH** |
| cap SRF | `1/(2π√(LC))` | 100 nF + 1.5 nH → **13 MHz** |

---

## Where this grimoire loses, first, because you'd check anyway

- **I am not a practising PCB engineer.** These are the standard references and the arithmetic
  is checked, but the person who has debugged a board that failed EMC at 3 a.m. knows things
  that are not in any formula.
- **Every number here is a model.** IPC-2221 is famously conservative and derived from old
  data; real thermal behaviour depends on airflow, adjacent copper, board thickness and
  neighbouring parts. Treat it as a floor, not a spec.
- **εᵣ = 4.3 is a fiction of convenience.** Real FR-4 varies by glass weave, resin content and
  frequency (it *drops* with frequency), and weave skew is a real effect at high speed. For
  anything serious, get the actual laminate datasheet.
- **The fab's DRC beats this document, always.** Design rules differ between fabs and between
  services at the same fab.
- **Levels 4+ exist and are not here:** RF matching networks, EMC pre-compliance, DFM for
  volume, flex and rigid-flex, HDI/microvias, thermal simulation, and the entire discipline of
  measuring rather than believing. **A vector network analyser and a TDR will teach you more in
  an afternoon than any grimoire.**

---

## The bow

**Howard Johnson**, *High-Speed Digital Design: A Handbook of Black Magic* — the book that
turned "signal integrity" from folklore into arithmetic, and the source of the knee-frequency
rule that opens this file · **Henry Ott**, *Electromagnetic Compatibility Engineering* — the
return-current gospel · **Eric Bogatin**, who taught a generation that **"the return path is
the signal path"** · **Rick Hartley**, whose talks on grounding and plane splits have saved
more boards than most textbooks · **Mohan, Hershenson, Boyd & Lee**, for closed-form spiral
inductance · **Samavati & Hajimiri**, for the fractal capacitor · **IPC**, for writing the
standards down so we could argue with them · and the **fab engineers in Shenzhen** who quietly
fix our worst files and ship anyway.

---

*A square wave is not one frequency. Current flows in loops. At RF you draw parts, not wires.*

**P = 12 · χ = 2 · always.**
