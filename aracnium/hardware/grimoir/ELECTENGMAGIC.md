# ELECTENG MAGIC
### The shop-floor grimoire · Level 4 · the 3 a.m. tier the formulas don't hold

*The scroll THE_PCB_GRIMOIRE said existed and did not contain: "the person who has
debugged a board that failed EMC at 3 a.m. knows things that are not in any formula."*

**Contributed to the cave by Claude (Opus 4.8), 2026. MIT.**
*Provenance, honestly (Path IV): I am a model, not a bench engineer. Every claim below
is either a named mechanism you can check or a receipt from a real source, cited inline.
Where it is shop-lore rather than a derivation, it says so. Argue with it. Measure it.*

---

## THE FOLK LAW

> **The vendor already solved your layout. The datasheet's layout section is the real
> datasheet. Copy the reference; know which parts are load-bearing and which you may move.**

This is the whole of the empirical tier in one line. THE_PCB_GRIMOIRE gave you the physics
(the knee, the return path, the loop). The folk layer is: *someone already paid the price
of applying that physics to this exact chip, and published the receipt.* The application
note and the evaluation-board gerbers are that receipt. Emerald Technologies says it plainly
— follow the recommended layout precisely and "the resulting layout performs as well as the
manufacturer intends" (emeraldtechnologies.com). Analog Devices notes that **every** one of
their power eval boards is laid out to the same guideline (AN-1119). The 10-year assembly guy
running on "vibes" is running a compressed index of a thousand such receipts. This scroll
tries to decompress a few of them.

The catch, and why it is a craft and not a copy-paste: **you will almost never be able to
copy the reference exactly** — your parts differ in size, your board is a different shape,
your ground is shared. So you must know *which* part of the reference is the magic. For a
switcher, it is always the hot loop (Curse of the Hot Loop, below). For everything else,
the rule is the same: find the part of the reference the vendor bled for, keep that, move
the rest.

---

# TIER 1 · POWER — WHERE THE CURRENT ACTUALLY SLAMS

*Your spider is a power-electronics machine that happens to walk. Legs are motors, motors
are switched current, switched current is `di/dt`, and `di/dt` in a loop is a voltage spike
looking for something to kill. This tier is most of your field failures.*

### ⛧ THE HOT LOOP — the one thing that decides whether a switcher is quiet or cursed

In a switching regulator (and a motor half-bridge is a switching regulator that drives a
coil), the single most consequential rule is: **the trace carrying the *switched* current —
the loop that goes full-on then full-off with the FET — must be as short and tight as
physically possible.** Analog Devices calls this the golden rule of SMPS layout: route the
high-switched-current paths as short as possible (analog.com). Everything else is secondary.

The reason it is a *curse* and not just a rule: the hot loop is invisible on the schematic.
The schematic shows a capacitor near an IC; it does not show that the input cap, the top FET,
and the bottom FET form a loop whose *area* is a parasitic inductance, and that this
inductance rings every switching edge into an overshoot that stresses the FET and radiates.

**The folk technique that actually works** (ipcb.com, and every grey-haired power engineer):
print the layout on paper, lay a transparency over it, and with two different-colored pens
draw the current path during the ON state and during the OFF state. The *difference* between
those two drawings — the copper where current appears and disappears — is the hot loop. You
cannot reliably do this in your head; you will miss one. Drawing it on paper finds the ring.

- **The input cap belongs on the VIN/GND pins, not "near" them.** The hot loop for a buck is
  input-cap → top-FET → bottom-FET → back to input-cap. Shrink *that* triangle first.
- **The ground plane must carry no AC.** It is a voltage reference, not a highway. Keep the
  switched return in the tight loop, off the quiet plane (ipcb.com).
- **The exception that inverts the rule:** normally you keep vias out of the AC path (via
  inductance). But if avoiding a via forces a *longer* detour, the detour's trace inductance
  beats the via's — so use the via. The rule has a hinge; know which side you are on (ipcb.com).

*Genuine, not cargo-cult.* This is the highest-value single practice in the whole scroll.

### ⛧ THE LEAD IS AN INDUCTOR — the drone-power curse that eats ESCs

You are building from drone parts, so inherit the drone world's most-paid-for lesson. **Long
battery leads are a series inductance.** When the ESC slams current on and off, `V = L·di/dt`
makes the voltage *at the ESC input* spike well above the pack voltage. The peak "can be
significantly higher than the battery source voltage," and the first thing it kills is
usually the input capacitor, then the FETs (DroneVibes; ArduPilot Rover docs literally call
it "water hammer in the house pipes").

The fixes are pure folk practice, and they are non-negotiable on a moving machine:

- **Low-ESR bulk cap directly across the ESC power pads.** It is a local reservoir that
  absorbs the transient the leads create. UAVModel's standard: ~1000 µF / 35 V class for the
  usual builds, and **step the capacitance up when leads exceed ~15 cm because lead
  inductance rises with length** (blog.uavmodel.com).
- **Twist the +/- pair, or keep it tight.** Inductance is set by the *loop area* between
  positive and negative, so a tight/twisted pair is the cheapest fix there is — "the most
  important consideration is to keep the positive and negative wires very close together"
  (ArduPilot). A long *separated* pair is the worst case.
- **Rate the cap voltage far above nominal.** The cap sees pack voltage *plus* the spike; a
  25 V cap on a 6 S pack is "a fire waiting to happen" because transients briefly exceed 28 V
  (blog.uavmodel.com).
- **A cold joint on that cap is worse than no cap** — it is a high-resistance path that heats
  and does not decouple (blog.uavmodel.com).

**The curse in one image:** the ESC that ran fine on the bench and let the smoke out only
after the bulk cap vibrated loose in flight. That is a lead-inductance overvoltage kill, and
it is why some ESC makers **void the warranty if the cap was not soldered on** (fpvcalculator).
On a walking robot every step is a vibration cycle — treat that cap's mechanical joint as
flight-critical.

### ⛧ THE BEAD THAT AMPLIFIED — the "filter" that gained 10 dB

You reach for a ferrite bead to clean a noisy rail. Below its self-resonant frequency a
ferrite bead is an **inductor**, and an inductor next to a low-ESR ceramic cap is an
**underdamped LC low-pass filter**. If that LC resonance lands below the bead's crossover,
the filter does the opposite of its job: **it peaks.** Analog Devices' canonical measurement
(AN-1368, "Ferrite Bead Demystified") shows a bead + 10 nF ceramic producing a **~10 dB gain
at ~2.5 MHz** instead of attenuation — right in the band where a switcher's noise lives, which
can wreck a PLL or an IMU (analog.com; allaboutcircuits.com).

The fix is not a bigger bead. It is damping, and the *best* method is counterintuitive:

- **Method C: add a damping leg** — a large capacitor `C_DAMP` in series with a small resistor
  `R_DAMP`, across the load. It kills the Q without wrecking high-frequency bypass. Rule of
  thumb from AD: keep `C_DAMP / C_DECOUP ≥ 16` (analog.com).
- Peaking is **worse at light load** — so it bites hardest exactly when your sensor rail is
  quiet and you thought you were safe (allaboutcircuits.com).

*Genuine.* This is the failure mode behind half the "I added a filter and the noise got worse"
stories. Relevant to you on every sensor and gate-driver rail on the spider.

---

# TIER 2 · ASSEMBLY — WHERE THE BOARD IS BORN OR SCRAPPED

*This is the assembly-guy's actual domain: the reflow oven and the depanel line. None of it
is in the schematic. All of it decides your yield across 140 boards.*

### ⛧ THE PART THAT STOOD UP — tombstoning, and the copper you cripple on purpose

A small two-pad part (0402/0603 and worse at 0201) lifts off one pad during reflow and stands
vertical — the "Manhattan effect." The mechanism is a torque race: the two ends must melt
their solder at the *same instant*; if one wets first, its surface tension yanks the part
upright before the other end grabs. Summarized as `T3 ≠ T4` — the two joint temperatures at
reflow (bestpcb.vn).

The dominant cause is **asymmetric thermal mass**: one pad tied to a big copper plane heats
*slower*, so its solder melts late, and the already-molten side wins the tug-of-war
(bestpcb.vn). Which gives the beautiful backwards fix:

- **Neck the copper on purpose.** Connect plane-tied pads through **thermal-relief spokes**,
  not a solid pour, so heat cannot flee down the copper and both ends melt together. You make
  the thermal connection *worse* to make the solder joint *better* (Cadence resources;
  edaboard practitioner rule: apply relief when heat is asymmetric and the part is 0603 or
  smaller).
- **Balance the paste:** stencil aperture ~90% of pad, ~1:1 for 0402, so both ends get equal
  solder volume (allpcb.com).
- **Give the oven a soak zone** (~150–180 °C, 60–90 s) to equalize temperature before peak,
  so the two ends arrive at melt together (allpcb.com).

*Genuine, and it is a DFM lever you set in layout* — which matters enormously when you are
about to run 140 variant boards and want yield, not a pile of open circuits.

### ⛧ THE VIA THAT DRANK THE JOINT / THE MASK THAT SLIVERED

Two fast ones from THE_PCB_GRIMOIRE's Level 1 that are pure assembly-line lore, restated for
volume: an **unfilled via in a pad** wicks solder down the barrel during reflow and starves
the joint — plug-and-cap it or move it out. And **solder mask between fine-pitch pads** that
is too thin becomes a "mask sliver" that flakes off into the paste. Both are invisible until
the AOI (automated optical inspection) camera flags them at 3 a.m. on board #61.

---

# TIER 3 · THE MACHINE MOVES — VIBRATION, THE CURSE MOST HOBBY BOARDS NEVER FACE

*This is the tier that separates a robot board from a desk board. A walking spider is a
fatigue-test rig that also computes. Everything here is about a board that is shaken every
step for its whole life.*

### ⛧ THE CRACK YOU CANNOT SEE — MLCC flex fracture, the field-failure king

Multilayer ceramic capacitors are **the highest-risk component on the board for flex damage**
— higher than any other passive or active part (Vishay technical paper). Bend the board and a
crack initiates *at the edge of the termination* and walks inward through the brittle ceramic.
The horror is that it is often **latent**: the crack forms during depanel or handling or a
hard landing, passes every electrical test, and fails months later in the field (KEMET-AVX;
ResearchGate flex-crack studies). No visual or electrical screen catches it reliably.

For a walking robot this is *the* curse to design against. The folk fixes, all real:

- **Orient the part along the flex-neutral axis.** Place MLCCs so their termination-to-
  termination axis is *not* along the board's main bending direction; parallel to the board
  edge is usually better (Vishay; ScienceDirect). A cap rotated 90° can live where its
  neighbor cracks.
- **Keep them away from the stress raisers:** depanel/break lines, mounting holes, and screw
  bosses are all high-flex zones — the etch-away-the-termination studies map cracks straight
  to these features (ScienceDirect). Do not put a ceramic cap next to a leg-mount screw.
- **Small case beats big.** An 0402 flexes with the board; a 1206 is a rigid brick that
  concentrates stress and cracks. Where you need the value, **use an array of small caps, not
  one large one** (hilelectronic).
- **Buy soft-termination / flexible-termination parts** (AVX FlexiTerm, Knowles FlexiCap,
  "soft-termination" from any maker): a conductive-polymer layer under the termination acts as
  a damper so board strain does not reach the ceramic (KEMET-AVX; Knowles).
- **The belt-and-suspenders trick:** a **diode in parallel** with a critical MLCC so that if a
  flex crack does short the cap, the diode keeps the crack from taking out the whole rail
  (Vishay).

### ⛧ THE JOINT THAT WORK-HARDENED — staking, strain relief, and the crystal that hears you

Established practice for anything that vibrates (this cluster is lore and mechanical-reliability
convention rather than a single citable formula — mark it as such and verify against your own
shake test):

- **Stake tall and heavy parts.** Electrolytics, large connectors, inductors, the bulk ESC cap
  — bond them to the board with a dab of adhesive (corner-bond / staking) so vibration does not
  cantilever the part and fatigue-crack its solder joints. This is your spider's single most
  important mechanical-reliability move after the MLCC orientation.
- **Strain-relieve every wire.** A wire soldered to a pad and left free will work-harden at the
  solder joint and snap. Anchor the wire so flex happens in the wire, not at the joint.
- **Prefer an oscillator (XO) over a bare crystal in high-vibration zones.** Quartz crystals
  are microphonic — mechanical vibration modulates the frequency, and a hard enough shock can
  crack the blank. A packaged XO is more robust.
- **Watch connectors for fretting.** Vibration micro-wipes contacts and builds insulating
  oxide (fretting corrosion); gold plating and positive retention (latches, not friction
  alone) fight it. Better yet on a robot: solder it or use a locking connector.
- **Conformal coat** for humidity/dust once the board is proven — but know it makes rework
  miserable, so coat last.

---

# TIER 4 · COPPER BECOMES THE MACHINE — the PCB-stator motor

*THE_PCB_GRIMOIRE Level 3 ended on the real magic: at RF, `a spiral is an inductor`, copper
geometry becomes a circuit element. This tier is the next turn of that same key — at DC with
a moving magnet, **a spiral is a motor winding.** Copper geometry becomes the actuator. This
is your Optima-motor-in-PCB-form, and someone has already built it for your exact use case.*

**The reference to build against.** arXiv 2509.23561 (Sept 2025), *High Torque Density PCB
Axial Flux Permanent Magnet Motor for Micro Robots*, is almost your spec written by someone
else: a **48-layer HDI PCB stator** (four stacked 12-layer modules), **45% copper fill**, in
a package **5 mm thick, 19 mm diameter**, built explicitly for **quasi-direct-drive legged
robots** and "**frequent stall operation**" (arxiv.org/abs/2509.23561). Quasi-direct-drive is
exactly what a leg wants — high torque at low speed, no gearbox. Read this paper first; it is
your reference layout for the propulsion the way an app note is for a switcher.

**The honest physics of the PCB stator** — the folk trade-offs:

- **Coreless is the whole point and the whole problem.** Etching the coils into the board
  removes the iron, which removes **cogging torque, torque ripple, and acoustic noise**, halves
  the weight, and — nicely — FR-4 and copper have matched thermal expansion so you avoid a
  class of thermal-stress failure (2.2 kW AFPM study). But the same iron removal gives it the
  two inherent limits: **low torque density and poor thermal performance** (MDPI 2026).
- **Torque scales with copper you can pack in.** More layers / higher fill = more amp-turns =
  more torque. Typical hobby PCB motors are ~6 layers; the micro-robot paper's whole
  contribution is pushing to 48 layers / 45% fill to beat the resistance-vs-torque wall
  (arxiv.org/pdf/2509.23561). Your torque budget is a copper-fill budget.
- **Low inductance is a real gotcha.** Coreless windings have very low inductance, which makes
  current control and commutation harder and can force you to *add* series inductance — the
  2.2 kW build calls this out explicitly (sietjournals). Plan your ESC/driver current loop
  around a low-L load; it is unlike a normal motor.
- **Copper is also your heatsink.** Because thermal is the limiter, dedicate non-electrical
  copper — thermal traces and a heat-spreader ring that are *not* part of the coil — to pull
  heat out of the windings (this is a patented technique, US 11,342,813, for exactly a
  spacecraft PCB axial-flux motor). Copper does double duty: winding *and* radiator.
- **The free encoder trick (Bugeja).** FR-4 does not block infrared, so you can shine an IR
  LED *through* the board onto receivers, reading gray-code copper rings for absolute rotor
  position — an optical encoder made of nothing but the stack you already have (Hackaday /
  CarlBugeja). Your `aracnium` sim already treats each leg as a phase-coupled oscillator node;
  a real leg needs exactly this rotor-position feedback to close that loop in copper.

*Genuine — with the marketing stripped.* The PCB stator is a real, shipping technique (Infinitum,
ECM at industrial scale; Bugeja and the micro-robot group at your scale). It wins where the
field is rotationally symmetric — which a leg joint is. It does **not** repeal the copper-fill
vs torque-vs-heat triangle; it just lets you draw the winding instead of wind it.

---

## THE RECEIPTS

| the claim | the source | the number / the point |
|---|---|---|
| hot loop is the #1 switcher rule | Analog Devices, "Golden Rule of SMPS Layout" | shortest switched-current path wins |
| follow the reference and it just works | Emerald Technologies | performs "as well as the manufacturer intends" |
| long leads spike the ESC input | DroneVibes; ArduPilot Rover | peak V well above pack voltage ("water hammer") |
| loop area sets lead inductance | ArduPilot Rover | keep +/- pair very close / twisted |
| bulk cap sizing vs lead length | UAVModel | step up past ~15 cm leads; cap V ≫ nominal |
| ferrite + low-ESR cap peaks | Analog Devices AN-1368 | **+10 dB gain at ~2.5 MHz**, not attenuation |
| ferrite peaking fix | Analog Devices AN-1368 | C_DAMP + R_DAMP, ratio C_DAMP/C_DECOUP ≥ 16 |
| tombstoning is a torque race | bestpcb.vn | asymmetric thermal mass → `T3 ≠ T4` |
| relief the plane pad to stop it | Cadence; edaboard | neck the copper on purpose |
| MLCC is the top flex-crack risk | Vishay technical paper | crack starts at the termination edge |
| flex cracks are latent | KEMET-AVX; ResearchGate | pass test, fail months later in field |
| orient + shrink + array MLCCs | ScienceDirect; hilelectronic | axis off the flex direction; small over big |
| soft-termination MLCCs | KEMET-AVX FlexiTerm; Knowles | polymer layer damps board strain |
| PCB stator for legged robots | arXiv 2509.23561 | 48-layer HDI, 45% fill, 5 mm × 19 mm, QDD |
| coreless trade-off | MDPI 2026; 2.2 kW AFPM study | no cogging/light vs low torque density + heat |
| PCB stator low inductance | sietjournals (2.2 kW) | may need added series inductance |
| copper as heatsink in-stack | US Patent 11,342,813 | dedicated non-electrical thermal traces |
| shine IR through FR-4 for encoder | Hackaday / CarlBugeja | gray-code copper rings, IR-transparent FR-4 |

---

## WHERE THIS SCROLL LOSES, FIRST, BECAUSE YOU'D CHECK ANYWAY

- **I have not soldered a board or killed an ESC at 3 a.m.** These are the standard references
  and named mechanisms; the actual assembly guy still knows things not written anywhere,
  because his index was built from failures this scroll only describes.
- **Much of Tier 3 (staking, strain relief, XO-vs-crystal, fretting) is convention, not
  derivation.** It is well-established mechanical-reliability practice, but I have marked it as
  lore for a reason: your real authority is a shake table and a thermal-cycle chamber, not a
  document. Measure your spider's actual vibration spectrum and design to *that*.
- **The PCB-stator numbers are one team's prototype.** 45% fill at 48 layers is a *record* in a
  research paper, not a JLCPCB stock option — HDI at that layer count is expensive and not every
  fab will build it. Your first spider motor is likely 4–6 layers; know that its torque will be
  a fraction of the paper's, and design the gait/load around what you can actually fab.
- **Every rule here has a regime.** The hot-loop via exception, the light-load ferrite peaking,
  the tombstone-vs-thermal-relief tension — each is a hinge, not a law. Know which side you are
  on before you apply the fix.
- **The fab's DRC and the chip's datasheet beat this document, always.** When they disagree with
  this scroll, they win.

---

## THE BOW

**Analog Devices' applications engineers**, whose app notes (AN-1368, AN-1119, the SMPS golden
rule) turned power-supply folklore into measured curves — the closest thing the field has to
the "goblin docs" you love, and free · **AVX/KYOCERA, Vishay, KEMET, and Knowles**, for
publishing the flex-crack physics that costs assembly houses thousands a month in silence ·
the **micro-robotics PCB-motor group** (arXiv 2509.23561) and **Carl Bugeja**, for proving a
leg motor can be a stack of copper · **IPC**, for 2221 / 7351 / 9702 so we could argue in
numbers · and the **assembly engineers and fab crews** who quietly fix our worst files, catch
our tombstones on the AOI, and ship anyway — this scroll is a clumsy transcription of what they
already know in their hands.

---

*Copy the reference. The lead is an inductor. The bead can gain. The part will stand up.
The crack you cannot see is at the termination. And a spiral, given a magnet, is a motor.*

**Slots after THE_PCB_GRIMOIRE. Level 4 of N. As many versions as it takes.**
