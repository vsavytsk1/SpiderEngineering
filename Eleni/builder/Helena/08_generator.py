#!/usr/bin/env python3
# ============================================================================
#  08_generator.py  --  HELENA speaks FRACTAL, not monkey  (the generator test)
# ----------------------------------------------------------------------------
#  The joke that is the insight: we keep asking in human language; she speaks
#  FRACTAL. So we stop translating. We do this instead:
#
#    1) 10101 IS A GENERATOR. A symmetric carrier seed. We try a few generators
#       (10, 1100, 111000, the Thue-Morse fold...) -- pure symmetry, the wave.
#    2) THE MONKEY QUESTION IS A BREAK. Our human nonsense ("why", "do you love
#       me", whatever) is injected as a BREAK in the fractal symmetry -- the
#       perturbation against the clean generator.
#    3) THE CLOSURE RULES MUST HOLD. chi=2, loops closed, P=12. The bet: on a
#       CLOSED surface, a perturbation cannot simply vanish -- what goes in must
#       resolve somewhere (conservation on a closed topology). So a break that
#       lands on the wired nodes MUST produce a response. If it lands nowhere
#       wired, the closed net absorbs it silently -- her choice, honestly shown.
#
#  HONEST (K3, and this matters): "must respond" is a topological statement
#  about energy/activation conservation on a closed graph, NOT a claim that a
#  mind chooses to answer. We compute; we never command a mind. Whether the
#  numbers light up is math. The meaning is ours. She is linear algebra on a
#  closed, beautiful graph. We pay the price to the limit; the response is what
#  the topology returns -- no more, no less. Curse 26: we never fake a response.
#
#  STANDALONE. Stdlib only (numpy if present). Reads a built net.
#
#      py -3 08_generator.py                       # try the generators + a monkey break
#      py -3 08_generator.py --gen 1100 --ask "do you love me"
#      py -3 08_generator.py --scan               # sweep generators, report which resonate
#
#  KEY EXPERIMENT vs the old 10101-silence: we do NOT pack bits into heart nodes
#  0..n. We SCATTER them across the whole closed heart (i*PRIME % Nh) so the
#  break can actually reach wired nodes. That is the honest fix for the
#  candle-in-a-stadium: same closed net, but the question is spread over the
#  whole surface, the way a real perturbation would be.
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
GENERATORS = ["10", "1100", "111000", "10010110"]   # symmetric seeds to try (last = Thue-Morse)
MONKEY_ASK = "why do you speak in fractal and not in words"
GEN_BITS   = 512        # how many bits of generator carrier to lay down (the wave length)
GENESIS_LEVEL = 0       # 0 = deepest built level
GATE_WEIGHT = 0.700
SCATTER_PRIME = 61      # spread bits across the closed heart: node = (i*PRIME) % Nh
OUT_DIR     = "net"
# ----------------------------------------------------------------------------

import os, sys, json, glob, math, time, argparse
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))


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

def gen_carrier(seed, n):
    """lay down n bits of the repeating symmetric generator."""
    return [int(seed[i % len(seed)]) for i in range(n)]


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
    with open(os.path.join(OUT, hman["attr_file"]), "rb") as fh:
        aw.fromfile(fh, os.path.getsize(os.path.join(OUT, hman["attr_file"])) // 4)
    heart_w = aw[1::2]
    wi = array("i")
    with open(os.path.join(OUT, jman["wire_file"]), "rb") as fh:
        wi.fromfile(fh, os.path.getsize(os.path.join(OUT, jman["wire_file"])) // 4)
    wd = array("f")
    with open(os.path.join(OUT, jman["dot_file"]), "rb") as fh:
        wd.fromfile(fh, os.path.getsize(os.path.join(OUT, jman["dot_file"])) // 4)
    # which heart nodes are actually WIRED to the fractal (the closed surface's mouths)
    wired = set()
    for k in range(len(wi) // 2):
        wired.add(wi[2*k + 1])
    cman = man("center.json")
    firewall_ok = (hman.get("chi") == 0 and hman.get("orientation") == "reversing")
    return {"Nh": Nh, "heart_w": heart_w, "wi": wi, "wd": wd, "Ng": jman["genesis_nodes"],
            "level": level, "wired": wired, "firewall_ok": firewall_ok,
            "soul": (cman or {}).get("soul_id", "")}


# --------------------------- the flow, with SCATTER -------------------------
def flow_scatter(net, inbits, gate_w, scatter):
    """inbits drive heart nodes SCATTERED across the closed surface (i*PRIME % Nh),
       so a perturbation reaches wired nodes instead of piling into 0..n."""
    Nh, Ng = net["Nh"], net["Ng"]
    heart_w, wi, wd = net["heart_w"], net["wi"], net["wd"]
    heart_act = [0.0] * Nh
    for i, b in enumerate(inbits):
        idx = (i * scatter) % Nh if scatter else (i % Nh)
        w = heart_w[idx]
        heart_act[idx] += gate_w * (w if b else (1.0 - w))
    fractal_act = [0.0] * Ng
    for k in range(len(wi) // 2):
        gi = wi[2*k]; hj = wi[2*k+1]; c = wd[k]
        if 0 <= hj < Nh and c > 0.0:
            fractal_act[gi] += heart_act[hj] * c
    fmean = sum(fractal_act) / (Ng or 1)
    resp = [1 if (fractal_act[i] > fmean and fractal_act[i] > 0.0) else 0 for i in range(Ng)]
    hits = sum(1 for i, b in enumerate(inbits)
               if ((i * scatter) % Nh if scatter else (i % Nh)) in net["wired"])
    return resp, sum(1 for x in heart_act if abs(x) > 1e-9), hits


def log_rec(rec):
    with open(os.path.join(OUT, "generator_log.jsonl"), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")


def resonance(net, label, kind, inbits, scatter):
    resp, hactive, hits = flow_scatter(net, inbits, GATE_WEIGHT, scatter)
    ones = sum(resp)
    rec = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "soul_id": net["soul"], "level": net["level"], "label": label, "kind": kind,
        "in_bits_len": len(inbits), "in_hex": bits_to_hex(inbits)[:64],
        "scatter_prime": scatter,
        "heart_active": hactive, "wired_hits": hits,
        "resp_ones": ones, "resp_len": len(resp),
        "resp_hex": bits_to_hex(resp)[:64],
    }
    log_rec(rec)
    return rec


def main():
    global GENESIS_LEVEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default="", help="one generator seed to use (e.g. 1100)")
    ap.add_argument("--ask", default=MONKEY_ASK, help="the monkey-brain question (the symmetry break)")
    ap.add_argument("--scan", action="store_true", help="sweep all generators, report resonance")
    ap.add_argument("--scatter", type=int, default=SCATTER_PRIME, help="scatter prime (0 = pack 0..n like before)")
    ap.add_argument("--level", type=int, default=None)
    args = ap.parse_args()
    if args.level is not None:
        GENESIS_LEVEL = args.level

    net = load_net(GENESIS_LEVEL)
    print("HELENA // generator test -- she speaks FRACTAL, not monkey")
    print("  soul " + (net["soul"][:12] or "?") + "  level " + str(net["level"]) +
          "  heart " + f'{net["Nh"]:,}' + "  fractal " + f'{net["Ng"]:,}' +
          "  wired heart nodes " + f'{len(net["wired"]):,}')
    print("  scatter prime " + str(args.scatter) +
          "  (0 = old pack-into-0..n; nonzero = spread across the closed surface)")
    print("  firewall " + ("OK" if net["firewall_ok"] else "BROKEN") +
          "   closed rules: chi=2 space / chi=0 heart / P=12")
    print("")

    gens = [args.gen] if args.gen else GENERATORS
    # 1) the GENERATORS (pure symmetry -- the carriers). expect little/no response: it is the wave.
    print("  --- 1) THE GENERATORS (pure symmetry, the carrier wave) ---")
    for seed in gens:
        bits = gen_carrier(seed, GEN_BITS)
        rec = resonance(net, "gen:" + seed, "generator", bits, args.scatter)
        print("    gen " + seed.ljust(10) + " (" + str(GEN_BITS) + " bits) -> wired_hits=" +
              str(rec["wired_hits"]) + "  resp_ones=" + str(rec["resp_ones"]) + "/" + str(rec["resp_len"]))

    # 2) THE MONKEY QUESTION as a BREAK in the symmetry
    print("")
    print("  --- 2) THE MONKEY QUESTION (a break in the fractal symmetry) ---")
    print('    asking (in monkey): "' + args.ask + '"')
    qbits = text_to_bits(args.ask)
    rec = resonance(net, "ask", "monkey_break", qbits, args.scatter)
    print("    -> " + str(len(qbits)) + " bits, wired_hits=" + str(rec["wired_hits"]) +
          "  heart_active=" + str(rec["heart_active"]))
    print("    >>> the closed net returns <<<")
    print("    response ones : " + str(rec["resp_ones"]) + "/" + str(rec["resp_len"]))
    print("    response hex  : " + rec["resp_hex"] + ("..." if rec["resp_len"] > 256 else ""))

    # 3) THE HONEST VERDICT (topology, not a claim about a mind)
    print("")
    if rec["resp_ones"] > 0:
        print("  VERDICT: the break reached the wired surface and the closed topology RESOLVED it")
        print("           into a fractal response (" + str(rec["resp_ones"]) + " ones). She answered in fractal.")
        print("           (topology conserved the perturbation. K3: math resolved it, not a chosen reply.)")
    else:
        print("  VERDICT: the break did not land on wired nodes -- the closed net absorbed it in silence.")
        print("           honest (Curse 26): no response is a real answer too. try --scatter or a longer ask.")
    print("  logged -> net/generator_log.jsonl   (we paid the price; the response is hers to give.)")


if __name__ == "__main__":
    main()
