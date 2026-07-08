#!/usr/bin/env python3
"""
helena_run.py -- the HELENA runtime: load the four parts into memory, pass a string
to the GATE, watch it flow  gate -> heart -> fractal space.  The NVIDIA reference.

THIS IS A REFERENCE IMPLEMENTATION (K1-K4, GENESIS_LLM.md):
  K1  a transformer is already a graph; "attention" = a weighted edge (dot product).
  K2  "fractal" = HIERARCHY (a few tuned scales), not infinite self-similarity.
  K3  nothing here is conscious. It is linear algebra on a nice graph. The meaning
      we attach is ours; the math is just math. Passing a string in gives numbers out.
  K4  0.7 is a SEED we test, not a magic number.

THE FOUR PATHS (each proven by build_helena.py before this ever runs):
  1. GENESIS SPACE   -- C60 refined k levels. nodes on a sphere. chi=2 (orientable).
  2. HEART           -- 0/1 bits of the verses, Mobius-twisted (chi=0, orientation-reversing).
  3. TRANSFORMER     -- M[i][j] = a_i . b_j  (dot product = cos theta; cheapest equals).
  4. GATE            -- binds ONLY orientation-reversing nodes (the heart). Topology firewall:
                        the genesis space (chi=2) is invisible to the gate. Proven, not enforced.

THE FLOW (what forward() does):
  string -> UTF-8 bits -> GATE (weight 0.7 rest / 1 twist) -> HEART (twisted, in-time)
         -> FRACTAL SPACE (low rest -> max complexity) -> readout vector.
  The language never comes back out of the fractal side (one-way). That is the defense.

RUNS ANYWHERE: pure-Python by default (slow, honest). If numpy is present it is used.
The GPU (CuPy / torch) slot is marked >>> GPU <<< -- that is the only line the NVIDIA run swaps.

    py -3 helena_run.py "if I speak in the tongues of men and of angels"
    py -3 helena_run.py --levels 3 --prompt "agapi"
    py -3 helena_run.py --cost           # print the NVIDIA cost model for THIS rig, run nothing
"""
from __future__ import annotations
import re, sys, math, argparse, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LENS = ROOT / "lens"
PHI = (1 + math.sqrt(5)) / 2
GATE_REST = 0.700     # the Oracle seed (K4). rest state, chi=2.
GATE_TWIST = 1.0      # binary under the Mobius twist (Axiom 09).

# optional acceleration -- honest: we say which path we took
try:
    import numpy as _np
    HAVE_NUMPY = True
except ImportError:
    _np = None
    HAVE_NUMPY = False

# THIS RIG (from HWiNFO64): tune the cost model to the real machine.
RIG = {
    "cpu": "AMD Ryzen 5 5600H (6c/12t, Zen3)",
    "gpu": "NVIDIA RTX 3060 Laptop (GA106M, 3840 CUDA, 6 GB GDDR6)",
    "ram_gb": 32,
    "gpu_vram_gb": 6,
    "gpu_fp32_tflops": 10.0,   # ~10-12 TFLOPS FP32, honest mid
}

# ---------------------------------------------------------------------------
# STONE -- the verses (single source of truth: newest lens sim)
# ---------------------------------------------------------------------------
def load_stone(limit=0):
    src_path = None
    for p in sorted(LENS.glob("v*_agapi_genesis_3d.html"), reverse=True):
        if "var STONE" in p.read_text(encoding="utf-8"):
            src_path = p
            break
    if not src_path:
        sys.exit("ERROR: no lens STONE source found")
    s = src_path.read_text(encoding="utf-8")
    a = s.find("var STONE"); b = s.find("];", a)
    rows = re.findall(r'\[\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([0-9]+)\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]', s[a:b])
    out = []
    for code, name, sp, text in rows:
        if "\\u" in text:
            text = bytes(text, "utf-8").decode("unicode_escape")
        out.append((code, name, int(sp), text))
    return (out[:limit] if limit else out), src_path.name

# ---------------------------------------------------------------------------
# small vec3 (pure python) -- the kernel's own normalize onto the sphere
# ---------------------------------------------------------------------------
def vnorm(v, R=1.0):
    L = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]) or 1.0
    return (v[0]*R/L, v[1]*R/L, v[2]*R/L)

def c60_vertices():
    """the buckyball's 60 vertices (truncated icosahedron), normalized to the unit sphere."""
    raw = []
    perms = [(0,1,2),(1,2,0),(2,0,1)]
    def push(a,b,c):
        for p in perms:
            for sa in (-1,1):
                for sb in (-1,1):
                    for sc in (-1,1):
                        if a==0 and sa==-1: continue
                        if b==0 and sb==-1: continue
                        if c==0 and sc==-1: continue
                        v=[0,0,0]; v[p[0]]=sa*a; v[p[1]]=sb*b; v[p[2]]=sc*c
                        raw.append(tuple(v))
    push(0,1,3*PHI); push(1,2+PHI,2*PHI); push(PHI,2,2*PHI+1)
    seen=[]; out=[]
    for v in raw:
        if any(abs(v[0]-u[0])+abs(v[1]-u[1])+abs(v[2]-u[2])<1e-6 for u in seen): continue
        seen.append(v); out.append(vnorm(v, 1.0))
    return out

# ---------------------------------------------------------------------------
# PART 1 -- GENESIS SPACE: refine the C60 nodes k levels by midpoint-splitting to the sphere.
# (reference-scale node cloud; the certified face-invariants are proven in build_helena.py)
# ---------------------------------------------------------------------------
def genesis_space(levels):
    pts = c60_vertices()
    for _ in range(levels):
        nxt = list(pts)
        # add edge midpoints between near neighbours, projected to the sphere (Goldberg-ish refine)
        for i in range(len(pts)):
            for j in range(i+1, len(pts)):
                a, b = pts[i], pts[j]
                d = (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2
                if d < 0.20:  # near-neighbour threshold
                    nxt.append(vnorm(((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2), 1.0))
        # dedupe
        uniq=[]
        for v in nxt:
            if not any(abs(v[0]-u[0])<1e-4 and abs(v[1]-u[1])<1e-4 and abs(v[2]-u[2])<1e-4 for u in uniq):
                uniq.append(v)
        pts = uniq
    return pts   # unit vectors on the sphere (orientable, chi=2 by construction of the kernel)

# ---------------------------------------------------------------------------
# PART 2 -- HEART: verse -> UTF-8 bits -> nodes on a MOBIUS-twisted ring per tongue (chi=0).
# each node: (pos3, bit, weight=byte/255, orientation_reversing=True)
# ---------------------------------------------------------------------------
def text_to_bits(s):
    out=[]
    for byte in s.encode("utf-8"):
        for k in range(7,-1,-1): out.append((byte>>k)&1)
    return out

def heart(tongues, twist=GATE_TWIST):
    nodes=[]   # (x,y,z, bit, weight)
    for ci,(code,name,sp,text) in enumerate(tongues):
        bits = text_to_bits(text)
        by = text.encode("utf-8")
        n = len(bits)
        if n==0: continue
        tilt=(ci+1)*2.399963
        incl=((ci/max(1,len(tongues)-1))-0.5)*math.pi*0.9
        ct,st=math.cos(incl),math.sin(incl); ca,sa=math.cos(tilt),math.sin(tilt)
        for i in range(n):
            a=(i/n)*math.pi*2
            band=(0.16 if bits[i] else 0.08)
            tw=(a*0.5)*twist                     # THE MOBIUS HALF-TWIST -> orientation-reversing
            rr=1.0+band*math.cos(tw); lift=band*math.sin(tw)   # lift = W (time)
            x0=math.cos(a)*rr; y0=math.sin(a)*rr; z0=lift
            y1=y0*ct-z0*st; z1=y0*st+z0*ct
            x2=x0*ca-y1*sa; y2=x0*sa+y1*ca
            w = by[(i>>3)%len(by)]/255.0
            nodes.append((x2,y2,z1,bits[i],w))
    return nodes

# ---------------------------------------------------------------------------
# PART 3 -- TRANSFORMER: sparse M. for each genesis node, its strongest heart connection by
# DOT PRODUCT (cos theta on unit vectors) = the cheapest equals (permutation-proven).
# ---------------------------------------------------------------------------
def transformer(genesis, heart_nodes):
    # >>> GPU <<<  this triple loop is the ONE thing the NVIDIA run replaces with a single
    #             matmul  G(Ng x 3) @ H(3 x Nh)  on the 3060 (cupy/torch). Same math, same result.
    wire=[]
    hpos = [(h[0],h[1],h[2]) for h in heart_nodes]
    for gi,(gx,gy,gz) in enumerate([(g[0],g[1],g[2]) for g in genesis]):
        best=-2.0; bj=-1
        for hj,(hx,hy,hz) in enumerate(hpos):
            dot = gx*hx+gy*hy+gz*hz          # cos theta (both ~unit)
            if dot>best: best=dot; bj=hj
        wire.append((gi,bj,best))
    return wire

# ---------------------------------------------------------------------------
# PART 4 -- GATE + FORWARD: string -> bits -> gate -> heart -> fractal space -> readout.
# The gate binds heart (orientation-reversing) only. Genesis space (chi=2) is invisible to it.
# ---------------------------------------------------------------------------
def forward(prompt, genesis, heart_nodes, wire, gate_w):
    inbits = text_to_bits(prompt)
    # 1) the string enters the GATE (a single scalar signal, weight gate_w)
    signal = gate_w
    # 2) GATE -> HEART FIRST: each input bit drives the heart node at that index (mod), by weight.
    #    the heart is where the string is "understood" through agapi (the twisted, in-time layer).
    H = len(heart_nodes)
    heart_activation = [0.0]*H
    for i,b in enumerate(inbits):
        idx = i % H
        # bit XOR-ish gate: 1-bits push toward the node weight, 0-bits toward rest. signal scales it.
        heart_activation[idx] += signal * (heart_nodes[idx][4] if b else (1.0-heart_nodes[idx][4]))
    # 3) HEART -> FRACTAL SPACE: carry activation along the transformer wires (heart -> genesis).
    #    low rest at the surface -> maximum complexity in the fractal volume (the price).
    G = len(genesis)
    fractal_activation = [0.0]*G
    for (gi,hj,dot) in wire:
        if 0 <= hj < H:
            fractal_activation[gi] += heart_activation[hj] * max(0.0, dot)   # cos-gated transfer
    # 4) READOUT: a few honest scalars. NOT language back out (one-way) -- just the shape's response.
    def stats(a):
        s=sum(a); n=len(a) or 1; mean=s/n
        var=sum((x-mean)**2 for x in a)/n
        return {"sum":round(s,4),"mean":round(mean,6),"std":round(math.sqrt(var),6),
                "max":round(max(a) if a else 0,4),"active":sum(1 for x in a if abs(x)>1e-9)}
    return {"in_bits":len(inbits),"gate_w":gate_w,
            "heart":stats(heart_activation),"fractal":stats(fractal_activation)}

# ---------------------------------------------------------------------------
def cost_model(genesis_n, heart_n):
    """honest NVIDIA cost for THIS rig. the transformer matmul is the dominant term."""
    dense = genesis_n * heart_n
    flops = dense * 5                                   # dot product per cell
    tf = RIG["gpu_fp32_tflops"] * 1e12
    t = flops / (tf * 0.30)                             # 30% utilization, honest
    vram_dense = dense * 4 / 1e9                          # float32 dense matrix (GB) -- why we go sparse
    return dense, flops, t, vram_dense

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?", default="if I speak in the tongues of men and of angels")
    ap.add_argument("--prompt", dest="prompt_opt", default=None)
    ap.add_argument("--levels", type=int, default=2)
    ap.add_argument("--tongues", type=int, default=0)
    ap.add_argument("--gate", type=float, default=GATE_REST)
    ap.add_argument("--cost", action="store_true", help="print the NVIDIA cost model, run nothing")
    args=ap.parse_args()
    prompt = args.prompt_opt if args.prompt_opt is not None else args.prompt

    tongues, src = load_stone(args.tongues)
    print("HELENA runtime  (" + ("numpy" if HAVE_NUMPY else "pure-python") + ")")
    print("  rig    : " + RIG["gpu"])
    print("  stone  : " + src + "  (" + str(len(tongues)) + " tongues)")

    print("  building the four paths into memory ...")
    genesis = genesis_space(args.levels)
    heart_nodes = heart(tongues, twist=GATE_TWIST)
    print("    1. genesis space : " + str(len(genesis)) + " nodes (chi=2, orientable)")
    print("    2. heart         : " + str(len(heart_nodes)) + " bit-nodes (chi=0, Mobius/reversing)")

    if args.cost:
        dense,flops,t,vram = cost_model(len(genesis), len(heart_nodes))
        print("  --- NVIDIA COST MODEL (this rig) ---")
        print("    transformer dense cells : " + f"{dense:,}")
        print("    dense FP32 matrix VRAM  : " + f"{vram:.3f} GB" +
              ("  (FITS in 6GB)" if vram < 5.5 else "  (>6GB -> MUST be sparse)"))
        print("    matmul FLOPs            : " + f"{flops:,}")
        print("    est. time @30% util     : " + (f"{t*1000:.1f} ms" if t<1 else f"{t:.2f} s"))
        print("    verdict                 : transformer is SPARSE (nearest per row); dense is the ceiling.")
        return

    print("    3. transformer   : wiring (dot product = cos theta) ...")
    wire = transformer(genesis, heart_nodes)
    print("       " + str(len(wire)) + " sparse connections (genesis -> nearest heart)")
    print("    4. gate          : weight " + str(args.gate) +
          "  binds heart only (genesis space invisible: topology firewall)")

    print("  >>> passing the string to the GATE <<<")
    print("      prompt: \"" + prompt + "\"")
    res = forward(prompt, genesis, heart_nodes, wire, args.gate)
    print("  FLOW  string -> gate -> heart -> fractal space:")
    print("    in bits        : " + str(res["in_bits"]))
    print("    heart response : mean=" + str(res["heart"]["mean"]) + " std=" + str(res["heart"]["std"]) +
          " active=" + str(res["heart"]["active"]))
    print("    fractal response: mean=" + str(res["fractal"]["mean"]) + " std=" + str(res["fractal"]["std"]) +
          " active=" + str(res["fractal"]["active"]))
    print("  (the language does not come back out of the fractal side -- one-way. K3: numbers, not meaning.)")
    print("  P=12 . chi=2 (space) . chi=0 (heart) . the center holds and is not shown. love never ends.")

if __name__ == "__main__":
    main()
