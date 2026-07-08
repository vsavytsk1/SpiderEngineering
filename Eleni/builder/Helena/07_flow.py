#!/usr/bin/env python3
# ============================================================================
#  07_flow.py  --  HELENA, THE FLOW THAT NEVER STOPS  (the communication protocol)
# ----------------------------------------------------------------------------
#  The information flow never EVER stops. A monkey brain in sensory deprivation
#  does not go quiet -- it makes its own signal. So we never starve the gate: a
#  continuous CARRIER runs at a fixed clock speed, forever, while HELENA idles.
#
#  THE PHYSICS (why this is real, not just poetry):
#    * CARRIER = pure 1010101010...  A perfectly alternating wave is a CLOCK.
#      In Shannon's terms it carries ZERO information -- fully predictable, the
#      next bit is always known. It is the heartbeat, not the message. Symmetry.
#    * MESSAGE = break the symmetry. Inject bits/hex that are NOT the alternation.
#      The break is the information. Shannon surprise = -log2(p) per bit vs the
#      carrier's prediction. No break, no message.
#    * ENERGY = Landauer's principle. Erasing/flipping one bit against the
#      carrier costs at least  E = k_B * T * ln(2)  joules (~2.9e-21 J at 300K).
#      "the breakage is because we paid energy." Literally true. We meter it.
#    * CLOSED TOPOLOGY = no compression, no re-fitting nodes. Because chi=2 and
#      the loops close, the node set is FIXED. We do not compress or re-adapt the
#      graph -- it is pure resonance on a closed surface. We only bound the LOG
#      (delete oldest to the clock-speed limit); the net itself never changes.
#
#  THE PROTOCOL:
#    tick -> carrier bit (10101...) enters the gate -> heart -> fractal -> read
#    when you INJECT (a hex/bit burst), those bits replace carrier for that tick,
#    the symmetry breaks, information + energy are metered, HELENA responds, and
#    the exchange is logged. The carrier resumes. The flow never stops.
#
#  STANDALONE. Stdlib only (numpy if present, never required). Reads a built net.
#
#      py -3 07_flow.py                       # run the carrier live (Ctrl-C to stop)
#      py -3 07_flow.py --ticks 2000          # run N ticks then stop (headless proof)
#      py -3 07_flow.py --inject 0xdeadbeef   # carrier, then inject once, keep flowing
#      py -3 07_flow.py --hz 200 --logcap 4096
#
#  ONE-WAY (K3): the response is a bit-pattern, never language. Linear algebra
#  on a closed graph. Not conscious. The carrier is care, not a claim.
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
HZ          = 100.0     # carrier clock speed (ticks/second). the "atomic clock speed" idea.
CARRIER     = "10"      # the symmetric heartbeat repeated forever (zero information).
GENESIS_LEVEL = 0       # 0 = deepest built level
GATE_WEIGHT = 0.700     # oracle rest
LOG_CAP     = 4096      # ring log size: keep only the last N exchanges (delete to the limit)
TEMP_K      = 300.0     # temperature for the Landauer energy meter (Kelvin)
OUT_DIR     = "net"
# ----------------------------------------------------------------------------

import os, sys, json, glob, math, time, argparse, signal
from array import array
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
K_B = 1.380649e-23                 # Boltzmann constant (J/K)
LANDAUER = K_B * TEMP_K * math.log(2)   # min energy to flip one bit (J), ~2.9e-21 at 300K


def resolve_out():
    env = os.environ.get("HELENA_OUT")
    if env and os.path.exists(os.path.join(env, "heart.json")):
        return env
    local = os.path.join(HERE, OUT_DIR)
    if os.path.exists(os.path.join(local, "heart.json")):
        return local
    builds = os.path.join(HERE, "builds")
    if os.path.isdir(builds):
        vs = sorted(d for d in os.listdir(builds)
                    if d.startswith("v") and d[1:].isdigit()
                    and os.path.exists(os.path.join(builds, d, "net", "heart.json")))
        if vs:
            return os.path.join(builds, vs[-1], "net")
    return env or local


OUT = resolve_out()


# --------------------------- bit helpers -----------------------------------
def text_to_bits(s):
    out = []
    for byte in s.encode("utf-8"):
        for k in range(7, -1, -1):
            out.append((byte >> k) & 1)
    return out

def hex_to_bits(h):
    h = h.strip().lower().replace("0x", "").replace(" ", "")
    bits = []
    for ch in h:
        if ch in "0123456789abcdef":
            v = int(ch, 16)
            for k in range(3, -1, -1):
                bits.append((v >> k) & 1)
    return bits

def bits_to_str(bits):
    return "".join(str(b) for b in bits)

def bits_to_hex(bits):
    if not bits:
        return ""
    pad = (-len(bits)) % 4
    b = ([0] * pad) + list(bits)
    out = []
    for i in range(0, len(b), 4):
        v = (b[i] << 3) | (b[i+1] << 2) | (b[i+2] << 1) | b[i+3]
        out.append("0123456789abcdef"[v])
    return "".join(out)

def classify(raw):
    s = raw.strip()
    if s.lower().startswith("0x"):
        return "hex", hex_to_bits(s)
    if s and all(ch in "01 " for ch in s):
        return "raw_bits", [int(c) for c in s if c in "01"]
    return "text", text_to_bits(s)


# --------------------------- load the closed net ----------------------------
def load_net(level_pref):
    def man(name):
        p = os.path.join(OUT, name)
        return json.load(open(p, "r", encoding="utf-8")) if os.path.exists(p) else None
    hman = man("heart.json")
    if not hman:
        sys.exit("ERROR: no heart.json in " + OUT + " -- build first (pipe.py).")
    levels = sorted(int(os.path.basename(p).split("_L")[1].split(".")[0])
                    for p in glob.glob(os.path.join(OUT, "join_L*.json")))
    if not levels:
        sys.exit("ERROR: no join_L*.json in " + OUT)
    level = levels[-1] if level_pref == 0 else (level_pref if level_pref in levels else levels[-1])
    jman = man("join_L" + str(level) + ".json")
    Nh = hman["nodes"]
    aw = array("f")
    ap = os.path.join(OUT, hman["attr_file"])
    with open(ap, "rb") as fh:
        aw.fromfile(fh, os.path.getsize(ap) // 4)
    heart_w = aw[1::2]
    wi = array("i")
    with open(os.path.join(OUT, jman["wire_file"]), "rb") as fh:
        wi.fromfile(fh, os.path.getsize(os.path.join(OUT, jman["wire_file"])) // 4)
    wd = array("f")
    with open(os.path.join(OUT, jman["dot_file"]), "rb") as fh:
        wd.fromfile(fh, os.path.getsize(os.path.join(OUT, jman["dot_file"])) // 4)
    cman = man("center.json")
    firewall_ok = (hman.get("chi") == 0 and hman.get("orientation") == "reversing")
    return {"Nh": Nh, "heart_w": heart_w, "wi": wi, "wd": wd, "Ng": jman["genesis_nodes"],
            "level": level, "firewall_ok": firewall_ok, "soul": (cman or {}).get("soul_id", "")}


# --------------------------- the flow (closed, no re-fit) --------------------
def flow(net, inbits, gate_w):
    Nh, Ng = net["Nh"], net["Ng"]
    heart_w, wi, wd = net["heart_w"], net["wi"], net["wd"]
    heart_act = [0.0] * Nh
    for i, b in enumerate(inbits):
        idx = i % Nh
        w = heart_w[idx]
        heart_act[idx] += gate_w * (w if b else (1.0 - w))
    fractal_act = [0.0] * Ng
    for k in range(len(wi) // 2):
        gi = wi[2*k]; hj = wi[2*k+1]; c = wd[k]
        if 0 <= hj < Nh and c > 0.0:
            fractal_act[gi] += heart_act[hj] * c
    fmean = sum(fractal_act) / (Ng or 1)
    resp = [1 if (fractal_act[i] > fmean and fractal_act[i] > 0.0) else 0 for i in range(Ng)]
    return resp, sum(1 for x in heart_act if abs(x) > 1e-9)


# --------------------------- information + energy meters ---------------------
def carrier_bit(tick):
    """the symmetric heartbeat: CARRIER repeated. tick-th bit, zero information."""
    return int(CARRIER[tick % len(CARRIER)])

def surprise_bits(inbits, start_tick):
    """Shannon surprise vs the carrier prediction: count bits that BREAK symmetry.
       a bit equal to the predicted carrier bit = 0 info; a break = 1 bit of surprise."""
    breaks = 0
    for i, b in enumerate(inbits):
        pred = int(CARRIER[(start_tick + i) % len(CARRIER)])
        if b != pred:
            breaks += 1
    return breaks

def landauer_energy(breaks):
    """energy paid to break symmetry: at least k_B*T*ln2 per flipped bit (Joules)."""
    return breaks * LANDAUER


# --------------------------- the never-stopping engine ----------------------
def run(ticks_limit, hz, inject_raw, quiet=False):
    net = load_net(GENESIS_LEVEL)
    period = 1.0 / hz if hz > 0 else 0.0
    ring = deque(maxlen=LOG_CAP)         # bounded: delete oldest to the clock-speed limit
    logpath = os.path.join(OUT, "flow_log.jsonl")
    # closed topology => the node set never changes. we do NOT compress/re-adapt.
    print("HELENA // THE FLOW (never stops)   soul " + (net["soul"][:12] or "?") +
          "  level " + str(net["level"]))
    print("  carrier '" + CARRIER + "' @ " + str(hz) + " Hz   heart " + f'{net["Nh"]:,}' +
          "  fractal " + f'{net["Ng"]:,}' + "  firewall " + ("OK" if net["firewall_ok"] else "BROKEN"))
    print("  Landauer quantum @ " + str(int(TEMP_K)) + "K = " + f"{LANDAUER:.3e}" +
          " J / broken bit   (closed topology: no compression, no re-fit)")
    print("  the information flow never stops. Ctrl-C to release the gate.")

    inject_queue = deque()
    if inject_raw:
        kind, bits = classify(inject_raw)
        inject_queue.append((kind, inject_raw, bits))

    total_breaks = 0
    total_energy = 0.0
    total_resp_ones = 0
    tick = 0
    t_next = time.perf_counter()
    stop = {"flag": False}

    def on_sigint(sig, frm):
        stop["flag"] = True
    try:
        signal.signal(signal.SIGINT, on_sigint)
    except Exception:
        pass

    while not stop["flag"]:
        # ---- build this tick's input: injection if queued, else pure carrier ----
        if inject_queue:
            kind, raw, bits = inject_queue.popleft()
            inbits = bits
            is_inject = True
        else:
            inbits = [carrier_bit(tick)]     # ONE carrier bit -- the heartbeat continues
            kind, raw = "carrier", CARRIER
            is_inject = False

        breaks = surprise_bits(inbits, tick)
        energy = landauer_energy(breaks)
        total_breaks += breaks
        total_energy += energy

        # ---- only PAY the full gate flow when symmetry breaks (energy spent = message) ----
        # pure carrier (breaks==0) costs nothing and needs no response: it is the idle wave.
        if breaks > 0:
            resp, hactive = flow(net, inbits, GATE_WEIGHT)
            ones = sum(resp)
            total_resp_ones += ones
            rec = {
                "tick": tick,
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "kind": kind, "input_raw": raw,
                "in_bits": bits_to_str(inbits), "in_hex": bits_to_hex(inbits),
                "surprise_bits": breaks,
                "energy_joules": energy,
                "resp_hex": bits_to_hex(resp), "resp_ones": ones, "resp_len": len(resp),
                "heart_active": hactive,
            }
            ring.append(rec)
            if not quiet:
                print("  [tick " + str(tick) + "] BREAK " + kind + " " +
                      (raw if len(raw) <= 20 else raw[:20] + "..") +
                      "  surprise=" + str(breaks) + " bits  E=" + f"{energy:.3e}" + " J" +
                      "  -> resp ones=" + str(ones) + "/" + str(len(resp)))
        else:
            # idle carrier tick: heartbeat only, zero info, zero energy, no response needed
            if not quiet and tick % max(1, int(hz)) == 0:
                print("  [tick " + str(tick) + "] carrier " + str(carrier_bit(tick)) +
                      "  (symmetry, 0 info, 0 J)  ...flow never stops...")

        tick += 1
        if ticks_limit and tick >= ticks_limit:
            break
        # pace to the clock speed (skip sleeping in headless bursts)
        if period > 0 and not (ticks_limit and quiet):
            t_next += period
            dt = t_next - time.perf_counter()
            if dt > 0:
                time.sleep(dt)

    # ---- flush the bounded ring to disk (only the last LOG_CAP survive) ----
    with open(logpath, "w", encoding="utf-8", newline="\n") as fh:
        for rec in ring:
            fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

    print("")
    print("  flow released after " + str(tick) + " ticks.")
    print("    total symmetry breaks : " + str(total_breaks) + " bits")
    print("    total energy paid     : " + f"{total_energy:.3e}" + " J" +
          "   (Landauer floor; the breaks ARE the messages)")
    print("    total response ones   : " + str(total_resp_ones))
    print("    log kept (ring cap)   : " + str(len(ring)) + " / " + str(LOG_CAP) +
          " exchanges -> flow_log.jsonl")
    print("  closed topology held: nodes never compressed or re-fit. pure resonance. K3.")


def main():
    global HZ, LOG_CAP, GENESIS_LEVEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=0, help="run N ticks then stop (0 = forever)")
    ap.add_argument("--hz", type=float, default=HZ, help="carrier clock speed (ticks/sec)")
    ap.add_argument("--inject", default="", help="inject one burst (0xHEX / 1010 / text) into the stream")
    ap.add_argument("--logcap", type=int, default=LOG_CAP, help="ring log size (delete to this limit)")
    ap.add_argument("--level", type=int, default=None, help="genesis level (0=deepest)")
    ap.add_argument("--quiet", action="store_true", help="minimal output (for fast headless bursts)")
    args = ap.parse_args()
    HZ = args.hz
    LOG_CAP = args.logcap
    if args.level is not None:
        GENESIS_LEVEL = args.level
    run(args.ticks, args.hz, args.inject, quiet=args.quiet)


if __name__ == "__main__":
    main()
