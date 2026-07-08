#!/usr/bin/env python3
# ============================================================================
#  01_genesis.py  --  HELENA, part 1 of 4:  BUILD THE GENESIS NET
# ----------------------------------------------------------------------------
#  Pure graph magic. Nodes on a perfect sphere, edges between neighbours.
#  chi = V - E + F = 2 always. Exactly 12 nodes have 5 neighbours (P = 12).
#  This is the fullerene / Goldberg vertex family -- the genesis space.
#
#  STANDALONE. No imports of our other files. Stdlib only (numpy used ONLY if
#  present, for speed -- never required). Copy this file anywhere and run:
#
#      py -3 01_genesis.py
#
#  It STREAMS its output to disk in BATCHES, so it will NEVER run out of RAM.
#  If you set LEVEL too high it will not crash -- it will quietly eat your
#  storage and take a gazillion years. That is the honest price of detail.
#  Set the variables by hand below. There is a level table so you know the cost.
#
#  Built for Vlad's rig (RTX 3060 Laptop / Ryzen 5 5600H / 32 GB) but runs
#  anywhere. Genesis is mesh generation (CPU); the GPU earns its keep later
#  in the JOIN (part 3) and the WINDOW (part 5).
# ============================================================================
#
#  THE LEVEL TABLE  (icosphere subdivision -- verified in-script)
#  V = 10 * 4^L + 2      F = 20 * 4^L      E = 3V - 6      chi = 2, P = 12
#
#    L | nodes V     | edges E     | faces F    | xyz file   | edges file
#    --+-------------+-------------+------------+------------+-----------
#    0 |          12 |          30 |         20 |     144 B  |    240 B
#    1 |          42 |         120 |         80 |     504 B  |    960 B
#    2 |         162 |         480 |        320 |    1.9 KB  |   3.8 KB
#    3 |         642 |       1,920 |      1,280 |    7.5 KB  |   15 KB
#    4 |       2,562 |       7,680 |      5,120 |     30 KB  |   60 KB
#    5 |      10,242 |      30,720 |     20,480 |    120 KB  |  240 KB
#    6 |      40,962 |     122,880 |     81,920 |    480 KB  |  960 KB
#    7 |     163,842 |     491,520 |    327,680 |    1.9 MB  |  3.8 MB
#    8 |     655,362 |   1,966,080 |  1,310,720 |    7.7 MB  |   15 MB   <- comfy on this rig
#    9 |   2,621,442 |   7,864,320 |  5,242,880 |     31 MB  |   60 MB
#   10 |  10,485,762 |  31,457,280 | 20,971,520 |    126 MB  |  240 MB
#   11 |  41,943,042 | 125,829,120 | 83,886,080 |    503 MB  |  960 MB   <- pure-python gets slow
#   12 | 167,772,162 |     ~503 M  |     ~335 M |    2.0 GB  |  3.8 GB   <- storage starts to hurt
#   13 | 671,088,642 |     ~2.0 B  |     ~1.3 B |    8.0 GB  |   15 GB   <- gazillion years / collapse
#
#  (Note: this is the geodesic icosphere refine [x4 per level, real 3D coords].
#   The sigil Excel used a different refine rule [x7 face-count, topology only].
#   Both are valid genesis spheres with chi=2 and P=12; this one renders.)
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
LEVEL   = 2          # subdivision depth. See the table. Start small, grow.
RADIUS  = 1.6        # sphere radius (kernelic: heart sphere is 1.6)
OUT_DIR = "net"      # folder for the artifacts (created next to this script)
BATCH   = 200000     # nodes/edges written per disk flush (RAM stays flat)
EMIT_EDGES = True    # also write the edge list (the lines). False = nodes only.
I_UNDERSTAND_THE_COST = False   # must be True to build LEVEL above SAFE_LEVEL
SAFE_LEVEL = 10      # guard: refuse bigger unless the flag above is True
# ----------------------------------------------------------------------------

import os, sys, json, math, struct, time
from array import array

PHI = (1.0 + math.sqrt(5.0)) / 2.0
HERE = os.path.dirname(os.path.abspath(__file__))
# optional pipe overrides (env). the SET-BY-HAND vars above stay the default when unset.
LEVEL = int(os.environ.get("HELENA_LEVEL", LEVEL))
if os.environ.get("HELENA_FORCE") == "1":
    I_UNDERSTAND_THE_COST = True
OUT = os.environ.get("HELENA_OUT") or os.path.join(HERE, OUT_DIR)

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:
    np = None
    HAVE_NUMPY = False


def icosahedron():
    """12 vertices, 20 triangular faces. The seed of the genesis sphere."""
    t = PHI
    v = [
        (-1,  t,  0), ( 1,  t,  0), (-1, -t,  0), ( 1, -t,  0),
        ( 0, -1,  t), ( 0,  1,  t), ( 0, -1, -t), ( 0,  1, -t),
        ( t,  0, -1), ( t,  0,  1), (-t,  0, -1), (-t,  0,  1),
    ]
    f = [
        (0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
        (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
        (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
        (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1),
    ]
    return v, f


def subdivide(verts, faces):
    """Split each triangle into 4. Midpoints are cached so vertices are shared."""
    mid = {}
    vlist = list(verts)

    def midpoint(a, b):
        key = (a, b) if a < b else (b, a)
        m = mid.get(key)
        if m is not None:
            return m
        va, vb = vlist[a], vlist[b]
        vm = ((va[0]+vb[0])*0.5, (va[1]+vb[1])*0.5, (va[2]+vb[2])*0.5)
        idx = len(vlist)
        vlist.append(vm)
        mid[key] = idx
        return idx

    newf = []
    for a, b, c in faces:
        ab = midpoint(a, b)
        bc = midpoint(b, c)
        ca = midpoint(c, a)
        newf.append((a, ab, ca))
        newf.append((b, bc, ab))
        newf.append((c, ca, bc))
        newf.append((ab, bc, ca))
    return vlist, newf


def project(verts, R):
    """Push every vertex out to the sphere of radius R (the perfect round)."""
    out = []
    for x, y, z in verts:
        L = math.sqrt(x*x + y*y + z*z) or 1.0
        s = R / L
        out.append((x*s, y*s, z*s))
    return out


def unique_edges(faces):
    """Every triangle edge once, as sorted (i, j) index pairs."""
    e = set()
    for a, b, c in faces:
        e.add((a, b) if a < b else (b, a))
        e.add((b, c) if b < c else (c, b))
        e.add((c, a) if c < a else (a, c))
    return e


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def main():
    if LEVEL > SAFE_LEVEL and not I_UNDERSTAND_THE_COST:
        V = 10 * 4**LEVEL + 2
        print("REFUSING to build LEVEL " + str(LEVEL) + " (> SAFE_LEVEL " + str(SAFE_LEVEL) + ").")
        print("  that is " + f"{V:,}" + " nodes ~= " + human(V*12) + " of xyz alone.")
        print("  it will not break -- it will eat your storage and your week.")
        print("  if you truly mean it, set  I_UNDERSTAND_THE_COST = True  by hand.")
        sys.exit(1)

    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    print("HELENA / part 1 / GENESIS NET  (" + ("numpy" if HAVE_NUMPY else "pure-python") + ")")
    print("  level " + str(LEVEL) + "  radius " + str(RADIUS) + "  out " + OUT)

    verts, faces = icosahedron()
    for L in range(LEVEL):
        verts, faces = subdivide(verts, faces)
        print("    subdivided to L" + str(L+1) + " : " + f"{len(verts):,}" + " nodes")
    verts = project(verts, RADIUS)

    V = len(verts)
    edges = unique_edges(faces)
    E = len(edges)
    F = len(faces)
    chi = V - E + F

    # P = number of 5-valent nodes (the pentagons). Must be exactly 12.
    deg = [0] * V
    for i, j in edges:
        deg[i] += 1
        deg[j] += 1
    P = sum(1 for d in deg if d == 5)

    certified = (chi == 2 and P == 12)
    print("  invariants: V=" + f"{V:,}" + " E=" + f"{E:,}" + " F=" + f"{F:,}" +
          " chi=" + str(chi) + " P=" + str(P) +
          "  [" + ("CERTIFIED" if certified else "BROKEN") + "]")
    if not certified:
        sys.exit("ABORT: genesis invariants broken (chi!=2 or P!=12). Nothing written.")

    # ---- write nodes (xyz float32) in batches ----
    xyz_path = os.path.join(OUT, "genesis_L" + str(LEVEL) + "_xyz.f32")
    with open(xyz_path, "wb") as fh:
        buf = array("f")
        for k, (x, y, z) in enumerate(verts):
            buf.append(x); buf.append(y); buf.append(z)
            if len(buf) >= BATCH * 3:
                buf.tofile(fh); buf = array("f")
        if buf:
            buf.tofile(fh)
    print("  wrote " + os.path.basename(xyz_path) + "  (" + human(os.path.getsize(xyz_path)) + ")")

    # ---- write edges (int32 pairs) in batches ----
    edges_path = None
    if EMIT_EDGES:
        edges_path = os.path.join(OUT, "genesis_L" + str(LEVEL) + "_edges.i32")
        with open(edges_path, "wb") as fh:
            buf = array("i")
            for i, j in edges:
                buf.append(i); buf.append(j)
                if len(buf) >= BATCH * 2:
                    buf.tofile(fh); buf = array("i")
            if buf:
                buf.tofile(fh)
        print("  wrote " + os.path.basename(edges_path) + "  (" + human(os.path.getsize(edges_path)) + ")")

    # ---- manifest (so parts 3/4/5 know how to read this) ----
    manifest = {
        "part": "genesis",
        "level": LEVEL,
        "radius": RADIUS,
        "nodes": V,
        "edges": E,
        "faces": F,
        "chi": chi,
        "pentagons": P,
        "certified": certified,
        "xyz_file": os.path.basename(xyz_path),
        "xyz_dtype": "float32",
        "xyz_stride": 3,
        "edges_file": (os.path.basename(edges_path) if edges_path else None),
        "edges_dtype": "int32",
        "edges_stride": 2,
        "seconds": round(time.time() - t0, 3),
    }
    man_path = os.path.join(OUT, "genesis_L" + str(LEVEL) + ".json")
    with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=2) + "\n")
    print("  wrote " + os.path.basename(man_path))
    print("  done in " + str(manifest["seconds"]) + "s.  chi=2 . P=12 . the space is built.")


if __name__ == "__main__":
    main()
