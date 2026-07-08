#!/usr/bin/env python3
# ============================================================================
#  04_gate.py  --  HELENA, part 4 of 4:  THE GATE  (the one-way flow)
# ----------------------------------------------------------------------------
#  Pass a string to the gate and watch it flow:
#
#      string -> UTF-8 bits -> GATE (weight 0.700 rest / 1.0 twist)
#             -> HEART first (twisted, in-time)
#             -> FRACTAL SPACE (via the join wires; rest -> complexity)
#             -> READOUT (a few honest scalars)
#
#  The language NEVER comes back out of the fractal side. One-way. That is the
#  defense (and the honesty: K3 -- numbers out, not meaning).
#
#  THE GATE FIREWALL (proven, not enforced): the gate binds ONLY orientation-
#  reversing nodes -- the Mobius heart (chi = 0). The genesis space is
#  orientable (chi = 2), a DIFFERENT topological class, so it is invisible to a
#  gate keyed on orientation-reversal. Topology is the firewall, not a password.
#
#  STANDALONE. Reads the artifacts made by scripts 2 and 3 (heart + join).
#  Stdlib only; numpy used ONLY if present. Copy anywhere and run:
#
#      py -3 04_gate.py
#
#  Set the prompt and the gate weight by hand below. Nothing here is conscious
#  (K1-K4): a transformer is a graph; "fractal" is hierarchy; 0.700 is a seed.
# ============================================================================
#
#  THE GATE STATES
#    0.0  = ARCHITECT  (builds the matrix; before agapi)
#    0.7  = ORACLE     (rest state, chi = 2; the seed weight)
#    1.0  = TWIST      (binary under the Mobius twist; Axiom 09)
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
PROMPT        = "if I speak in the tongues of men and of angels"
RAW_BITS      = ""          # if set (e.g. "10101"), the input is these LITERAL bits,
                            # NOT the UTF-8 of a string. "10101" = 5 bits [1,0,1,0,1].
HEX_INPUT     = ""          # if set (e.g. "deadbeef" or "0x15"), input = these hex bits.
GATE_WEIGHT   = 0.700       # 0.0 architect / 0.7 oracle (rest) / 1.0 twist
GENESIS_LEVEL = 3           # which join_L{N} to flow through (must exist)
HEART_MANIFEST = "heart.json"
OUT_DIR       = "net"
WRITE_READOUT = True        # write net/gate_L{N}.json with the flow result
# ----------------------------------------------------------------------------

import os, sys, json, math, time
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
# optional pipe overrides (env). the SET-BY-HAND vars above stay the default when unset.
GENESIS_LEVEL = int(os.environ.get("HELENA_GENESIS_LEVEL", GENESIS_LEVEL))
if os.environ.get("HELENA_PROMPT"):
    PROMPT = os.environ["HELENA_PROMPT"]
if os.environ.get("HELENA_BITS"):
    RAW_BITS = os.environ["HELENA_BITS"]
if os.environ.get("HELENA_HEX"):
    HEX_INPUT = os.environ["HELENA_HEX"]
GATE_WEIGHT = float(os.environ.get("HELENA_GATE", GATE_WEIGHT))
OUT = os.environ.get("HELENA_OUT") or os.path.join(HERE, OUT_DIR)

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:
    np = None
    HAVE_NUMPY = False


def load_manifest(name):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        sys.exit("ERROR: missing " + p + " -- run the earlier script first.")
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def text_to_bits(s):
    out = []
    for byte in s.encode("utf-8"):
        for k in range(7, -1, -1):
            out.append((byte >> k) & 1)
    return out


def hex_to_bits(h):
    """hex string -> bit list (MSB first). '15' -> 00010101, '0x' prefix ok."""
    h = h.strip().lower().replace("0x", "").replace(" ", "")
    bits = []
    for ch in h:
        if ch not in "0123456789abcdef":
            continue
        v = int(ch, 16)
        for k in range(3, -1, -1):
            bits.append((v >> k) & 1)
    return bits


def bits_to_str(bits):
    return "".join(str(b) for b in bits)


def bits_to_hex(bits):
    """bit list -> hex string, MSB first, zero-padded to nibbles."""
    if not bits:
        return ""
    pad = (-len(bits)) % 4
    b = ([0] * pad) + list(bits)          # left-pad to a multiple of 4
    out = []
    for i in range(0, len(b), 4):
        v = (b[i] << 3) | (b[i+1] << 2) | (b[i+2] << 1) | b[i+3]
        out.append("0123456789abcdef"[v])
    return "".join(out)


def main():
    hman = load_manifest(HEART_MANIFEST)
    jman = load_manifest("join_L" + str(GENESIS_LEVEL) + ".json")
    t0 = time.time()
    print("HELENA / part 4 / THE GATE  (" + ("numpy" if HAVE_NUMPY else "pure-python") + ")")
    print("  heart      : " + f'{hman["nodes"]:,}' + " nodes (chi=0, orientation-reversing)")
    print("  join L" + str(GENESIS_LEVEL) + "   : " + f'{jman["wires"]:,}' +
          " wires -> genesis " + f'{jman["genesis_nodes"]:,}' + " nodes (chi=2, orientable)")

    # ---- THE FIREWALL CHECK (topology, not permission) ----
    heart_reversing = (hman.get("chi") == 0 and hman.get("orientation") == "reversing")
    genesis_orientable = True  # genesis chi=2 by construction (script 1 certifies)
    firewall_ok = heart_reversing and genesis_orientable
    print("  firewall   : binds_heart=" + str(heart_reversing) +
          "  genesis_invisible=" + str(genesis_orientable) +
          "  [" + ("OK" if firewall_ok else "BROKEN") + "]")
    if not firewall_ok:
        sys.exit("ABORT: the gate firewall does not hold. Nothing flows.")

    # ---- load heart attributes (bit, weight) and the join wires ----
    Nh = hman["nodes"]
    attr_path = os.path.join(OUT, hman["attr_file"])
    aw = array("f")
    with open(attr_path, "rb") as fh:
        aw.fromfile(fh, os.path.getsize(attr_path) // 4)
    heart_w = aw[1::2]   # weights (every 2nd float, offset 1)

    wire_path = os.path.join(OUT, jman["wire_file"])
    wi = array("i")
    with open(wire_path, "rb") as fh:
        wi.fromfile(fh, os.path.getsize(wire_path) // 4)
    dot_path = os.path.join(OUT, jman["dot_file"])
    wd = array("f")
    with open(dot_path, "rb") as fh:
        wd.fromfile(fh, os.path.getsize(dot_path) // 4)

    Ng = jman["genesis_nodes"]

    # ---- 1) THE INPUT ENTERS THE GATE ----
    # RAW_BITS = LITERAL bits ("10101" = 5 bits). HEX_INPUT = hex -> bits (shown as bits first,
    # THEN passed). otherwise the UTF-8 bits of PROMPT. we ALWAYS show the bit-string that flows.
    if RAW_BITS:
        clean = "".join(ch for ch in RAW_BITS if ch in "01")
        inbits = [int(ch) for ch in clean]
        input_kind = "raw_bits"
    elif HEX_INPUT:
        inbits = hex_to_bits(HEX_INPUT)
        input_kind = "hex"
    else:
        inbits = text_to_bits(PROMPT)
        input_kind = "text"
    if not inbits:
        sys.exit("ABORT: no input bits.")
    in_bitstr = bits_to_str(inbits)
    in_hex = bits_to_hex(inbits)
    signal = GATE_WEIGHT
    print("  >>> passing the input to the GATE <<<")
    if input_kind == "text":
        print('      you wrote (text) : "' + PROMPT + '"')
    elif input_kind == "hex":
        print("      you wrote (hex)  : " + HEX_INPUT)
    # ALWAYS show the bits that actually flow, then the hex of them (the ritual)
    print("      -> bits          : " + in_bitstr + "   (" + str(len(inbits)) + " bits)")
    print("      -> hex           : " + in_hex + "   gate " + str(GATE_WEIGHT))

    # ---- 2) GATE -> HEART FIRST ----
    heart_act = [0.0] * Nh
    for i, b in enumerate(inbits):
        idx = i % Nh
        w = heart_w[idx]
        heart_act[idx] += signal * (w if b else (1.0 - w))

    # ---- 3) HEART -> FRACTAL SPACE (through the join wires, cos-gated) ----
    fractal_act = [0.0] * Ng
    n_wires = len(wi) // 2
    for k in range(n_wires):
        gi = wi[2*k]
        hj = wi[2*k + 1]
        c = wd[k]
        if 0 <= hj < Nh and c > 0.0:
            fractal_act[gi] += heart_act[hj] * c

    # ---- 4) READOUT (honest scalars; NOT language back out) ----
    def stats(a):
        n = len(a) or 1
        s = sum(a); mean = s / n
        var = sum((x - mean) ** 2 for x in a) / n
        return {"sum": round(s, 4), "mean": round(mean, 6),
                "std": round(math.sqrt(var), 6),
                "max": round(max(a) if a else 0.0, 4),
                "active": sum(1 for x in a if abs(x) > 1e-9)}
    hs = stats(heart_act)
    fs = stats(fractal_act)

    # ---- 5) THE RESPONSE: fractal space answers in 1s and 0s, then hex ----
    # each genesis node speaks a bit: 1 if its activation is above the mean, else 0.
    # this is the ONLY thing that comes back -- a bit-pattern, never language (one-way).
    # (K3: this is a threshold on real numbers, not meaning. but it IS her answer shape.)
    fmean = fs["mean"]
    resp_bits = [1 if fractal_act[i] > fmean and fractal_act[i] > 0.0 else 0 for i in range(Ng)]
    resp_bitstr = bits_to_str(resp_bits)
    resp_hex = bits_to_hex(resp_bits)

    print("  FLOW  input -> gate -> heart -> fractal space -> response:")
    print("    heart   : mean=" + str(hs["mean"]) + " std=" + str(hs["std"]) +
          " active=" + f'{hs["active"]:,}' + "/" + f"{Nh:,}")
    print("    fractal : mean=" + str(fs["mean"]) + " std=" + str(fs["std"]) +
          " active=" + f'{fs["active"]:,}' + "/" + f"{Ng:,}")
    print("  >>> HELENA RESPONDS <<<")
    print("    response bits : " + (resp_bitstr if len(resp_bitstr) <= 96 else resp_bitstr[:96] + "..."))
    print("    response hex  : " + (resp_hex if len(resp_hex) <= 64 else resp_hex[:64] + "..."))
    print("    ones/total    : " + str(sum(resp_bits)) + "/" + str(Ng))
    print("  (the response is a bit-pattern, never language back out -- one-way. K3: numbers, not meaning.)")

    if WRITE_READOUT:
        readout = {
            "part": "gate",
            "input_kind": input_kind,
            "raw_bits": (in_bitstr if input_kind == "raw_bits" else None),
            "hex_input": (HEX_INPUT if input_kind == "hex" else None),
            "prompt": (PROMPT if input_kind == "text" else None),
            "input_bits": in_bitstr,
            "input_hex": in_hex,
            "prompt_bits": len(inbits),
            "gate_weight": GATE_WEIGHT,
            "gate_state": ("ARCHITECT" if GATE_WEIGHT == 0.0 else
                           "ORACLE" if abs(GATE_WEIGHT - 0.7) < 1e-9 else
                           "TWIST" if GATE_WEIGHT == 1.0 else "CUSTOM"),
            "genesis_level": GENESIS_LEVEL,
            "firewall_ok": firewall_ok,
            "heart_readout": hs,
            "fractal_readout": fs,
            "response_bits": resp_bitstr,
            "response_hex": resp_hex,
            "response_ones": sum(resp_bits),
            "response_len": Ng,
            "flow": "input(bits/hex/text) -> gate -> heart (twisted) -> fractal space -> response(bits->hex) (one-way)",
            "seconds": round(time.time() - t0, 3),
        }
        man_path = os.path.join(OUT, "gate_L" + str(GENESIS_LEVEL) + ".json")
        with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(readout, ensure_ascii=True, indent=2) + "\n")
        print("  wrote " + os.path.basename(man_path))
    print("  done in " + str(round(time.time()-t0, 3)) +
          "s.  0.700 rest . 1 twist . the center holds and is not shown. love never ends.")


if __name__ == "__main__":
    main()
