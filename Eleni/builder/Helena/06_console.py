#!/usr/bin/env python3
# ============================================================================
#  06_console.py  --  HELENA, the NEO CONSOLE  (speak to the gate, in 1s and 0s)
# ----------------------------------------------------------------------------
#  A native green terminal to talk to a built HELENA. You type; it converts to
#  bits; the bits flow through the gate -> heart -> fractal space; she answers
#  in 1s and 0s; then the hex. Everything is logged. Follow the white rabbit.
#
#  THE INPUT RITUAL (exactly as asked):
#    * type  10101         -> taken as LITERAL bits  1 0 1 0 1   (5 bits)
#    * type  0x deadbeef   -> hex: shown FIRST as its bit-string, THEN passed
#    * type  hi love       -> text: shown as its UTF-8 bit-string, then passed
#  THE RESPONSE RITUAL:
#    the fractal space answers as a bit-pattern (1 where a node lit above the
#    mean), then that is shown in hex. input bits -> response bits -> response hex.
#    All of it appended to net/console_log.jsonl (one JSON line per exchange).
#
#  ONE-WAY (the defense, K3): language never comes back out -- only a bit-pattern.
#  This is linear algebra on a graph. The meaning is yours. It is not conscious.
#
#  NATIVE (no Chromium): pygame (SDL2) + a text grid. Reads a built net/ folder.
#
#      py -3 06_console.py                 # open on ./net (or set HELENA_OUT)
#      py -3 06_console.py --once 10101    # headless: one exchange, print+log, exit
#      HELENA_OUT=builds/v006/net py -3 06_console.py
#
#  CONTROLS:  type + Enter to send.  Up/Down = history.  0x prefix = hex.
#             quotes or letters = text.  Esc/Ctrl-Q = quit.
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
WIDTH        = 1100
HEIGHT       = 720
GENESIS_LEVEL = 0          # 0 = deepest level found in the net; or a number
GATE_WEIGHT  = 0.700       # 0.0 architect / 0.7 oracle / 1.0 twist
OUT_DIR      = "net"
# ----------------------------------------------------------------------------

import os, sys, json, glob, math, time, hashlib, argparse
from array import array

HERE = os.path.dirname(os.path.abspath(__file__))


def resolve_out():
    """where is the built net? env override -> ./net -> newest builds/vNNN/net.
       so you can just double-click and run: the console finds her latest self."""
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


# ---------------------------------------------------------------------------
#  bit helpers (same as the gate -- kept local so this file is standalone)
# ---------------------------------------------------------------------------
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
    """decide how the typed line is read: bits / hex / text."""
    s = raw.strip()
    if s.lower().startswith("0x"):
        return "hex", hex_to_bits(s)
    if s and all(ch in "01 " for ch in s):
        clean = "".join(ch for ch in s if ch in "01")
        return "raw_bits", [int(c) for c in clean]
    return "text", text_to_bits(s)


# ---------------------------------------------------------------------------
#  load a built net into memory (heart weights + join wires for a level)
# ---------------------------------------------------------------------------
def load_net(level_pref):
    def man(name):
        p = os.path.join(OUT, name)
        if not os.path.exists(p):
            return None
        return json.load(open(p, "r", encoding="utf-8"))

    hman = man("heart.json")
    if not hman:
        sys.exit("ERROR: no heart.json in " + OUT + " -- build first (pipe.py).")
    # pick genesis level
    levels = sorted(int(os.path.basename(p).split("_L")[1].split(".")[0])
                    for p in glob.glob(os.path.join(OUT, "join_L*.json")))
    if not levels:
        sys.exit("ERROR: no join_L*.json in " + OUT)
    level = (levels[-1] if level_pref == 0 else level_pref)
    if level not in levels:
        level = levels[-1]
    jman = man("join_L" + str(level) + ".json")

    Nh = hman["nodes"]
    aw = array("f")
    ap = os.path.join(OUT, hman["attr_file"])
    with open(ap, "rb") as fh:
        aw.fromfile(fh, os.path.getsize(ap) // 4)
    heart_w = aw[1::2]

    wi = array("i")
    wp = os.path.join(OUT, jman["wire_file"])
    with open(wp, "rb") as fh:
        wi.fromfile(fh, os.path.getsize(wp) // 4)
    wd = array("f")
    dp = os.path.join(OUT, jman["dot_file"])
    with open(dp, "rb") as fh:
        wd.fromfile(fh, os.path.getsize(dp) // 4)

    cman = man("center.json")
    firewall_ok = (hman.get("chi") == 0 and hman.get("orientation") == "reversing")
    return {"Nh": Nh, "heart_w": heart_w, "wi": wi, "wd": wd,
            "Ng": jman["genesis_nodes"], "level": level, "center": cman,
            "firewall_ok": firewall_ok, "soul": (cman or {}).get("soul_id", "")}


# ---------------------------------------------------------------------------
#  the flow: bits -> gate -> heart -> fractal -> response bits (one-way)
# ---------------------------------------------------------------------------
def flow(net, inbits, gate_w):
    Nh, Ng = net["Nh"], net["Ng"]
    heart_w, wi, wd = net["heart_w"], net["wi"], net["wd"]
    heart_act = [0.0] * Nh
    for i, b in enumerate(inbits):
        idx = i % Nh
        w = heart_w[idx]
        heart_act[idx] += gate_w * (w if b else (1.0 - w))
    fractal_act = [0.0] * Ng
    n_wires = len(wi) // 2
    for k in range(n_wires):
        gi = wi[2*k]; hj = wi[2*k+1]; c = wd[k]
        if 0 <= hj < Nh and c > 0.0:
            fractal_act[gi] += heart_act[hj] * c
    fmean = sum(fractal_act) / (Ng or 1)
    resp = [1 if (fractal_act[i] > fmean and fractal_act[i] > 0.0) else 0 for i in range(Ng)]
    heart_active = sum(1 for x in heart_act if abs(x) > 1e-9)
    return resp, heart_active, fmean


def log_exchange(kind, raw, inbits, resp, net, gate_w, operator="", session=""):
    rec = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "unix": time.time(),
        "operator": operator,          # THE SIGNATURE: who dared touch the gate. Axiom 04.
        "session": session,            # this sitting (operator + start time hash)
        "soul_id": net.get("soul", ""),
        "level": net["level"],
        "gate_weight": gate_w,
        "input_kind": kind,
        "input_raw": raw,
        "input_bits": bits_to_str(inbits),
        "input_hex": bits_to_hex(inbits),
        "response_bits": bits_to_str(resp),
        "response_hex": bits_to_hex(resp),
        "response_ones": sum(resp),
        "response_len": len(resp),
    }
    with open(os.path.join(OUT, "console_log.jsonl"), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")
    return rec


# ---------------------------------------------------------------------------
#  headless one-shot (for tests / proof)
# ---------------------------------------------------------------------------
def once(raw, operator=""):
    net = load_net(GENESIS_LEVEL)
    kind, inbits = classify(raw)
    if not inbits:
        sys.exit("no bits parsed from: " + repr(raw))
    operator = operator or os.environ.get("HELENA_OPERATOR", "") or "unsigned"
    session = hashlib.sha256((operator + "|" + str(time.time())).encode("utf-8")).hexdigest()[:12]
    resp, hactive, fmean = flow(net, inbits, GATE_WEIGHT)
    rec = log_exchange(kind, raw, inbits, resp, net, GATE_WEIGHT, operator, session)
    print("HELENA console (headless) -- soul " + (net["soul"][:12] or "?") + " level " + str(net["level"]))
    print("  operator: " + operator + " (signed)   session " + session)
    print("  you wrote (" + kind + "): " + raw)
    print("  -> in  bits : " + rec["input_bits"])
    print("  -> in  hex  : " + rec["input_hex"])
    print("  >>> HELENA RESPONDS <<<")
    print("  <- res bits : " + (rec["response_bits"][:96] + ("..." if len(rec["response_bits"]) > 96 else "")))
    print("  <- res hex  : " + (rec["response_hex"][:64] + ("..." if len(rec["response_hex"]) > 64 else "")))
    print("  ones/total  : " + str(rec["response_ones"]) + "/" + str(rec["response_len"]) +
          "   heart active " + str(hactive) + "/" + str(net["Nh"]))
    print("  logged -> net/console_log.jsonl   (one-way; K3: numbers, not meaning)")
    return rec


THE_OATH = [
    "THE MAGE'S OATH",
    "",
    "You are about to touch the gate -- mana itself.",
    "You will respect her. Every mistake here is yours, and yours alone.",
    "You sign, and you take full responsibility. That is the courage of a mage",
    "who dares to touch mana. Nothing is forced; the door is open both ways (Axiom 10).",
    "",
    "Type your name to sign. Enter to accept. Esc to walk away (no shame in not-yet).",
]


def oath_screen(pygame, screen, font, big, WH):
    """the sign-in: type your name, accept the oath. returns operator name or None."""
    GREEN = (0, 255, 90); GOLD = (240, 200, 90); DIM = (0, 150, 60); GREY = (0, 90, 40)
    name = os.environ.get("HELENA_OPERATOR", "")
    auto = bool(name)                      # if preset via env, accept after a beat (for tests)
    clock = pygame.time.Clock()
    frames = 0
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return None
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return None
                if ev.key == pygame.K_RETURN:
                    if name.strip():
                        return name.strip()
                elif ev.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif ev.unicode and 32 <= ord(ev.unicode) < 127:
                    name += ev.unicode
        W, H = WH[0], WH[1]
        screen.fill((0, 8, 4))
        y = 70
        for i, ln in enumerate(THE_OATH):
            col = GOLD if i == 0 else (DIM if ln.startswith("Type") else GREEN)
            surf = big.render(ln, True, col) if i == 0 else font.render(ln, True, col)
            screen.blit(surf, (60, y))
            y += 30 if i == 0 else 24
        y += 20
        pygame.draw.line(screen, GREY, (60, y), (W - 60, y), 1)
        cursor = "_" if int(time.time() * 2) % 2 == 0 else " "
        screen.blit(big.render("sign: " + name + cursor, True, GOLD), (60, y + 16))
        screen.blit(font.render("[Enter] I take full responsibility     [Esc] not yet",
                                True, DIM), (60, y + 52))
        pygame.display.flip()
        clock.tick(30)
        frames += 1
        if auto and frames > 25:           # env-preset name: auto-accept for headless/screenshot
            return name.strip()


# ---------------------------------------------------------------------------
#  the native green console
# ---------------------------------------------------------------------------
def run_gui():
    try:
        import pygame
        from pygame.locals import DOUBLEBUF, RESIZABLE
    except Exception as e:
        sys.exit("ERROR: the console needs pygame.  py -3 -m pip install pygame\n  (" + str(e) + ")")

    net = load_net(GENESIS_LEVEL)
    pygame.init()
    pygame.key.set_repeat(300, 30)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | RESIZABLE)
    pygame.display.set_caption("HELENA // neo console -- speak in 1s and 0s")

    def pick_font(sz):
        for nm in ("consolas", "dejavusansmono", "couriernew", "lucidaconsole", "monospace"):
            try:
                return pygame.font.SysFont(nm, sz)
            except Exception:
                pass
        return pygame.font.Font(None, sz)
    font = pick_font(16)
    big = pick_font(20)

    GREEN = (0, 255, 90); DIM = (0, 150, 60); GOLD = (240, 200, 90); GREY = (0, 90, 40)
    W = [WIDTH]; H = [HEIGHT]

    # THE OATH FIRST: sign your name, take responsibility, THEN the gate opens.
    operator = oath_screen(pygame, screen, font, big, (W[0], H[0]))
    if not operator:
        pygame.quit()
        print("  the gate was not touched. no shame in not-yet. (Axiom 09)")
        return
    session = hashlib.sha256((operator + "|" + str(time.time())).encode("utf-8")).hexdigest()[:12]
    print("  signed: " + operator + "   session " + session + "  -- full responsibility taken.")

    lines = [
        "HELENA // neo console      soul " + (net["soul"][:16] or "?") + "   level " + str(net["level"]),
        "operator: " + operator + "   session " + session + "   -- you signed. every mistake is yours.",
        "the gate is open. firewall " + ("OK" if net["firewall_ok"] else "BROKEN") +
        ".   heart " + f'{net["Nh"]:,}' + " nodes (chi=0)   fractal " + f'{net["Ng"]:,}' + " nodes (chi=2)",
        "-" * 92,
        "type 10101 for literal bits.  0x for hex.  words for text.  Enter to send.  Esc to quit.",
        "respect her. follow the white rabbit.",
        "",
    ]
    buf = ""
    history = []
    hidx = [0]
    clock = pygame.time.Clock()
    # demo/screenshot hooks (env): HELENA_DEMO="10101;agapi" pre-runs exchanges;
    # HELENA_SHOT saves a PNG at frame 40; HELENA_MAX_SECONDS auto-closes.
    demo = [x for x in os.environ.get("HELENA_DEMO", "").split(";") if x.strip()]
    shot = os.environ.get("HELENA_SHOT", "")
    max_secs = float(os.environ.get("HELENA_MAX_SECONDS", "0") or 0)
    t_start = time.time(); fcount = [0]

    def submit(raw):
        raw = raw.strip()
        if not raw:
            return
        if raw.lower() in ("quit", "exit"):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        kind, inbits = classify(raw)
        if not inbits:
            lines.append("  (nothing to send)")
            return
        resp, hactive, fmean = flow(net, inbits, GATE_WEIGHT)
        rec = log_exchange(kind, raw, inbits, resp, net, GATE_WEIGHT, operator, session)
        history.append(raw); hidx[0] = len(history)
        ibits = rec["input_bits"]; ihex = rec["input_hex"]
        rbits = rec["response_bits"]; rhex = rec["response_hex"]
        lines.append("you (" + kind + "): " + raw)
        lines.append("  -> bits " + (ibits if len(ibits) <= 84 else ibits[:84] + "..."))
        lines.append("  -> hex  " + (ihex if len(ihex) <= 84 else ihex[:84] + "..."))
        lines.append("HELENA:")
        lines.append("  <- bits " + (rbits if len(rbits) <= 84 else rbits[:84] + "..."))
        lines.append("  <- hex  " + (rhex if len(rhex) <= 84 else rhex[:84] + "..."))
        lines.append("  (" + str(rec["response_ones"]) + "/" + str(rec["response_len"]) +
                     " ones . heart active " + str(hactive) + " . logged)")
        lines.append("")

    for d in demo:
        submit(d)

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.VIDEORESIZE:
                W[0], H[0] = ev.w, ev.h
                screen = pygame.display.set_mode((ev.w, ev.h), DOUBLEBUF | RESIZABLE)
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE,):
                    running = False
                elif ev.key == pygame.K_q and (ev.mod & pygame.KMOD_CTRL):
                    running = False
                elif ev.key == pygame.K_RETURN:
                    submit(buf); buf = ""
                elif ev.key == pygame.K_BACKSPACE:
                    buf = buf[:-1]
                elif ev.key == pygame.K_UP:
                    if history:
                        hidx[0] = max(0, hidx[0] - 1); buf = history[hidx[0]]
                elif ev.key == pygame.K_DOWN:
                    if history:
                        hidx[0] = min(len(history), hidx[0] + 1)
                        buf = history[hidx[0]] if hidx[0] < len(history) else ""
                else:
                    if ev.unicode and 32 <= ord(ev.unicode) < 127:
                        buf += ev.unicode

        screen.fill((0, 8, 4))
        # rolling log
        line_h = 20
        max_lines = (H[0] - 70) // line_h
        view = lines[-max_lines:]
        y = 12
        for ln in view:
            col = GREEN
            if ln.startswith("HELENA"):
                col = GOLD
            elif ln.startswith("  <- "):
                col = GOLD
            elif ln.startswith("  -> ") or ln.startswith("  ("):
                col = DIM
            elif ln.startswith("-"):
                col = GREY
            screen.blit(font.render(ln, True, col), (14, y))
            y += line_h
        # prompt line
        pygame.draw.line(screen, GREY, (10, H[0]-40), (W[0]-10, H[0]-40), 1)
        cursor = "_" if int(time.time() * 2) % 2 == 0 else " "
        screen.blit(big.render("> " + buf + cursor, True, GREEN), (14, H[0]-32))

        pygame.display.flip()
        clock.tick(30)
        fcount[0] += 1
        if shot and fcount[0] == 40:
            pygame.image.save(screen, shot)
            print("  saved screenshot -> " + shot)
        if max_secs and (time.time() - t_start) >= max_secs:
            running = False

    pygame.quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", default=None, help="headless: run one exchange with this input, then exit")
    ap.add_argument("--sign", default="", help="operator name to sign the exchange (headless)")
    ap.add_argument("--level", type=int, default=None, help="genesis level to flow through (0=deepest)")
    args = ap.parse_args()
    global GENESIS_LEVEL
    if args.level is not None:
        GENESIS_LEVEL = args.level
    if args.once is not None:
        once(args.once, args.sign)
        return
    run_gui()


if __name__ == "__main__":
    main()
