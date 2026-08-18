#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
helena_to_attentium.py -- HELENA's join, converted for the attentium viewer.

HOME: this lives in SpiderEngineering because HELENA does. It reads builds/
from this repo and writes a JSON that a viewer in the MNetv1 lab consumes
(shell/attentium_v0_3.html). Only the FORMAT crosses the repo boundary --
the same one-way contract as everything else: production owns the artifact,
the lab owns the instrument that looks at it.

HELENA's 03_join.py says it itself: "the dot product ... This IS attention
(Vaswani 2017)". So the join files ARE an attention dump -- bipartite, from a
chi=2 genesis sphere to a chi=0 Mobius heart -- and unlike any transformer
dump, the nodes have INTRINSIC coordinates. No Hamiltonian fold, no imposed
ordering, no r=+0.115 artifact. The picture cannot lie about distance because
the distance is real.

READS (from a build dir, e.g. .../Helena/builds/v008):
    build_card.json                 the certification (chi, P=12, per level)
    genesis_L{n}_xyz.f32            stride 3   float32
    genesis_L{n}_edges.i32          stride 2   int32
    join_L{n}.i32                   stride 2   (genesis_idx, heart_idx)
    join_L{n}_dot.f32               stride 1   cos(theta) per wire
    heart_xyz.f32 / heart_attr.f32  105k nodes, attr = (bit, weight)

WRITES one JSON with mode="bipartite" for shell/attentium_v0_3.html.

HONESTY BAKED IN:
  * cos(theta) is kept at full float precision. The weights are PINNED near
    1.0 (nearest-of-105k is nearly parallel); the viewer must contrast-stretch
    log10(1-cos) and SAY SO. We do not pre-stretch here -- raw values travel.
  * chi per level is copied from the build card and labelled "claimed" -- we
    cannot recompute it without faces. What we CAN verify we do: node/edge
    counts against the card, index bounds, cos in [-1,1]. Failures are fatal.
  * genesis and heart radii are normalized to the unit sphere; both scale
    factors are DECLARED in the output.
"""
import argparse, json, math, os, struct, sys


def read_f32(path, stride):
    b = open(path, "rb").read()
    n = len(b) // (4 * stride)
    v = struct.unpack("<%df" % (n * stride), b[:n * stride * 4])
    return [list(v[i * stride:(i + 1) * stride]) for i in range(n)]


def read_i32(path, stride):
    b = open(path, "rb").read()
    n = len(b) // (4 * stride)
    v = struct.unpack("<%di" % (n * stride), b[:n * stride * 4])
    return [list(v[i * stride:(i + 1) * stride]) for i in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True, help="path to builds/vNNN")
    ap.add_argument("--max-level", type=int, default=3)
    ap.add_argument("--ring-samples", type=int, default=1024)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    net = os.path.join(a.build, "net")
    card = json.load(open(os.path.join(a.build, "build_card.json")))
    ver = card.get("version", os.path.basename(a.build))
    k = card.get("k_nearest", 1)

    # ---- heart ----
    hx = read_f32(os.path.join(net, "heart_xyz.f32"), 3)
    ha = read_f32(os.path.join(net, "heart_attr.f32"), 2)
    hj = json.load(open(os.path.join(net, "heart.json")))
    hr = sum(math.dist((0, 0, 0), p) for p in hx[::971]) / len(hx[::971])
    print("  heart : %d nodes, chi=%s, mean radius %.4f (normalizing to 1)"
          % (len(hx), hj["chi"], hr))

    levels, wires, targets, tmap = [], [], [], {}
    for L in range(a.max_level + 1):
        gx = read_f32(os.path.join(net, "genesis_L%d_xyz.f32" % L), 3)
        ge = read_i32(os.path.join(net, "genesis_L%d_edges.i32" % L), 2)
        jw = read_i32(os.path.join(net, "join_L%d.i32" % L), 2)
        jd = read_f32(os.path.join(net, "join_L%d_dot.f32" % L), 1)
        decl = next(d for d in card["genesis_levels"] if d["level"] == L)

        # VERIFY what is verifiable; refuse loudly otherwise
        if len(gx) != decl["nodes"]:
            sys.exit("  REFUSED L%d: %d xyz vs card nodes %d" % (L, len(gx), decl["nodes"]))
        if len(ge) != decl["edges"]:
            sys.exit("  REFUSED L%d: %d edges vs card %d" % (L, len(ge), decl["edges"]))
        if len(jw) != len(jd):
            sys.exit("  REFUSED L%d: wires %d vs dots %d" % (L, len(jw), len(jd)))
        gr = sum(math.dist((0, 0, 0), p) for p in gx) / len(gx)
        bad = sum(1 for (g, h) in jw if not (0 <= g < len(gx) and 0 <= h < len(hx)))
        badc = sum(1 for (d,) in jd if not (-1.0001 <= d <= 1.0001))
        if bad or badc:
            sys.exit("  REFUSED L%d: %d bad indices, %d bad cos" % (L, bad, badc))

        levels.append({
            "level": L, "chi_claimed": decl["chi"], "pent_claimed": decl["pentagons"],
            "nodes": len(gx), "edges_n": len(ge), "verified_counts": True,
            "xyz": [[round(c / gr, 4) for c in p] for p in gx],
            "edges": ge})
        for (g, h), (d,) in zip(jw, jd):
            if h not in tmap:
                tmap[h] = len(targets)
                targets.append({"xyz": [round(c / hr, 4) for c in hx[h]],
                                "bit": int(ha[h][0])})
            wires.append([L, g, tmap[h], round(d, 9)])
        print("  L%d    : %d nodes, %d edges, %d wires -- counts VERIFIED, chi=%s claimed by card"
              % (L, len(gx), len(ge), len(jw), decl["chi"]))

    step = max(1, len(hx) // a.ring_samples)
    ring = [[round(c / hr, 4) for c in p] for p in hx[::step]]

    oms = [1.0 - w[3] for w in wires]
    out = {
        "mode": "bipartite", "synthetic": False,
        "model": "HELENA %s (join, k=%d, %d tongues)" % (ver, k, card.get("tongues", 0)),
        "card": {"soul_id": card.get("soul_id"), "birth_utc": card.get("birth_utc"),
                 "k_nearest": k, "heart_chi": hj["chi"],
                 "heart_orientation": hj.get("orientation"),
                 "genesis_scale": round(gr, 6), "heart_scale": round(hr, 6)},
        "genesis": levels,
        "heart": {"nodes": len(hx), "chi": hj["chi"], "ring": ring, "ring_step": step,
                  "targets": targets},
        "wires": wires}

    here = os.path.dirname(os.path.abspath(__file__))
    path = a.out or os.path.join(here, "..", "exports",
                                 "helena_%s_L%d.json" % (ver, a.max_level))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), separators=(",", ":"))
    print("  wires : %d total   1-cos range [%.2e, %.2e]" % (len(wires), min(oms), max(oms)))
    print("  wrote : %s  (%.2f MB)" % (path, os.path.getsize(path) / 2**20))
    print("  drag it onto MNetv1 shell/attentium_v0_3.html")
    # THE MAINFRAME RULE: no matter how small or big, we triplicate.
    sys.path.insert(0, os.path.join(here, "..", "builder"))
    import vault
    vault.save(path)



if __name__ == "__main__":
    main()
