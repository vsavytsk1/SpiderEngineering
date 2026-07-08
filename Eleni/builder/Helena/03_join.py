#!/usr/bin/env python3
# ============================================================================
#  03_join.py  --  HELENA, part 3 of 4:  THE JOIN  (the transformer)
# ----------------------------------------------------------------------------
#  Connect the genesis space to the heart. For every genesis node we find its
#  strongest heart connection by the DOT PRODUCT  a . b = cos(theta)  (both are
#  ~unit vectors on the sphere). The dot product is the cheapest "equals sign
#  between two concepts" -- proven by permutation. This IS attention (Vaswani
#  2017: attention = scaled dot product). Pure graph magic: new edges.
#
#  THE WORKFLOW Vlad asked for:  fractalize 1 -> JOIN -> fractalize 2 -> JOIN
#  -> store all.  So this reads ONE genesis level file + the heart file and
#  writes a join file tagged with that level. Run it once per level; keep them
#  all. Each join is independent and reproducible.
#
#      1) py -3 01_genesis.py   (LEVEL = 1)      -> net/genesis_L1_*
#      2) py -3 03_join.py      (GENESIS_LEVEL=1)-> net/join_L1.*
#      3) py -3 01_genesis.py   (LEVEL = 2)      -> net/genesis_L2_*
#      4) py -3 03_join.py      (GENESIS_LEVEL=2)-> net/join_L2.*   ... store all
#
#  STANDALONE. Stdlib only; numpy used ONLY if present (chunked matmul, fast).
#  Pure-python fallback is the same math, just slower (honest). Copy anywhere:
#
#      py -3 03_join.py
#
#  STREAMS the wire list to disk in BATCHES -> RAM stays flat even for millions
#  of genesis nodes. It will not crash on a big level; it eats disk + time.
#
#  >>> GPU <<<  the ONE hot loop is marked below. On the NVIDIA run you replace
#  it with a single cupy/torch matmul  G(chunk x 3) @ H.T(3 x Nh) -> argmax.
#  Same math, same result, ~100x faster. Everything else stays identical.
# ============================================================================
#
#  THE COST  (wires = number of genesis nodes; each wire = 1 nearest heart node)
#  work = genesis_nodes * heart_nodes dot products (this is the 1T-style term)
#
#   genesis L | genesis nodes | dots vs 105k heart | numpy time* | join file
#   ----------+---------------+--------------------+-------------+----------
#          0  |          12   |         1.3 M      |   instant   |    96 B
#          3  |         642   |          67 M      |   ~0.1 s    |   7.5 KB
#          5  |      10,242   |         1.1 B      |   ~2 s      |   120 KB
#          6  |      40,962   |         4.3 B      |   ~8 s      |   480 KB
#          8  |     655,362   |          69 B      |   ~2 min    |   7.7 MB
#         10  |  10,485,762   |         1.1 T      |  ~30 min    |   126 MB   (the 1T neighbourhood)
#  *rough, RTX 3060 laptop w/ numpy CPU BLAS; a real GPU matmul is far faster.
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
GENESIS_LEVEL = 2          # which net/genesis_L{N}_* to join (must exist already)
HEART_MANIFEST = "heart.json"   # the heart file made by 02_heart.py
K_NEAREST     = 1          # how many nearest heart nodes per genesis node (1 = sparse)
OUT_DIR       = "net"      # artifacts folder
BATCH         = 200000     # wires per disk flush (RAM stays flat)
CHUNK         = 4096       # genesis rows per matmul chunk (numpy path). tune to your RAM.
# ----------------------------------------------------------------------------

import os, sys, json, math, time
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
# optional pipe overrides (env). the SET-BY-HAND vars above stay the default when unset.
GENESIS_LEVEL = int(os.environ.get("HELENA_GENESIS_LEVEL", GENESIS_LEVEL))
K_NEAREST = int(os.environ.get("HELENA_K", K_NEAREST))   # more nearest heart nodes = denser data
OUT = os.environ.get("HELENA_OUT") or os.path.join(HERE, OUT_DIR)

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:
    np = None
    HAVE_NUMPY = False


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def load_manifest(name):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        sys.exit("ERROR: missing " + p + " -- run the earlier script first.")
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def read_xyz(fname, stride=3):
    p = os.path.join(OUT, fname)
    if not os.path.exists(p):
        sys.exit("ERROR: missing " + p)
    if HAVE_NUMPY:
        return np.fromfile(p, dtype=np.float32).reshape(-1, stride)
    # pure-python: list of tuples
    a = array("f")
    with open(p, "rb") as fh:
        a.fromfile(fh, os.path.getsize(p) // 4)
    return [tuple(a[i:i+stride]) for i in range(0, len(a), stride)]


def main():
    gman = load_manifest("genesis_L" + str(GENESIS_LEVEL) + ".json")
    hman = load_manifest(HEART_MANIFEST)
    t0 = time.time()
    print("HELENA / part 3 / THE JOIN  (transformer)  (" +
          ("numpy" if HAVE_NUMPY else "pure-python") + ")")
    print("  genesis L" + str(GENESIS_LEVEL) + " : " + f'{gman["nodes"]:,}' + " nodes")
    print("  heart          : " + f'{hman["nodes"]:,}' + " nodes")
    print("  op  a.b = cos(theta)  (dot product = the cheapest equals; K=" + str(K_NEAREST) + ")")

    G = read_xyz(gman["xyz_file"], 3)     # genesis nodes
    H = read_xyz(hman["xyz_file"], 3)     # heart nodes
    Ng = gman["nodes"]
    Nh = hman["nodes"]

    out_path = os.path.join(OUT, "join_L" + str(GENESIS_LEVEL) + ".i32")
    # each wire row: [genesis_idx, heart_idx] (K per genesis node). dot stored separately as f32.
    dot_path = os.path.join(OUT, "join_L" + str(GENESIS_LEVEL) + "_dot.f32")
    fw = open(out_path, "wb")
    fd = open(dot_path, "wb")
    wbuf = array("i"); dbuf = array("f")
    wires = 0

    if HAVE_NUMPY:
        # normalize to true unit vectors so dot == cos exactly
        Gn = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-12)
        Hn = H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-12)
        HnT = Hn.T.copy()                                  # 3 x Nh
        for s in range(0, Ng, CHUNK):
            gchunk = Gn[s:s+CHUNK]                          # (c x 3)
            # >>> GPU <<<  this matmul is the whole transformer for the chunk.
            #             swap for cupy/torch:  sims = gchunk @ HnT  on the 3060.
            sims = gchunk @ HnT                             # (c x Nh) cos-similarities
            if K_NEAREST == 1:
                idx = np.argmax(sims, axis=1)              # nearest heart node
                val = sims[np.arange(sims.shape[0]), idx]
                for r in range(gchunk.shape[0]):
                    wbuf.append(s + r); wbuf.append(int(idx[r]))
                    dbuf.append(float(val[r]))
                    wires += 1
                    if len(wbuf) >= BATCH * 2:
                        wbuf.tofile(fw); wbuf = array("i")
                        dbuf.tofile(fd); dbuf = array("f")
            else:
                k = min(K_NEAREST, Nh)
                part = np.argpartition(-sims, k-1, axis=1)[:, :k]
                for r in range(gchunk.shape[0]):
                    order = part[r][np.argsort(-sims[r, part[r]])]
                    for hj in order:
                        wbuf.append(s + r); wbuf.append(int(hj))
                        dbuf.append(float(sims[r, hj]))
                        wires += 1
                    if len(wbuf) >= BATCH * 2:
                        wbuf.tofile(fw); wbuf = array("i")
                        dbuf.tofile(fd); dbuf = array("f")
            if s % (CHUNK * 20) == 0:
                print("    ... " + f"{min(s+CHUNK, Ng):,}" + " / " + f"{Ng:,}" + " genesis nodes")
    else:
        # pure-python: same math, one nearest per genesis node (K=1 only, honest + slow)
        def norm(v):
            L = math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]) or 1.0
            return (v[0]/L, v[1]/L, v[2]/L)
        Hn = [norm(h) for h in H]
        for gi in range(Ng):
            gx, gy, gz = norm(G[gi])
            best = -2.0; bj = 0
            # >>> GPU <<<  this inner loop is what the matmul replaces.
            for hj in range(Nh):
                hx, hy, hz = Hn[hj]
                d = gx*hx + gy*hy + gz*hz
                if d > best:
                    best = d; bj = hj
            wbuf.append(gi); wbuf.append(bj); dbuf.append(best); wires += 1
            if len(wbuf) >= BATCH * 2:
                wbuf.tofile(fw); wbuf = array("i")
                dbuf.tofile(fd); dbuf = array("f")
            if gi % 5000 == 0:
                print("    ... " + f"{gi:,}" + " / " + f"{Ng:,}")

    if wbuf: wbuf.tofile(fw)
    if dbuf: dbuf.tofile(fd)
    fw.close(); fd.close()

    print("  wrote " + os.path.basename(out_path) + "  (" + human(os.path.getsize(out_path)) +
          ")  " + f"{wires:,}" + " wires [genesis->heart]")
    print("  wrote " + os.path.basename(dot_path) + "  (" + human(os.path.getsize(dot_path)) +
          ")  cos(theta) per wire")

    manifest = {
        "part": "join",
        "genesis_level": GENESIS_LEVEL,
        "genesis_nodes": Ng,
        "heart_nodes": Nh,
        "k_nearest": K_NEAREST,
        "wires": wires,
        "op": "dot product a.b = cos(theta) (nearest heart node per genesis node)",
        "wire_file": os.path.basename(out_path),
        "wire_dtype": "int32", "wire_stride": 2, "wire_fields": ["genesis_idx", "heart_idx"],
        "dot_file": os.path.basename(dot_path),
        "dot_dtype": "float32", "dot_stride": 1,
        "seconds": round(time.time() - t0, 3),
    }
    man_path = os.path.join(OUT, "join_L" + str(GENESIS_LEVEL) + ".json")
    with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=2) + "\n")
    print("  wrote " + os.path.basename(man_path))
    print("  done in " + str(manifest["seconds"]) + "s.  the space is joined to the heart.")


if __name__ == "__main__":
    main()
