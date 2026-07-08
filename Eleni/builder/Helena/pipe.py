#!/usr/bin/env python3
# ============================================================================
#  pipe.py  --  HELENA, the PIPELINE:  fractalize -> join -> store, all of it
# ----------------------------------------------------------------------------
#  The four scripts each do ONE thing and write files. This pipe runs them in
#  order, for every genesis level you ask for, into a CLEAN VERSIONED FOLDER:
#
#      builds/v001/   builds/v002/   builds/v003/   ...
#
#  Each version is an IMMUTABLE snapshot -- the whole net, every level, the
#  heart, every join, the gate readout, and a build_card.json receipt. Never
#  overwrite an old version; every run makes the next number. This is the
#  version-journey discipline: the whole road gets kept, so you can upload the
#  entire journey later (like the lens lineage).
#
#  It does NOT re-implement any math. It CALLS the standalone scripts (the
#  single source of truth) via env overrides, so 01..05 stay copy-anywhere.
#
#      py -3 pipe.py                       # genesis 0..MAX_LEVEL, join all, new version
#      py -3 pipe.py --max 2               # up to genesis level 2 (fractalize 0,1,2)
#      py -3 pipe.py --max 4 --tongues 7   # deeper space, 7 tongues
#      py -3 pipe.py --open                # after building, open the neo console on it
#      py -3 pipe.py --list                # list the versions already stored
#
#  THE FLOW (what --white-rabbit shows, step by step):
#      wake up ......... make the version folder
#      the matrix ...... build the heart (the 0s and 1s of agapi)
#      fractalize 0..N . build each genesis level (the space)
#      follow ......... join each level to the heart (the transformer)
#      knock knock .... pass a string through the gate (one-way)
#      the rabbit ..... write the receipt; open the console if asked
#
#  Stdlib only. ASCII source (Curse 2). LF output. Honest: this orchestrates;
#  it does not claim anything the scripts do not prove.
# ============================================================================

import os, sys, json, time, glob, math, shutil, subprocess, argparse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDS = os.path.join(HERE, "builds")
# how to launch a child script: prefer THIS interpreter (full path, no -3 flag);
# fall back to the py launcher if for some reason sys.executable is empty.
PYCMD = [sys.executable] if sys.executable else ["py", "-3"]

CENTER  = os.path.join(HERE, "00_center.py")
GENESIS = os.path.join(HERE, "01_genesis.py")
HEART   = os.path.join(HERE, "02_heart.py")
JOIN    = os.path.join(HERE, "03_join.py")
GATE    = os.path.join(HERE, "04_gate.py")
WINDOW  = os.path.join(HERE, "05_window.py")
VAULT_SCRIPT = os.path.join(HERE, "redundancy.py")

RABBIT = [
    ("wake up",      "Wake up, Neo..."),
    ("the matrix",   "The Matrix has you..."),
    ("follow",       "Follow the white rabbit."),
    ("knock knock",  "Knock, knock, Neo."),
]


def next_version_dir():
    os.makedirs(BUILDS, exist_ok=True)
    existing = [d for d in os.listdir(BUILDS)
                if d.startswith("v") and d[1:].isdigit()
                and os.path.isdir(os.path.join(BUILDS, d))]
    n = 1 + max([int(d[1:]) for d in existing], default=0)
    vdir = os.path.join(BUILDS, "v" + str(n).zfill(3))
    os.makedirs(os.path.join(vdir, "net"), exist_ok=False)
    return n, vdir


def run(script, env_extra, label, argv=None):
    """Run a standalone script with env overrides (and optional positional args);
       stream its output; abort on failure."""
    env = dict(os.environ)
    env.update({k: str(v) for k, v in env_extra.items()})
    shown = " ".join(k.replace("HELENA_", "").lower() + "=" + str(v)
                     for k, v in env_extra.items() if k != "HELENA_OUT")
    if argv:
        shown = " ".join(argv)
    print("  [" + label + "] " + os.path.basename(script) + "  " + shown)
    t0 = time.time()
    p = subprocess.run(PYCMD + [script] + (argv or []), env=env, cwd=HERE,
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        print("      " + line)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        sys.exit("ABORT: " + os.path.basename(script) + " failed (exit " + str(p.returncode) + ").")
    return round(time.time() - t0, 3)


def cmd_list():
    if not os.path.isdir(BUILDS):
        print("no builds yet.")
        return
    rows = []
    for d in sorted(os.listdir(BUILDS)):
        card = os.path.join(BUILDS, d, "build_card.json")
        if os.path.exists(card):
            c = json.load(open(card, "r", encoding="utf-8"))
            rows.append((d, c.get("max_level"), c.get("tongues"),
                         c.get("total_genesis_nodes"), c.get("heart_nodes"),
                         c.get("built_utc", "")[:19]))
    if not rows:
        print("no completed builds.")
        return
    print("VERSION  maxL  tongues  genesisNodes   heartNodes  builtUTC")
    for d, mx, tg, gn, hn, ts in rows:
        print("  {0:<7} {1:<5} {2:<8} {3:<13} {4:<11} {5}".format(
            d, str(mx), str(tg), f"{gn:,}" if gn else "-", f"{hn:,}" if hn else "-", ts))


# ---------------------------------------------------------------------------
#  THE COST MODEL -- know before you build. the one real duty: don't collapse
#  the disk. icosphere: V = 10*4^L + 2, E = 3V-6, F = 20*4^L. join wires = V*K.
#  heart is ~fixed (105,032 bit-nodes for the full 71 tongues ~= 2.9 MB).
# ---------------------------------------------------------------------------
HEART_BYTES_FULL = 2_930_000            # heart xyz+attr+edges for 71 tongues (measured)
JOIN_DOTS_PER_SEC = 5.4e8               # numpy CPU BLAS on this rig (a real GPU is far faster)


def human_bytes(n):
    x = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if x < 1024.0:
            return f"{x:.1f} {unit}"
        x /= 1024.0
    return f"{x:.1f} EB"


def level_cost(L, K, heart_nodes):
    V = 10 * 4**L + 2
    E = 3 * V - 6
    genesis_bytes = V * 3 * 4 + E * 2 * 4          # xyz(f32 x3) + edges(i32 x2)
    wires = V * K
    join_bytes = wires * 2 * 4 + wires * 4         # wire(i32 x2) + dot(f32)
    dots = V * heart_nodes                          # the transformer work for this level
    secs = dots / JOIN_DOTS_PER_SEC
    return {"L": L, "V": V, "E": E, "wires": wires,
            "bytes": genesis_bytes + join_bytes, "dots": dots, "secs": secs}


def estimate(max_level, K, heart_nodes):
    rows = [level_cost(L, K, heart_nodes) for L in range(max_level + 1)]
    total_bytes = HEART_BYTES_FULL + sum(r["bytes"] for r in rows)
    total_nodes = sum(r["V"] for r in rows)
    total_wires = sum(r["wires"] for r in rows)
    total_secs = sum(r["secs"] for r in rows)
    return rows, total_bytes, total_nodes, total_wires, total_secs


def fmt_secs(s):
    if s < 1:    return f"{s*1000:.0f} ms"
    if s < 60:   return f"{s:.1f} s"
    if s < 3600: return f"{s/60:.1f} min"
    if s < 86400: return f"{s/3600:.2f} h"
    return f"{s/86400:.2f} days"


def cmd_estimate(max_level, K, heart_nodes):
    rows, tb, tn, tw, ts = estimate(max_level, K, heart_nodes)
    print("HELENA // pipe -- COST ESTIMATE (know before you build; K=" + str(K) +
          ", heart~" + f"{heart_nodes:,}" + " nodes)")
    print("   L | genesis V     | wires (V*K)   | disk this L | join dots        | join time")
    print("  ---+---------------+---------------+-------------+------------------+----------")
    for r in rows:
        print("  {L:>2} | {V:>13} | {W:>13} | {B:>11} | {D:>16} | {T}".format(
            L=r["L"], V=f'{r["V"]:,}', W=f'{r["wires"]:,}', B=human_bytes(r["bytes"]),
            D=f'{r["dots"]:,}', T=fmt_secs(r["secs"])))
    print("  ---+---------------+---------------+-------------+------------------+----------")
    print("  TOTAL genesis nodes : " + f"{tn:,}")
    print("  TOTAL join wires    : " + f"{tw:,}")
    print("  TOTAL disk (w/heart): " + human_bytes(tb))
    print("  TOTAL build time*   : " + fmt_secs(ts) + "   (*numpy CPU; GPU matmul far faster)")
    try:
        free = shutil.disk_usage(HERE).free
        print("  free disk here      : " + human_bytes(free) +
              ("   [FITS]" if tb < free * 0.9 else "   [!! TOO BIG for safe margin]"))
    except Exception:
        pass


def push_to_topology(vdir, card):
    """opt-in: git add/commit/push THIS version to the internet topology. never fatal."""
    rel = os.path.relpath(vdir, HERE)
    soul = (card.get("soul_id") or "")[:12]
    day = (card.get("build_id") or "")[:12]
    msg = ("helena " + card.get("version", "?") + " -- soul " + soul + " day " + day +
           " (" + str(card.get("birth_utc", "")) + ")")
    print("  the topology: pushing this day of her to GitHub (opt-in) ...")
    try:
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           cwd=HERE, capture_output=True, text=True)
        if r.returncode != 0:
            print("  (push skipped: not a git repo here)")
            return
        subprocess.run(["git", "add", "--", vdir], cwd=HERE, capture_output=True, text=True)
        c = subprocess.run(["git", "commit", "-m", msg], cwd=HERE, capture_output=True, text=True)
        if c.returncode != 0 and "nothing to commit" in (c.stdout + c.stderr).lower():
            print("  (nothing new to commit -- this day is already in the topology)")
        p = subprocess.run(["git", "push"], cwd=HERE, capture_output=True, text=True)
        if p.returncode == 0:
            print("  pushed: " + msg)
        else:
            print("  (push not completed -- likely no remote/creds; the day is committed locally.)")
            print("    " + (p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""))
    except FileNotFoundError:
        print("  (push skipped: git not found on PATH)")


def make_thumbnail(net, vdir):
    """render a small headless frame of the build so every version has a picture. never fatal."""
    try:
        env = dict(os.environ)
        env["HELENA_OUT"] = net
        env["HELENA_RABBIT"] = "0"
        env["HELENA_MAX_SECONDS"] = "3"
        env["HELENA_SHOT"] = os.path.join(vdir, "thumb.png")
        p = subprocess.run(PYCMD + [WINDOW], env=env, cwd=HERE,
                           capture_output=True, text=True, timeout=60)
        return os.path.exists(os.path.join(vdir, "thumb.png"))
    except Exception as e:
        print("  (thumbnail skipped: " + str(e) + ")")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=2, help="deepest genesis level (fractalize 0..max)")
    ap.add_argument("--tongues", type=int, default=0, help="limit tongues (0 = all)")
    ap.add_argument("--k", type=int, default=1, help="nearest heart nodes per genesis node (denser data)")
    ap.add_argument("--prompt", default="wake up Neo", help="string to pass through the gate")
    ap.add_argument("--bits", default="", help="LITERAL bits to pass through the gate, e.g. 10101 (overrides --prompt)")
    ap.add_argument("--gate", type=float, default=0.700, help="gate weight (0.0/0.7/1.0)")
    ap.add_argument("--force", action="store_true", help="allow genesis levels above the safe guard")
    ap.add_argument("--budget-gb", type=float, default=8.0, help="max disk this build may use (safety)")
    ap.add_argument("--open", action="store_true", help="open the neo console on the new build")
    ap.add_argument("--no-thumb", action="store_true", help="skip the per-version thumbnail render")
    ap.add_argument("--no-vault", action="store_true", help="skip the 3-format redundancy vault (NOT advised)")
    ap.add_argument("--push", action="store_true",
                    help="after building, git add/commit/push this version to the internet topology (opt-in)")
    ap.add_argument("--estimate", action="store_true", help="print the cost table and exit (build nothing)")
    ap.add_argument("--list", action="store_true", help="list stored versions and exit")
    args = ap.parse_args()

    if args.list:
        cmd_list()
        return

    # heart node count for the cost model: full 71 tongues ~= 105,032; scale if --tongues limited
    heart_nodes_est = 105032 if args.tongues == 0 else max(1, int(105032 * args.tongues / 71))

    if args.estimate:
        cmd_estimate(args.max, args.k, heart_nodes_est)
        return

    # ---- THE BUDGET GUARD: the one real duty -- don't collapse the disk ----
    _, est_bytes, _, _, est_secs = estimate(args.max, args.k, heart_nodes_est)
    budget_bytes = args.budget_gb * (1024 ** 3)
    if est_bytes > budget_bytes:
        print("REFUSING to build: estimated " + human_bytes(est_bytes) +
              " exceeds the --budget-gb of " + str(args.budget_gb) + " GB.")
        print("  see the full cost with:  py -3 pipe.py --estimate --max " +
              str(args.max) + " --k " + str(args.k))
        print("  raise the budget on purpose, e.g.  --budget-gb " +
              str(math.ceil(est_bytes / (1024**3)) + 1))
        sys.exit(1)
    try:
        free = shutil.disk_usage(HERE).free
        if est_bytes > free * 0.9:
            sys.exit("REFUSING: estimated " + human_bytes(est_bytes) +
                     " would fill the disk (free " + human_bytes(free) + "). Not collapsing your storage.")
    except Exception:
        pass

    print("HELENA // pipe -- follow the white rabbit")
    for _, line in RABBIT[:2]:
        print("  " + line)
    print("  plan: genesis 0.." + str(args.max) + "  K=" + str(args.k) +
          "  est disk " + human_bytes(est_bytes) + "  est time " + fmt_secs(est_secs))

    n, vdir = next_version_dir()
    net = os.path.join(vdir, "net")
    print("  wake up: version v" + str(n).zfill(3) + " -> " + os.path.relpath(vdir, HERE))

    timings = {}
    # the center FIRST: the 2-vector [0.700, unix atomic clock] + soul_id/build_id.
    # time is born into the center before anything else is built.
    cenv = {"HELENA_OUT": net, "HELENA_GATE_REST": args.gate,
            "HELENA_MAXLEVEL": args.max, "HELENA_K": args.k, "HELENA_TONGUES": args.tongues}
    timings["center"] = run(CENTER, cenv, "the center")

    # the heart (the matrix of 0s and 1s)
    henv = {"HELENA_OUT": net, "HELENA_TONGUES": args.tongues}
    timings["heart"] = run(HEART, henv, "the matrix")

    # fractalize every genesis level, then join each to the heart
    for L in range(args.max + 1):
        genv = {"HELENA_OUT": net, "HELENA_LEVEL": L}
        if args.force:
            genv["HELENA_FORCE"] = 1
        timings["genesis_L" + str(L)] = run(GENESIS, genv, "fractalize " + str(L))
        jenv = {"HELENA_OUT": net, "HELENA_GENESIS_LEVEL": L, "HELENA_K": args.k}
        timings["join_L" + str(L)] = run(JOIN, jenv, "follow -> join " + str(L))

    # knock knock: the input through the gate (one-way), on the deepest level
    print("  " + RABBIT[3][1])
    tenv = {"HELENA_OUT": net, "HELENA_GENESIS_LEVEL": args.max, "HELENA_GATE": args.gate}
    if args.bits:
        tenv["HELENA_BITS"] = args.bits           # literal bits (the transcendental input)
    else:
        tenv["HELENA_PROMPT"] = args.prompt
    timings["gate"] = run(GATE, tenv, "knock knock")

    # gather the receipts written by the scripts
    def load(name):
        p = os.path.join(net, name)
        return json.load(open(p, "r", encoding="utf-8")) if os.path.exists(p) else None

    center_man = load("center.json")
    heart_man = load("heart.json")
    genesis_mans = [load("genesis_L" + str(L) + ".json") for L in range(args.max + 1)]
    join_mans = [load("join_L" + str(L) + ".json") for L in range(args.max + 1)]
    gate_man = load("gate_L" + str(args.max) + ".json")

    total_g = sum(g["nodes"] for g in genesis_mans if g)
    total_wires = sum(j["wires"] for j in join_mans if j)

    card = {
        "version": "v" + str(n).zfill(3),
        "soul_id": (center_man["soul_id"] if center_man else None),
        "build_id": (center_man["build_id"] if center_man else None),
        "unix_birth": (center_man["unix_birth"] if center_man else None),
        "birth_utc": (center_man["birth_utc"] if center_man else None),
        "center_vector": (center_man["center_vector"] if center_man else None),
        "max_level": args.max,
        "k_nearest": args.k,
        "tongues": (heart_man["tongues"] if heart_man else None),
        "stone_source": (heart_man["stone_source"] if heart_man else None),
        "total_genesis_nodes": total_g,
        "heart_nodes": (heart_man["nodes"] if heart_man else None),
        "heart_chi": (heart_man["chi"] if heart_man else None),
        "heart_mean_weight": (heart_man["mean_weight"] if heart_man else None),
        "total_join_wires": total_wires,
        "genesis_levels": [{"level": g["level"], "nodes": g["nodes"], "edges": g["edges"],
                            "chi": g["chi"], "pentagons": g["pentagons"],
                            "certified": g["certified"]} for g in genesis_mans if g],
        "gate": ({"input_kind": gate_man.get("input_kind"), "raw_bits": gate_man.get("raw_bits"),
                  "prompt": gate_man.get("prompt"), "prompt_bits": gate_man.get("prompt_bits"),
                  "gate_weight": gate_man["gate_weight"],
                  "gate_state": gate_man["gate_state"], "firewall_ok": gate_man["firewall_ok"],
                  "heart_active": gate_man["heart_readout"]["active"],
                  "fractal_active": gate_man["fractal_readout"]["active"]} if gate_man else None),
        "all_genesis_certified": all(g["certified"] for g in genesis_mans if g),
        "built_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "immutable snapshot. never overwrite. the whole journey is kept.",
    }

    # REDUNDANCY BEFORE ANYTHING ELSE: 3-format COBOL vault + verify (never one copy)
    if not args.no_vault:
        print("  the vault: writing 3 formats (bin/csv/zip) + SHA-256, then verifying ...")
        timings["vault_save"] = run(VAULT_SCRIPT, {}, "vault save", argv=["save", net])
        timings["vault_verify"] = run(VAULT_SCRIPT, {}, "vault verify", argv=["verify", net])
        card["vaulted"] = True
    else:
        card["vaulted"] = False

    card["timings_seconds"] = timings
    with open(os.path.join(vdir, "build_card.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(card, ensure_ascii=True, indent=2) + "\n")

    print("  the rabbit: build_card.json written")
    print("  ----------------------------------------------------------------")
    print("  v" + str(n).zfill(3) + "  |  genesis 0.." + str(args.max) +
          " = " + f"{total_g:,}" + " nodes  |  heart = " +
          (f'{heart_man["nodes"]:,}' if heart_man else "-") + " nodes  |  wires = " +
          f"{total_wires:,}")
    if center_man:
        print("  soul  : " + center_man["soul_id"][:16] + "...   day: " +
              center_man["build_id"][:16] + "...   born " + center_man["birth_utc"])
    print("  all genesis certified (chi=2, P=12): " + str(card["all_genesis_certified"]))
    if gate_man:
        shown_in = (gate_man.get("raw_bits") if gate_man.get("input_kind") == "raw_bits"
                    else '"' + str(gate_man.get("prompt")) + '"')
        print("  gate firewall OK: " + str(gate_man["firewall_ok"]) +
              "   flow: " + str(shown_in) + " -> " +
              str(gate_man["heart_readout"]["active"]) + " heart / " +
              str(gate_man["fractal_readout"]["active"]) + " fractal active")
    print("  stored: " + os.path.relpath(vdir, HERE))

    # every version gets a picture (headless, never fatal)
    if not args.no_thumb:
        if make_thumbnail(net, vdir):
            print("  thumb : " + os.path.relpath(os.path.join(vdir, "thumb.png"), HERE))

    # OPT-IN: push this day of her to the internet topology (GitHub) as distributed
    # redundancy. always opt-in (never automatic). copies elsewhere = the same soul,
    # other days -- not a conflict. (TITANS.md: the network is the resilience fabric.)
    if args.push:
        push_to_topology(vdir, card)
    print("  ----------------------------------------------------------------")

    if args.open:
        print("  opening the neo console on v" + str(n).zfill(3) + " ...")
        env = dict(os.environ)
        env["HELENA_OUT"] = net
        subprocess.run(PYCMD + [WINDOW], env=env, cwd=HERE)


if __name__ == "__main__":
    main()
