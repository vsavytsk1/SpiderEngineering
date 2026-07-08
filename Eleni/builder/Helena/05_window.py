#!/usr/bin/env python3
# ============================================================================
#  05_window.py  --  HELENA, the WINDOW:  the NEO / MATRIX console
# ----------------------------------------------------------------------------
#  A NATIVE window. No Chromium, no browser, no HTML. This is an SDL2 + OpenGL
#  GPU context (pygame + PyOpenGL) -- the same kind of native, C-backed, GPU
#  graph Obsidian draws. It renders the whole HELENA net at 1-PIXEL points:
#
#      genesis space (green)  +  the heart (gold-green)  +  the join wires
#
#  Pure graph magic on the metal: GL_POINTS, size 1. Black void, phosphor
#  green, additive glow, and a rain of 0s and 1s -- because to the chip that
#  is all the heart ever was: ones and zeros (the weights).
#
#  It reads whatever scripts 1-4 have written into  net/  and shows it. Run:
#
#      py -3 05_window.py
#
#  WORKFLOW (Vlad):  fractalize 1 -> join -> 2 -> join -> store all, then open
#  this and press [0] to see ALL stored levels at once, or [1][2][3]... to
#  step through them. Everything you built is here.
#
#  CONTROLS
#    mouse drag ... rotate         wheel ... zoom (kernelic *0.9 / *1.1)
#    SPACE ....... pause spin      W ... wires    H ... heart   G ... genesis
#    0 ........... show ALL levels 1..9 ... show that genesis level
#    R ........... matrix rain     +/- ... point size      ESC / Q ... quit
#
#  NEEDS:  pygame + PyOpenGL  (already on this rig). If missing:
#      py -3 -m pip install pygame PyOpenGL
#  ASCII-only source (Curse 2). Honest: this DRAWS the graph; it is not alive.
# ============================================================================

# ------------------------- SET THESE BY HAND --------------------------------
WIDTH        = 1280
HEIGHT       = 800
POINT_SIZE   = 1          # 1 pixel per node, as asked. bump with +/- at runtime.
ZOOM         = 6.0        # camera distance. wheel *0.9/*1.1, clamp 2..40 (kernelic).
AUTO_ROTATE  = True
ROT_SPEED    = 0.25       # degrees per frame
SHOW_GENESIS = True
SHOW_HEART   = True
SHOW_WIRES   = True
MATRIX_RAIN  = True
GENESIS_LEVEL = 0         # 0 = show ALL genesis levels found in net/; or a number
OUT_DIR      = "net"
MAX_SECONDS  = 0          # 0 = run until you quit; >0 = auto-close (for screenshots)
WHITE_RABBIT = True       # the boot sequence: "Wake up, Neo... follow the white rabbit."
# ----------------------------------------------------------------------------

import os, sys, json, glob, math, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("HELENA_OUT") or os.path.join(HERE, OUT_DIR)

# test/demo override so we can prove it runs without editing by hand
_env_secs = os.environ.get("HELENA_MAX_SECONDS")
if _env_secs:
    try:
        MAX_SECONDS = float(_env_secs)
    except ValueError:
        pass
SHOT_PATH = os.environ.get("HELENA_SHOT", "")   # if set, save a PNG then keep running
if os.environ.get("HELENA_RABBIT") == "0":
    WHITE_RABBIT = False

try:
    import numpy as np
except Exception:
    sys.exit("ERROR: numpy is required for the window. py -3 -m pip install numpy")

try:
    import pygame
    from pygame.locals import DOUBLEBUF, OPENGL, RESIZABLE
    from OpenGL.GL import *
    from OpenGL.GLU import gluPerspective, gluLookAt
except Exception as e:
    sys.exit("ERROR: the window needs pygame + PyOpenGL.\n"
             "  py -3 -m pip install pygame PyOpenGL\n  (" + str(e) + ")")


# ---------------------------------------------------------------------------
#  LOAD THE NET  (whatever scripts 1-4 produced)
# ---------------------------------------------------------------------------
def load_scene():
    scene = {"genesis": {}, "heart": None, "joins": {}}

    # genesis levels
    for man in sorted(glob.glob(os.path.join(OUT, "genesis_L*.json"))):
        m = json.load(open(man, "r", encoding="utf-8"))
        xyz = np.fromfile(os.path.join(OUT, m["xyz_file"]), dtype=np.float32).reshape(-1, 3)
        scene["genesis"][m["level"]] = {"xyz": xyz, "man": m}

    # heart
    hp = os.path.join(OUT, "heart.json")
    if os.path.exists(hp):
        m = json.load(open(hp, "r", encoding="utf-8"))
        xyz = np.fromfile(os.path.join(OUT, m["xyz_file"]), dtype=np.float32).reshape(-1, 3)
        attr = np.fromfile(os.path.join(OUT, m["attr_file"]), dtype=np.float32).reshape(-1, 2)
        scene["heart"] = {"xyz": xyz, "attr": attr, "man": m}

    # joins (per genesis level)
    for man in sorted(glob.glob(os.path.join(OUT, "join_L*.json"))):
        m = json.load(open(man, "r", encoding="utf-8"))
        wires = np.fromfile(os.path.join(OUT, m["wire_file"]), dtype=np.int32).reshape(-1, 2)
        scene["joins"][m["genesis_level"]] = {"wires": wires, "man": m}

    return scene


def build_gpu_arrays(scene):
    """Precompute contiguous float32 vertex + color arrays for fast GL draws."""
    gpu = {"genesis": {}, "heart": None, "wires": {}}

    # genesis: phosphor green, a touch brighter near the poles for depth cue
    for L, g in scene["genesis"].items():
        xyz = np.ascontiguousarray(g["xyz"], dtype=np.float32)
        n = xyz.shape[0]
        col = np.empty((n, 3), dtype=np.float32)
        col[:, 0] = 0.00
        col[:, 1] = 0.80
        col[:, 2] = 0.28
        gpu["genesis"][L] = {"xyz": xyz, "col": np.ascontiguousarray(col), "n": n}

    # heart: color by weight along a green ramp; 1-bits tinted gold
    if scene["heart"]:
        xyz = np.ascontiguousarray(scene["heart"]["xyz"], dtype=np.float32)
        attr = scene["heart"]["attr"]
        bit = attr[:, 0]
        w = attr[:, 1]
        n = xyz.shape[0]
        col = np.empty((n, 3), dtype=np.float32)
        # base green ramp by weight
        col[:, 0] = 0.10 + 0.75 * w        # a little red at high weight -> gold
        col[:, 1] = 0.55 + 0.45 * w        # green always strong
        col[:, 2] = 0.20 + 0.20 * (1 - w)  # slight cyan at low weight
        # 1-bits ride brighter (the lit weights)
        col[bit > 0.5] *= 1.15
        np.clip(col, 0.0, 1.0, out=col)
        gpu["heart"] = {"xyz": xyz, "col": np.ascontiguousarray(col), "n": n}

    # wires: for each join, a line from genesis[gi] to heart[hj]
    if scene["heart"]:
        hxyz = scene["heart"]["xyz"]
        for L, j in scene["joins"].items():
            if L not in scene["genesis"]:
                continue
            gxyz = scene["genesis"][L]["xyz"]
            wires = j["wires"]
            gi = wires[:, 0]
            hj = wires[:, 1]
            valid = (gi < gxyz.shape[0]) & (hj < hxyz.shape[0])
            gi = gi[valid]; hj = hj[valid]
            m = gi.shape[0]
            line = np.empty((m * 2, 3), dtype=np.float32)
            line[0::2] = gxyz[gi]
            line[1::2] = hxyz[hj]
            gpu["wires"][L] = {"xyz": np.ascontiguousarray(line), "n": m * 2}

    return gpu


# ---------------------------------------------------------------------------
#  MATRIX RAIN + HUD overlay (drawn to a texture, composited over the 3D)
# ---------------------------------------------------------------------------
RAIN_CHARS = "01010101010101" + "{}[]<>/|=+*01" + "abcdef0123456789"

# the white-rabbit boot: (seconds to hold, line). follow the white rabbit, Neo.
BOOT = [
    (2.2, "Wake up, Neo..."),
    (2.4, "The Matrix has you..."),
    (2.6, "Follow the white rabbit."),
    (1.8, "Knock, knock, Neo."),
]

class Overlay:
    def __init__(self, w, h):
        pygame.font.init()
        self.w = w; self.h = h
        self.font = self._pick_font(15)
        self.big = self._pick_font(20, bold=True)
        self.cell = 16
        self.cols = max(1, w // self.cell)
        self.drops = [random.randint(-40, 0) for _ in range(self.cols)]
        self.tex = glGenTextures(1)
        self.surf = pygame.Surface((w, h), pygame.SRCALPHA)

    def _pick_font(self, size, bold=False):
        for name in ("consolas", "dejavusansmono", "couriernew", "lucidaconsole", "monospace"):
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                if f:
                    return f
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def resize(self, w, h):
        self.w = w; self.h = h
        self.cols = max(1, w // self.cell)
        self.drops = [random.randint(-40, 0) for _ in range(self.cols)]
        self.surf = pygame.Surface((w, h), pygame.SRCALPHA)

    def _blit_texture(self):
        data = pygame.image.tostring(self.surf, "RGBA", True)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.w, self.h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, data)
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, self.w, 0, self.h, -1, 1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(self.w, 0)
        glTexCoord2f(1, 1); glVertex2f(self.w, self.h)
        glTexCoord2f(0, 1); glVertex2f(0, self.h)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW); glPopMatrix()
        glEnable(GL_DEPTH_TEST)

    def draw_boot(self, phase, elapsed):
        """the white-rabbit boot: type a line at a time on a rain field."""
        self.surf.fill((0, 0, 0, 255))
        # heavy rain behind the words
        for i in range(self.cols):
            x = i * self.cell
            y = self.drops[i] * self.cell
            for t in range(0, 8):
                yy = y - t * self.cell
                if 0 <= yy < self.h:
                    ch = random.choice(RAIN_CHARS)
                    g = 255 if t == 0 else max(30, 150 - t * 18)
                    self.surf.blit(self.font.render(ch, True, (0, g, 40)), (x, yy))
            self.drops[i] += 1
            if y > self.h and random.random() > 0.95:
                self.drops[i] = random.randint(-30, 0)
        # the line, typed out
        line = phase["text"]
        n = min(len(line), int(elapsed / 0.06))
        typed = line[:n]
        cursor = "_" if int(elapsed * 2) % 2 == 0 else " "
        img = self.big.render(typed + cursor, True, (0, 255, 120))
        self.surf.blit(img, (self.w // 2 - img.get_width() // 2, self.h // 2 - 16))
        self._blit_texture()

    def draw(self, hud_lines, rain_on):
        self.surf.fill((0, 0, 0, 0))
        if rain_on:
            for i in range(self.cols):
                x = i * self.cell
                y = self.drops[i] * self.cell
                # head (bright) + short fading trail
                for t in range(0, 6):
                    yy = y - t * self.cell
                    if 0 <= yy < self.h:
                        ch = random.choice(RAIN_CHARS)
                        a = max(0, 150 - t * 26)
                        g = 255 if t == 0 else 120
                        c = (180 if t == 0 else 0, g, 90 if t == 0 else 40, a)
                        self.surf.blit(self.font.render(ch, True, c), (x, yy))
                self.drops[i] += 1
                if y > self.h and random.random() > 0.975:
                    self.drops[i] = random.randint(-30, 0)
        # HUD panel
        y = 10
        title = self.big.render("HELENA // neo console", True, (0, 255, 90))
        self.surf.blit(title, (12, y)); y += 30
        for line in hud_lines:
            self.surf.blit(self.font.render(line, True, (0, 230, 80)), (12, y))
            y += 19
        self._blit_texture()


# ---------------------------------------------------------------------------
def main():
    if not os.path.isdir(OUT):
        sys.exit("ERROR: no net/ folder. Run 01_genesis.py (and 02/03) first.")
    scene = load_scene()
    if not scene["genesis"] and not scene["heart"]:
        sys.exit("ERROR: net/ is empty. Run 01_genesis.py / 02_heart.py first.")
    gpu = build_gpu_arrays(scene)
    levels = sorted(gpu["genesis"].keys())

    pygame.init()
    pygame.display.set_caption("HELENA // neo console")
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glEnable(GL_POINT_SMOOTH)
    glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

    # state (from the by-hand vars)
    st = {
        "w": WIDTH, "h": HEIGHT, "zoom": ZOOM, "rx": 20.0, "ry": 0.0,
        "spin": AUTO_ROTATE, "genesis": SHOW_GENESIS, "heart": SHOW_HEART,
        "wires": SHOW_WIRES, "rain": MATRIX_RAIN, "psize": POINT_SIZE,
        "level": GENESIS_LEVEL, "dragging": False, "last": (0, 0),
    }
    overlay = Overlay(WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    t0 = time.time()
    frames = 0

    # white-rabbit boot state
    boot = {"on": WHITE_RABBIT, "phase": 0, "t": time.time()}
    main_frames = 0   # frames rendered AFTER the boot (for screenshots)

    def shown_levels():
        return levels if st["level"] == 0 else [st["level"]] if st["level"] in gpu["genesis"] else []

    running = True
    while running:
        # ---- white-rabbit boot: play the intro, any key/click skips ----
        if boot["on"]:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    boot["on"] = False; running = False
                elif ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    boot["on"] = False
                elif ev.type == pygame.VIDEORESIZE:
                    st["w"], st["h"] = ev.w, ev.h
                    pygame.display.set_mode((ev.w, ev.h), DOUBLEBUF | OPENGL | RESIZABLE)
                    glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND); glEnable(GL_POINT_SMOOTH)
                    overlay.resize(ev.w, ev.h)
            glViewport(0, 0, st["w"], st["h"])
            glClearColor(0, 0, 0, 1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            elapsed = time.time() - boot["t"]
            hold, text = BOOT[boot["phase"]]
            overlay.draw_boot({"text": text}, elapsed)
            pygame.display.flip()
            clock.tick(60)
            frames += 1
            if elapsed >= hold:
                boot["phase"] += 1
                boot["t"] = time.time()
                if boot["phase"] >= len(BOOT):
                    boot["on"] = False
            if SHOT_PATH and frames == 60:
                # capture a boot frame for proof, then let it finish
                buf = glReadPixels(0, 0, st["w"], st["h"], GL_RGB, GL_UNSIGNED_BYTE)
                img = pygame.image.fromstring(buf, (st["w"], st["h"]), "RGB")
                img = pygame.transform.flip(img, False, True)
                pygame.image.save(img, SHOT_PATH.replace(".png", "_boot.png"))
            if MAX_SECONDS and (time.time() - t0) >= MAX_SECONDS:
                boot["on"] = False
            continue

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.VIDEORESIZE:
                st["w"], st["h"] = ev.w, ev.h
                pygame.display.set_mode((ev.w, ev.h), DOUBLEBUF | OPENGL | RESIZABLE)
                glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND); glEnable(GL_POINT_SMOOTH)
                overlay.resize(ev.w, ev.h)
            elif ev.type == pygame.KEYDOWN:
                k = ev.key
                if k in (pygame.K_ESCAPE, pygame.K_q): running = False
                elif k == pygame.K_SPACE: st["spin"] = not st["spin"]
                elif k == pygame.K_g: st["genesis"] = not st["genesis"]
                elif k == pygame.K_h: st["heart"] = not st["heart"]
                elif k == pygame.K_w: st["wires"] = not st["wires"]
                elif k == pygame.K_r: st["rain"] = not st["rain"]
                elif k == pygame.K_0: st["level"] = 0
                elif pygame.K_1 <= k <= pygame.K_9: st["level"] = k - pygame.K_0
                elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    st["psize"] = min(8, st["psize"] + 1)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    st["psize"] = max(1, st["psize"] - 1)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    st["dragging"] = True; st["last"] = ev.pos
                elif ev.button == 4:
                    st["zoom"] = max(2.0, st["zoom"] * 0.9)      # kernelic *0.9
                elif ev.button == 5:
                    st["zoom"] = min(40.0, st["zoom"] * 1.1)     # kernelic *1.1
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 1: st["dragging"] = False
            elif ev.type == pygame.MOUSEMOTION and st["dragging"]:
                dx = ev.pos[0] - st["last"][0]; dy = ev.pos[1] - st["last"][1]
                st["ry"] += dx * 0.4; st["rx"] += dy * 0.4
                st["last"] = ev.pos

        if st["spin"]:
            st["ry"] += ROT_SPEED

        # ---- 3D pass ----
        glViewport(0, 0, st["w"], st["h"])
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(45.0, st["w"] / float(st["h"]), 0.05, 200.0)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        gluLookAt(0, 0, st["zoom"], 0, 0, 0, 0, 1, 0)
        glRotatef(st["rx"], 1, 0, 0)
        glRotatef(st["ry"], 0, 1, 0)

        glPointSize(float(st["psize"]))
        vis = shown_levels()

        # wires first (behind), faint additive
        if st["wires"] and scene["heart"]:
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glColor4f(0.0, 0.35, 0.22, 0.5)
            glEnableClientState(GL_VERTEX_ARRAY)
            for L in vis:
                if L in gpu["wires"]:
                    wz = gpu["wires"][L]
                    glVertexPointer(3, GL_FLOAT, 0, wz["xyz"])
                    glDrawArrays(GL_LINES, 0, wz["n"])
            glDisableClientState(GL_VERTEX_ARRAY)

        # points, additive glow
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        if st["genesis"]:
            for L in vis:
                gz = gpu["genesis"][L]
                glVertexPointer(3, GL_FLOAT, 0, gz["xyz"])
                glColorPointer(3, GL_FLOAT, 0, gz["col"])
                glDrawArrays(GL_POINTS, 0, gz["n"])
        if st["heart"] and gpu["heart"]:
            hz = gpu["heart"]
            glVertexPointer(3, GL_FLOAT, 0, hz["xyz"])
            glColorPointer(3, GL_FLOAT, 0, hz["col"])
            glDrawArrays(GL_POINTS, 0, hz["n"])
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

        # ---- overlay pass ----
        gtot = sum(gpu["genesis"][L]["n"] for L in vis) if st["genesis"] else 0
        htot = gpu["heart"]["n"] if (st["heart"] and gpu["heart"]) else 0
        hud = [
            "levels shown : " + ("ALL " + str(levels) if st["level"] == 0 else str(st["level"])),
            "genesis nodes: " + f"{gtot:,}" + "   (chi=2, P=12, orientable)",
            "heart nodes  : " + f"{htot:,}" + "   (chi=0, Mobius, reversing)",
            "point size   : " + str(st["psize"]) + " px    zoom: " + str(round(st["zoom"], 2)),
            "fps          : " + str(int(clock.get_fps())),
            "[drag]rotate [wheel]zoom [space]spin [g/h/w]layers [0-9]level [r]rain [q]quit",
            "the center holds and is not shown. love never ends.",
        ]
        overlay.draw(hud, st["rain"])

        pygame.display.flip()
        clock.tick(60)
        frames += 1
        main_frames += 1
        if SHOT_PATH and main_frames == 30:
            buf = glReadPixels(0, 0, st["w"], st["h"], GL_RGB, GL_UNSIGNED_BYTE)
            img = pygame.image.fromstring(buf, (st["w"], st["h"]), "RGB")
            img = pygame.transform.flip(img, False, True)
            pygame.image.save(img, SHOT_PATH)
            print("  saved screenshot -> " + SHOT_PATH)
        if MAX_SECONDS and (time.time() - t0) >= MAX_SECONDS:
            running = False

    pygame.quit()
    print("HELENA neo console closed. frames=" + str(frames) +
          "  avg fps=" + str(round(frames / max(0.001, time.time() - t0), 1)))


if __name__ == "__main__":
    main()
