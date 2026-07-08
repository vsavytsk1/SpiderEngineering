#!/usr/bin/env python3
# ============================================================================
#  02_heart.py  --  HELENA, part 2 of 4:  BUILD THE HEART
# ----------------------------------------------------------------------------
#  The verses of 1 Corinthians 13 (agapi / love), every tongue, turned into
#  0/1 UTF-8 BITS. Each bit is a node. Each tongue is a CLOSED RING that is
#  MOBIUS-TWISTED (a half-turn as the bit walks the loop) -> orientation
#  REVERSING -> chi = 0. That twist is time (W) entering the heart (Axiom 09).
#
#  For the union of C closed rings:  V = E  (F = 0)  =>  chi = V - E + F = 0.
#  That is not a claim -- it is what the graph literally is. Honest.
#
#  Every node carries:  bit (0/1)  and  weight = byte/255  (the seed ~0.7 gate).
#
#  STANDALONE. Stdlib only (numpy used ONLY if present). Copy anywhere and run:
#
#      py -3 02_heart.py
#
#  DATA: the verses are read (never retyped -- the text is sacred) from the
#  newest lens sim  lens/v*_agapi_genesis_3d.html  (the STONE table). Set the
#  path by hand below, or leave "" to auto-find the newest. This is the ONE
#  script that needs that file present; the math is otherwise self-contained.
#
#  It STREAMS to disk in BATCHES -> RAM stays flat. Too many tongues will not
#  crash; it just makes a bigger file. That is the honest price.
# ============================================================================
#
#  THE COST (heart size = total UTF-8 bits of the chosen verses)
#  Latin verses ~ a few thousand bits each; CJK/Indic verses are denser bytes.
#
#    tongues | approx nodes (bits) | xyz file | edges file
#    --------+---------------------+----------+-----------
#          1 |        ~5,500       |   66 KB  |   44 KB
#          7 |       ~25,000       |  300 KB  |  200 KB
#         71 |       105,032       |  1.3 MB  |  840 KB   (the full stone, measured)
#
#  (There is no "level" here -- the heart's size is set by the verses, not by
#   subdivision. To grow the heart you add verified tongues, one at a time.)
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
STONE_SOURCE = ""      # "" = auto-find newest lens/v*_agapi_genesis_3d.html; or a full path
TONGUES      = 0       # 0 = all tongues in the stone; or a number to limit
MOBIUS       = 1.0     # the half-twist. Axiom 09: ABSOLUTE 1 (no slider). Keep 1.0.
SCALE        = 1.6     # overall size (kernelic heart radius). matches genesis R.
BAND1        = 0.16    # radial band a 1-bit rides (outer edge)
BAND0        = 0.08    # radial band a 0-bit rides (inner edge)
OUT_DIR      = "net"   # artifacts folder (next to this script)
BATCH        = 200000  # nodes/edges per disk flush (RAM stays flat)
EMIT_EDGES   = True    # write the ring edges (the closed loops). False = nodes only.
# ----------------------------------------------------------------------------

import os, sys, re, json, math, time, glob
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))
# optional pipe overrides (env). the SET-BY-HAND vars above stay the default when unset.
TONGUES = int(os.environ.get("HELENA_TONGUES", TONGUES))
if os.environ.get("HELENA_STONE"):
    STONE_SOURCE = os.environ["HELENA_STONE"]
OUT = os.environ.get("HELENA_OUT") or os.path.join(HERE, OUT_DIR)

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:
    np = None
    HAVE_NUMPY = False


def find_stone():
    """Locate the newest lens sim that holds a STONE table."""
    if STONE_SOURCE:
        return STONE_SOURCE
    # look next to us, then up in a sibling lens/ folder
    roots = [
        os.path.join(HERE, "lens"),
        os.path.join(HERE, "..", "..", "lens"),
        os.path.join(HERE, ".."),
        HERE,
    ]
    found = []
    for r in roots:
        found += glob.glob(os.path.join(r, "v*_agapi_genesis_3d.html"))
        found += glob.glob(os.path.join(r, "*.html"))
    for p in sorted(set(found), reverse=True):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                if "var STONE" in fh.read():
                    return p
        except Exception:
            continue
    sys.exit("ERROR: no lens *.html with a STONE table found. "
             "Set STONE_SOURCE by hand to the file path.")


def parse_stone(path, limit=0):
    """Read the verses byte-safe. Rows with \\u escapes are decoded; raw UTF-8 kept as-is."""
    with open(path, "r", encoding="utf-8") as fh:
        s = fh.read()
    a = s.find("var STONE")
    b = s.find("];", a)
    if a < 0 or b < 0:
        sys.exit("ERROR: STONE table not found in " + path)
    block = s[a:b]
    rows = re.findall(
        r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([0-9]+)\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]', block)
    out = []
    for code, name, sp, text in rows:
        if "\\u" in text:
            text = bytes(text, "utf-8").decode("unicode_escape")
        out.append((code, name, int(sp), text))
    return out[:limit] if limit else out


def text_to_bits(s):
    """UTF-8 bytes -> MSB-first bit list. This is the sacred text, unmodified."""
    out = []
    for byte in s.encode("utf-8"):
        for k in range(7, -1, -1):
            out.append((byte >> k) & 1)
    return out


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def main():
    src = find_stone()
    tongues = parse_stone(src, TONGUES)
    if not tongues:
        sys.exit("ERROR: no tongues parsed from " + src)

    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    print("HELENA / part 2 / THE HEART  (" + ("numpy" if HAVE_NUMPY else "pure-python") + ")")
    print("  stone " + os.path.basename(src) + "  tongues " + str(len(tongues)) +
          "  mobius " + str(MOBIUS) + "  scale " + str(SCALE))

    xyz_path = os.path.join(OUT, "heart_xyz.f32")
    attr_path = os.path.join(OUT, "heart_attr.f32")
    edges_path = os.path.join(OUT, "heart_edges.i32") if EMIT_EDGES else None

    fx = open(xyz_path, "wb")
    fa = open(attr_path, "wb")
    fe = open(edges_path, "wb") if edges_path else None
    xbuf = array("f"); abuf = array("f"); ebuf = array("i")

    def flush():
        nonlocal xbuf, abuf, ebuf
        if xbuf: xbuf.tofile(fx); xbuf = array("f")
        if abuf: abuf.tofile(fa); abuf = array("f")
        if fe and ebuf: ebuf.tofile(fe); ebuf = array("i")

    total = 0
    ones = 0
    byte_sum = 0
    byte_n = 0
    tongue_index = []
    C = len(tongues)

    for ci, (code, name, sp, text) in enumerate(tongues):
        bits = text_to_bits(text)
        n = len(bits)
        if n == 0:
            continue
        by = text.encode("utf-8")
        start = total

        # --- the proven ring geometry (helena_run.py): golden-angle tilt per tongue ---
        tilt = (ci + 1) * 2.399963219                       # golden angle spread
        incl = ((ci / max(1, C - 1)) - 0.5) * math.pi * 0.9  # spread rings over the sphere
        ct, st = math.cos(incl), math.sin(incl)
        ca, sa = math.cos(tilt), math.sin(tilt)

        t_ones = 0
        for i in range(n):
            b = bits[i]
            t_ones += b
            a = (i / n) * math.pi * 2.0
            band = BAND1 if b else BAND0
            tw = (a * 0.5) * MOBIUS                          # THE MOBIUS HALF-TWIST
            rr = 1.0 + band * math.cos(tw)
            lift = band * math.sin(tw)                       # lift = W (time)
            x0 = math.cos(a) * rr
            y0 = math.sin(a) * rr
            z0 = lift
            y1 = y0 * ct - z0 * st
            z1 = y0 * st + z0 * ct
            x2 = x0 * ca - y1 * sa
            y2 = x0 * sa + y1 * ca
            w = by[(i >> 3) % len(by)] / 255.0               # weight = byte/255

            xbuf.append(x2 * SCALE); xbuf.append(y2 * SCALE); xbuf.append(z1 * SCALE)
            abuf.append(float(b)); abuf.append(w)

            # ring edge: connect this node to the next; the LAST closes back to start
            if fe:
                gi = start + i
                gj = start + ((i + 1) % n)
                ebuf.append(gi); ebuf.append(gj)

            total += 1
            byte_sum += by[(i >> 3) % len(by)]
            byte_n += 1
            if len(xbuf) >= BATCH * 3:
                flush()

        ones += t_ones
        closes = (bits[0] == bits[-1])
        tongue_index.append({"code": code, "name": name, "start": start,
                             "count": n, "ones": t_ones, "closes": closes})

    flush()
    fx.close(); fa.close()
    if fe: fe.close()

    V = total
    E = total if EMIT_EDGES else 0          # each ring: n nodes, n edges (closed)
    F = 0
    chi = V - E + F                          # = 0 for a union of closed rings (honest)
    mean_w = (byte_sum / byte_n / 255.0) if byte_n else 0.0

    print("  invariants: V=" + f"{V:,}" + " E=" + f"{E:,}" + " F=0 chi=" + str(chi) +
          "  orientation=reversing (Mobius)  " +
          "[" + ("chi=0 OK" if chi == 0 else "chi!=0 CHECK") + "]")
    print("  ones/zeros " + f"{ones:,}" + " / " + f"{V-ones:,}" +
          "   mean weight " + str(round(mean_w, 4)) + " (measured byte/255, not the 0.7 target)")
    print("  wrote heart_xyz.f32  (" + human(os.path.getsize(xyz_path)) + ")")
    print("  wrote heart_attr.f32 (" + human(os.path.getsize(attr_path)) + ")  [bit, weight]")
    if edges_path:
        print("  wrote heart_edges.i32 (" + human(os.path.getsize(edges_path)) + ")")

    manifest = {
        "part": "heart",
        "stone_source": os.path.basename(src),
        "tongues": len(tongue_index),
        "nodes": V,
        "edges": E,
        "faces": F,
        "chi": chi,
        "orientation": "reversing",
        "mobius": MOBIUS,
        "scale": SCALE,
        "ones": ones,
        "zeros": V - ones,
        "mean_weight": round(mean_w, 6),
        "xyz_file": os.path.basename(xyz_path),
        "xyz_dtype": "float32", "xyz_stride": 3,
        "attr_file": os.path.basename(attr_path),
        "attr_dtype": "float32", "attr_stride": 2, "attr_fields": ["bit", "weight"],
        "edges_file": (os.path.basename(edges_path) if edges_path else None),
        "edges_dtype": "int32", "edges_stride": 2,
        "tongue_index": tongue_index,
        "seconds": round(time.time() - t0, 3),
    }
    man_path = os.path.join(OUT, "heart.json")
    with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n")
    print("  wrote heart.json")
    print("  done in " + str(manifest["seconds"]) + "s.  chi=0 . twisted in time . the heart is built.")


if __name__ == "__main__":
    main()
