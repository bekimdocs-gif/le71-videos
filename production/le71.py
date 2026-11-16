import cairo, math, json, sys, subprocess, os, wave

W, H, FPS = 1080, 1920, 30
RED = (0.851, 0.059, 0.137)
INK = (0.078, 0.078, 0.078)
WHITE = (1, 1, 1)
GREY = (0.29, 0.29, 0.29)
LIGHT = (0.97, 0.97, 0.97)
PINK = (0.992, 0.922, 0.925)
PINK2 = (0.965, 0.835, 0.851)
PINK3 = (0.949, 0.757, 0.78)

BLACK_F = "Barlow Condensed Black"
XB_F = "Barlow Condensed ExtraBold"
BOLD_F = "Barlow Condensed"

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else (1.0 if t >= a else 0.0)
def eo(x): return 1 - (1 - x) ** 3
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ---------- text ----------
def font(ctx, fam, size, italic=True, bold=False):
    ctx.select_font_face(fam, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)

def tw(ctx, s): return ctx.text_extents(s).x_advance

def text(ctx, s, x, y, fam, size, col, align="l", italic=True, bold=False, alpha=1.0):
    font(ctx, fam, size, italic, bold)
    w = tw(ctx, s)
    if align == "c": x -= w / 2
    elif align == "r": x -= w
    ctx.set_source_rgba(*col, alpha)
    ctx.move_to(x, y); ctx.show_text(s); ctx.new_path()
    return w

def wrap(ctx, s, fam, size, maxw, italic=True, bold=False):
    font(ctx, fam, size, italic, bold)
    lines, cur = [], ""
    for wd in s.split():
        tst = (cur + " " + wd).strip()
        if tw(ctx, tst) <= maxw: cur = tst
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

# ---------- shapes ----------
def rect(ctx, x, y, w, h, col, a=1.0):
    ctx.set_source_rgba(*col, a); ctx.rectangle(x, y, w, h); ctx.fill()

def circ(ctx, x, y, r, col, a=1.0):
    ctx.set_source_rgba(*col, a); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()

def poly(ctx, pts, col, a=1.0):
    ctx.set_source_rgba(*col, a); ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.close_path(); ctx.fill()

def line(ctx, x1, y1, x2, y2, col, w, a=1.0):
    ctx.set_source_rgba(*col, a); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x1, y1); ctx.line_to(x2, y2); ctx.stroke()

def skew_band(ctx, x, y, w, h, col, sk=0.21):
    o = h * sk
    poly(ctx, [(x + o, y), (x + w + o, y), (x + w - o, y + h), (x - o, y + h)], col)

def pin(ctx, x, y, s, col):
    # tip at (x,y)
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.set_source_rgb(*col)
    ctx.move_to(0, 0)
    ctx.curve_to(-6, -12, -20, -26, -20, -40)
    ctx.arc(0, -40, 20, math.pi, 2 * math.pi)
    ctx.curve_to(20, -26, 6, -12, 0, 0); ctx.close_path(); ctx.fill()
    circ(ctx, 0, -40, 8, WHITE)
    ctx.restore()

# ---------- characters & vehicles ----------
def walker(ctx, x, y, s, col, t, speed=1.4, body=None):
    body = body or col
    ph = math.sin(t * speed * 2 * math.pi)
    bob = abs(math.sin(t * speed * 2 * math.pi)) * 3 * s
    ctx.save(); ctx.translate(x, y - bob); ctx.scale(s, s)
    a = math.radians(26) * ph
    for ang, c in ((a, INK), (-a, INK)):
        line(ctx, 0, -42, math.sin(ang) * 40, -42 + math.cos(ang) * 40, c, 10)
    line(ctx, 0, -86, 0, -40, body, 13)
    for ang in (-a, a):
        line(ctx, 0, -78, math.sin(ang) * 30, -78 + math.cos(ang) * 30, body, 8)
    circ(ctx, 0, -104, 12, col)
    ctx.restore()

def car(ctx, x, y, s, col, t, flip=False):
    ctx.save(); ctx.translate(x, y); ctx.scale(-s if flip else s, s)
    ctx.set_source_rgb(*col)
    ctx.move_to(-104, -14); ctx.line_to(-104, -30); ctx.curve_to(-100, -42, -84, -44, -76, -44)
    ctx.line_to(-48, -66); ctx.curve_to(-40, -72, -32, -72, -24, -72); ctx.line_to(28, -72)
    ctx.curve_to(36, -72, 42, -70, 48, -64); ctx.line_to(72, -44); ctx.curve_to(96, -42, 104, -36, 104, -24)
    ctx.line_to(104, -14); ctx.close_path(); ctx.fill()
    poly(ctx, [(-40, -62), (-6, -62), (-6, -46), (-62, -46)], WHITE)
    poly(ctx, [(2, -62), (30, -62), (50, -46), (2, -46)], WHITE)
    rect(ctx, 94, -34, 10, 7, (1, .88, .54))
    for wx in (-60, 56):
        circ(ctx, wx, -12, 19, INK); circ(ctx, wx, -12, 7, (.86, .86, .86))
        ang = t * 14
        line(ctx, wx + math.cos(ang) * 16, -12 + math.sin(ang) * 16, wx - math.cos(ang) * 16, -12 - math.sin(ang) * 16, (.86, .86, .86), 3)
    ctx.restore()

def cloud(ctx, x, y, s, col=(0.94, 0.94, 0.94)):
    for dx, dy, rx, ry in ((0, 0, 60, 26), (52, -14, 52, 32), (98, 2, 44, 22)):
        ctx.save(); ctx.translate(x + dx * s, y + dy * s); ctx.scale(rx * s, ry * s)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*col); ctx.fill()

def flag(ctx, x, y, t, w=56, h=34):
    line(ctx, x, y, x, y + 90, (.74, .74, .74), 5)
    ctx.set_source_rgb(*RED)
    wv = math.sin(t * 5) * 6
    ctx.move_to(x, y); ctx.curve_to(x + w * .3, y - wv, x + w * .6, y + wv, x + w, y)
    ctx.line_to(x + w, y + h); ctx.curve_to(x + w * .6, y + h + wv, x + w * .3, y + h - wv, x, y + h)
    ctx.close_path(); ctx.fill()

def street(ctx, t, top):
    """animated street band from y=top to y=top+460"""
    ctx.save(); ctx.rectangle(0, top, W, 470); ctx.clip()
    cloud(ctx, ((t * 30) % 1400) - 220, top + 40, 1.0)
    cloud(ctx, ((t * 20 + 700) % 1400) - 220, top + 90, .7, (0.955, 0.955, 0.955))
    g = top + 380  # ground line
    # church
    rect(ctx, 80, g - 156, 168, 156, PINK2); rect(ctx, 116, g - 252, 68, 252, PINK3)
    poly(ctx, [(116, g - 252), (150, g - 324), (184, g - 252)], PINK3)
    line(ctx, 150, g - 348, 150, g - 322, (.91, .64, .67), 6); line(ctx, 140, g - 338, 160, g - 338, (.91, .64, .67), 6)
    circ(ctx, 216, g - 108, 18, WHITE)
    ctx.set_source_rgb(*WHITE); ctx.move_to(136, g); ctx.line_to(136, g - 60); ctx.arc(150, g - 60, 14, math.pi, 0); ctx.line_to(164, g); ctx.fill()
    # buildings
    rect(ctx, 280, g - 176, 116, 176, (.957, .957, .957))
    for wx in (300, 352):
        for wy in (g - 152, g - 100): rect(ctx, wx, wy, 24, 28, WHITE)
    rect(ctx, 408, g - 216, 100, 216, (.93, .93, .93))
    for wx in (428, 468):
        for wy in (g - 192, g - 140, g - 88): rect(ctx, wx, wy, 20, 24, WHITE)
    # arch gate
    rect(ctx, 552, g - 192, 256, 192, PINK2); rect(ctx, 552, g - 192, 256, 24, PINK3)
    for ax in (584, 692):
        ctx.set_source_rgb(*WHITE); ctx.move_to(ax, g); ctx.line_to(ax, g - 96)
        ctx.arc(ax + 42, g - 96, 42, math.pi, 0); ctx.line_to(ax + 84, g); ctx.fill()
    # town hall
    rect(ctx, 840, g - 172, 188, 172, (.957, .957, .957))
    poly(ctx, [(828, g - 172), (934, g - 228), (1040, g - 172)], (.93, .93, .93))
    for wx in (872, 920, 968): rect(ctx, wx, g - 132, 28, 132, WHITE)
    flag(ctx, 934, g - 320, t)
    # walkers on sidewalk
    rect(ctx, 0, g, W, 10, (.87, .87, .87))
    walker(ctx, ((t * 70) % 1300) - 80, g + 4, .7, INK, t)
    walker(ctx, 1200 - ((t * 55 + 400) % 1300), g + 4, .7, RED, t, 1.2, RED)
    # road
    rect(ctx, 0, g + 10, W, 80, INK)
    off = (t * 220) % 120
    for x in range(-120, W + 120, 120): rect(ctx, x - off, g + 48, 60, 6, WHITE)
    car(ctx, ((t * 330) % 1500) - 200, g + 82, .9, RED, t)
    car(ctx, 1300 - ((t * 240 + 600) % 1500), g + 90, .8, (.6, .6, .6), t, flip=True)
    ctx.restore()


# ---------- common chrome ----------
def header(ctx, t, label):
    text(ctx, "LE 71", 60, 128, BLACK_F, 80, RED)
    font(ctx, XB_F, 40)
    bw = tw(ctx, "FLASH NEWS") + 40
    skew_band(ctx, 224, 80, bw, 54, RED)
    text(ctx, "FLASH NEWS", 244, 122, XB_F, 40, WHITE)
    if label:
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.cos(t * 2 * math.pi / 1.2))
        x = text(ctx, label, 1020, 120, "Inter", 30, INK, "r", italic=False, bold=True)
        circ(ctx, 1020 - x - 24, 110, 10, RED, a)

def wipe_in(ctx, t):
    p = prog(t, 0, .3)
    if p < 1:
        e = eio(p)
        rect(ctx, W * e, 0, W, H, RED)

def ticker(ctx, t, msg):
    y = H - 84
    rect(ctx, 0, y, W, 84, INK)
    font(ctx, "Inter", 32, False, True)
    ww = tw(ctx, msg) + 80
    off = (t * 110) % ww
    ctx.save(); ctx.rectangle(200, y, W - 200, 84); ctx.clip()
    for k in range(3):
        text(ctx, msg, 220 + k * ww - off, y + 54, "Inter", 32, WHITE, italic=False, bold=True)
    ctx.restore()
    skew_band(ctx, -20, y, 220, 84, RED, 0.1)
    text(ctx, "EN BREF", 30, y + 58, XB_F, 46, WHITE)


# ---- illustrations (panel local coords 960x700) ----
PW, PH = 960, 700

def crowd(ctx, t, y, col=INK, n=11):
    for i in range(n):
        x = 40 + i * (PW - 80) / (n - 1)
        b = abs(math.sin(t * 3 + i * 1.3)) * 18
        c = col if i % 3 else RED
        circ(ctx, x, y - 70 - b, 26, c)
        ctx.set_source_rgb(*c); ctx.arc(x, y - b + 20, 50, math.pi, 2 * math.pi); ctx.fill()
        if i % 4 == 1:
            line(ctx, x + 30, y - 40 - b, x + 50, y - 130 - b + math.sin(t * 6 + i) * 12, c, 12)

def il_concert(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .96, .96))
    for i, base in enumerate((200, 480, 760)):
        a = math.sin(t * 1.4 + i * 2) * .25
        ctx.save(); ctx.translate(base, -10); ctx.rotate(a)
        ctx.move_to(-20, 0); ctx.line_to(20, 0); ctx.line_to(170, 620); ctx.line_to(-170, 620); ctx.close_path()
        ctx.set_source_rgba(*RED, .12); ctx.fill(); ctx.restore()
        rect(ctx, base - 30, 0, 60, 26, INK)
    rect(ctx, 0, 470, PW, 30, INK)
    # singer
    sx = 480
    line(ctx, sx + 70, 470, sx + 70, 330, GREY, 6); circ(ctx, sx + 70, 322, 12, INK)
    line(ctx, sx, 470, sx - 24, 400, INK, 14); line(ctx, sx, 470, sx + 24, 400, INK, 14)
    line(ctx, sx, 400, sx, 320, RED, 34)
    arm = math.sin(t * 2.5) * .5
    line(ctx, sx, 335, sx + 62, 325, RED, 14)
    line(ctx, sx, 335, sx - 50 - math.cos(arm) * 10, 290 - math.sin(arm) * 60, RED, 14)
    circ(ctx, sx, 280, 28, INK)
    for i in range(5):
        ph = (t * .45 + i * .2) % 1
        nx = 120 + i * 180 + math.sin(t * 2 + i) * 20
        ny = 440 - ph * 400
        al = 1 - abs(ph - .5) * 2
        circ(ctx, nx, ny, 14, RED, al); line(ctx, nx + 12, ny, nx + 12, ny - 50, RED, 5, al); line(ctx, nx + 12, ny - 50, nx + 34, ny - 40, RED, 5, al)
    crowd(ctx, t, PH)

def il_marche(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98))
    cloud(ctx, ((t * 40) % 1300) - 200, 60, 1)
    for i, sx in enumerate((40, 350, 660)):
        # awning stripes
        for k in range(6):
            rect(ctx, sx + k * 43, 170, 43, 80, RED if k % 2 == 0 else WHITE)
        for k in range(6):
            ctx.set_source_rgb(*(RED if k % 2 == 0 else (.93, .93, .93)))
            ctx.arc(sx + k * 43 + 21.5, 250, 21.5, 0, math.pi); ctx.fill()
        line(ctx, sx + 6, 250, sx + 6, 560, GREY, 8); line(ctx, sx + 252, 250, sx + 252, 560, GREY, 8)
        rect(ctx, sx - 6, 430, 270, 26, (.55, .38, .25)); rect(ctx, sx + 6, 456, 246, 104, (.92, .87, .82))
        if i == 0:
            for k in range(5): circ(ctx, sx + 40 + k * 46, 412, 20, [(1, .55, .1), RED, (.45, .7, .2), (1, .8, .2), (.6, .2, .4)][k])
        elif i == 1:
            for k in range(5):
                bx = sx + 34 + k * 46
                rect(ctx, bx, 330, 24, 100, (.35, .05, .12) if k % 2 else (.85, .78, .4)); rect(ctx, bx + 7, 300, 10, 32, INK)
        else:
            ctx.set_source_rgb(.97, .85, .4); ctx.arc(sx + 130, 430, 80, math.pi, 2 * math.pi); ctx.fill()
            for k in range(3):
                ph = (t * .6 + k * .33) % 1
                ctx.set_source_rgba(.7, .7, .7, 1 - ph); ctx.set_line_width(6)
                bx = sx + 90 + k * 40; by = 330 - ph * 120
                ctx.move_to(bx, by + 40); ctx.curve_to(bx - 20, by + 20, bx + 20, by, bx, by - 20); ctx.stroke()
    rect(ctx, 0, 600, PW, 100, (.87, .87, .87))
    walker(ctx, ((t * 90) % 1200) - 100, 680, 1.1, INK, t)
    walker(ctx, 1100 - ((t * 70 + 500) % 1200), 690, 1.1, RED, t, 1.2, RED)
    walker(ctx, ((t * 60 + 600) % 1200) - 100, 670, .9, GREY, t, 1.5, GREY)

CUR_ITEM = {}

def il_basket(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98))
    rect(ctx, 0, 500, PW, 200, (.93, .80, .62))
    line(ctx, 0, 520, PW, 520, WHITE, 6)
    # scoreboard
    aff = CUR_ITEM.get("affiche")          # ["ÉLAN CHALON", "ST-QUENTIN"] : tableau d'affichage seulement si renseigné
    if aff and len(aff) == 2:
        rect(ctx, 60, 40, 600, 100, INK)
        w1 = text(ctx, aff[0].upper(), 84, 106, XB_F, 48, WHITE)
        w2 = text(ctx, "vs", 84 + w1 + 16, 106, XB_F, 40, RED)
        text(ctx, aff[1].upper(), 84 + w1 + w2 + 32, 106, XB_F, 48, WHITE)
    # hoop
    rect(ctx, 870, 120, 16, 400, GREY)
    rect(ctx, 760, 150, 26, 170, WHITE); ctx.set_source_rgb(*INK); ctx.set_line_width(6); ctx.rectangle(760, 150, 26, 170); ctx.stroke()
    rect(ctx, 786, 230, 84, 12, GREY)
    hx, hy = 700, 290
    # ball arc (period 2.2s)
    T = 2.2; ph = (t % T) / T
    sx, sy = 180, 430
    if ph < .62:
        u = ph / .62
        bx = sx + (hx - sx) * u; by = sy + (hy - 30 - sy) * u - 280 * math.sin(math.pi * u)
    else:
        u = (ph - .62) / .38
        bx = hx; by = hy - 30 + u * 230
        if by > 470: by = 470 - abs(math.sin(u * 8)) * 40 * (1 - u)
    # player
    px = 170
    jump = max(0, math.sin(min(ph, .25) / .25 * math.pi)) * 40 if ph < .25 else 0
    line(ctx, px, 500 - jump, px - 20, 440 - jump, INK, 14); line(ctx, px, 500 - jump, px + 20, 440 - jump, INK, 14)
    line(ctx, px, 440 - jump, px, 360 - jump, RED, 36)
    line(ctx, px, 370 - jump, px + 30, 300 - jump, RED, 14)
    circ(ctx, px, 320 - jump, 30, INK)
    circ(ctx, bx, by, 34, (.93, .45, .1))
    ctx.set_source_rgb(*INK); ctx.set_line_width(4)
    ctx.arc(bx, by, 34, 0, 2 * math.pi); ctx.stroke(); line(ctx, bx - 34, by, bx + 34, by, INK, 4); line(ctx, bx, by - 34, bx, by + 34, INK, 4)
    # rim + net drawn over ball
    line(ctx, hx - 50, hy, hx + 70, hy, RED, 10)
    sw = math.sin(t * 10) * 6 if .6 < ph < .85 else 0
    for k in range(5):
        x0 = hx - 46 + k * 28
        line(ctx, x0, hy + 4, x0 + 8 + sw, hy + 80, (.8, .8, .8), 4)
    crowd(ctx, t, PH, INK, 9)

def curtain(ctx, x, w, t, left=True):
    ctx.set_source_rgb(.72, .04, .1)
    folds = 5
    for k in range(folds):
        fx = x + k * w / folds
        sway = math.sin(t * 1.5 + k) * 6
        ctx.set_source_rgb(*((.72, .04, .1) if k % 2 else RED))
        ctx.move_to(fx, 0); ctx.line_to(fx + w / folds, 0)
        ctx.curve_to(fx + w / folds + sway, 300, fx + w / folds - sway, 500, fx + w / folds, PH)
        ctx.line_to(fx, PH); ctx.curve_to(fx - sway, 500, fx + sway, 300, fx, 0); ctx.fill()

def il_humour(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.12, .12, .12))
    pr = .85 + .15 * math.sin(t * 3)
    ctx.save(); ctx.translate(480, 560); ctx.scale(260 * pr, 70 * pr); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgba(1, .95, .8, .25); ctx.fill()
    ctx.move_to(420, 0); ctx.line_to(540, 0); ctx.line_to(740, 560); ctx.line_to(220, 560); ctx.close_path()
    ctx.set_source_rgba(1, .95, .8, .10); ctx.fill()
    rect(ctx, 0, 600, PW, 100, (.25, .18, .12))
    # mic stand
    line(ctx, 480, 600, 480, 330, (.75, .75, .75), 8); line(ctx, 440, 600, 520, 600, (.75, .75, .75), 10)
    ctx.save(); ctx.translate(480, 310); ctx.rotate(-.3); ctx.scale(1, 1.4); ctx.arc(0, 0, 26, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(.85, .85, .85); ctx.fill()
    curtain(ctx, 0, 200, t); curtain(ctx, PW - 200, 200, t)
    rect(ctx, 0, 0, PW, 60, RED)
    for i in range(4):
        ph = (t * .7 + i * .25) % 1
        s = eback(clamp(ph * 3)) * (1 - clamp((ph - .7) / .3))
        if s <= 0: continue
        x = [310, 650, 260, 700][i]; y = [190, 160, 470, 440][i]
        ctx.save(); ctx.translate(x, y); ctx.rotate([-.2, .15, .1, -.15][i]); ctx.scale(s, s)
        text(ctx, "HA HA !", 0, 0, BLACK_F, 86, (1, .82, .2), "c")
        ctx.restore()

def il_theatre(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.99, .95, .88))
    rect(ctx, 0, 520, PW, 180, (.76, .6, .45))
    # window
    rect(ctx, 120, 110, 220, 200, (.78, .89, .97)); ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(12); ctx.rectangle(120, 110, 220, 200); ctx.stroke()
    line(ctx, 230, 110, 230, 310, WHITE, 8); line(ctx, 120, 210, 340, 210, WHITE, 8)
    # clock
    cx, cy = 720, 190
    circ(ctx, cx, cy, 70, (.55, .38, .25)); circ(ctx, cx, cy, 56, WHITE)
    a1 = t * .6; a2 = t * 6
    line(ctx, cx, cy, cx + math.sin(a1) * 34, cy - math.cos(a1) * 34, INK, 8)
    line(ctx, cx, cy, cx + math.sin(a2) * 48, cy - math.cos(a2) * 48, RED, 5)
    rect(ctx, cx - 6, cy + 70, 12, 120, (.55, .38, .25))
    pa = math.sin(t * 3) * .4
    line(ctx, cx, cy + 90, cx + math.sin(pa) * 90, cy + 90 + math.cos(pa) * 90, (.85, .7, .2), 6); circ(ctx, cx + math.sin(pa) * 90, cy + 90 + math.cos(pa) * 90, 16, (.85, .7, .2))
    # table + pot + steam
    rect(ctx, 260, 430, 440, 26, (.55, .38, .25)); rect(ctx, 290, 456, 22, 140, (.55, .38, .25)); rect(ctx, 648, 456, 22, 140, (.55, .38, .25))
    rect(ctx, 400, 350, 160, 80, (.25, .25, .25)); rect(ctx, 384, 342, 192, 16, (.35, .35, .35))
    for k in range(3):
        ph = (t * .6 + k * .33) % 1
        ctx.set_source_rgba(.6, .6, .6, 1 - ph); ctx.set_line_width(7)
        bx = 440 + k * 40; by = 300 - ph * 140
        ctx.move_to(bx, by + 40); ctx.curve_to(bx - 22, by + 20, bx + 22, by, bx, by - 22); ctx.stroke()
    # curtains opening
    o = eo(prog(t, .3, 2.0))
    cw = 480 - 330 * o
    curtain(ctx, 0, cw, t); curtain(ctx, PW - cw, cw, t)
    rect(ctx, 0, 0, PW, 60, RED)

ILL = dict(concert=il_concert, marche=il_marche, basket=il_basket, humour=il_humour, theatre=il_theatre)

# =====================================================================
#  LE 71 FLASH NEWS — moteur d'épisode (matin / soir / météo / spécial)
#  Usage : python3 le71.py episode.json sortie.mp4 [--stills dossier]
# =====================================================================
import urllib.request, urllib.parse, unicodedata, shutil, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EP = {}

# ---------- carte exacte du 71 ----------
_M = None
def M():
    global _M
    if _M is None:
        _M = json.load(open(os.path.join(HERE, "d71.json")))
    return _M

def proj(lon, lat):
    m = M()
    return ((lon * m["k"] - m["x0"]) * m["sc"], (-lat - m["y0"]) * m["sc"])

def draw_map(ctx, x, y, w, t_draw=1.0, t_fill=1.0, stroke=6):
    P = [(x + px * w, y + py * w) for px, py in M()["pts"]]
    ctx.new_path(); ctx.move_to(*P[0])
    for p in P[1:]: ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*PINK, t_fill); ctx.fill_preserve()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if t_draw < 1:
        ctx.new_path(); n = max(2, int(len(P) * t_draw)); ctx.move_to(*P[0])
        for p in P[1:n]: ctx.line_to(*p)
    ctx.set_source_rgb(*RED); ctx.set_line_width(stroke); ctx.stroke()
    return lambda lon, lat: (x + proj(lon, lat)[0] * w, y + proj(lon, lat)[1] * w)

# ---------- communes : coordonnées via geo.api.gouv.fr ----------
FALLBACK = {"macon": (4.828, 46.307), "chalon-sur-saone": (4.853, 46.781), "autun": (4.299, 46.951),
            "le creusot": (4.424, 46.801), "montceau-les-mines": (4.366, 46.668), "paray-le-monial": (4.120, 46.451),
            "charolles": (4.276, 46.435), "digoin": (3.982, 46.481), "louhans": (5.225, 46.627), "tournus": (4.909, 46.563),
            "cluny": (4.659, 46.434), "charnay-les-macon": (4.787, 46.307), "gueugnon": (4.063, 46.604),
            "bourbon-lancy": (3.769, 46.622), "chagny": (4.753, 46.910), "saint-marcel": (4.894, 46.776)}

def norm(s):
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("’", "'").replace(" ", "-").replace("--", "-")

def locate(commune):
    key = norm(commune)
    for k, v in FALLBACK.items():
        if norm(k) == key: return v
    try:
        q = urllib.parse.urlencode({"nom": commune, "codeDepartement": "71", "fields": "nom,centre", "limit": 1})
        r = json.load(urllib.request.urlopen("https://geo.api.gouv.fr/communes?" + q, timeout=15))
        if r: return tuple(r[0]["centre"]["coordinates"])
    except Exception as e:
        print("geo.api indisponible :", e)
    print("!! commune introuvable, centre du 71 utilisé :", commune)
    return (4.55, 46.65)

# ---------- illustrations supplémentaires ----------
def il_route(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 40) % 1300) - 200, 70, 1)
    rect(ctx, 0, 420, PW, 280, (.85, .92, .80))
    rect(ctx, 0, 470, PW, 150, INK)
    off = (t * 260) % 120
    for x in range(-120, PW + 120, 120): rect(ctx, x - off, 540, 60, 8, WHITE)
    # panneau travaux
    poly(ctx, [(760, 250), (840, 390), (680, 390)], (1, .75, .1)); text(ctx, "!", 760, 380, BLACK_F, 110, INK, "c")
    line(ctx, 760, 390, 760, 470, GREY, 8)
    for i in range(4):
        cx = 120 + i * 90; rect(ctx, cx - 14, 430, 28, 40, RED if i % 2 == 0 else WHITE); poly(ctx, [(cx - 22, 470), (cx + 22, 470), (cx, 410)], RED)
    car(ctx, ((t * 300) % 1300) - 150, 600, 1.0, RED, t)
    car(ctx, 1150 - ((t * 220 + 500) % 1300), 535, .85, (.6, .6, .6), t, flip=True)

def il_secours(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98))
    rect(ctx, 0, 520, PW, 180, INK)
    off = (t * 300) % 120
    for x in range(-120, PW + 120, 120): rect(ctx, x - off, 600, 60, 8, WHITE)
    x = ((t * 260) % 1400) - 300
    ctx.save(); ctx.translate(x, 0)
    rect(ctx, 0, 400, 260, 140, RED); poly(ctx, [(260, 400), (330, 400), (380, 470), (380, 540), (260, 540)], RED)
    poly(ctx, [(276, 416), (324, 416), (360, 470), (276, 470)], WHITE)
    rect(ctx, 20, 380, 220, 14, (.75, .75, .75)); rect(ctx, 0, 470, 380, 10, WHITE)
    blink = int(t * 4) % 2
    circ(ctx, 300, 388, 16, (.12, .36, .85) if blink else RED)
    for wx in (70, 310):
        circ(ctx, wx, 545, 30, INK); circ(ctx, wx, 545, 11, (.86, .86, .86))
    ctx.restore()
    ctx.set_source_rgba(.12, .36, .85, .08 + .1 * (int(t * 4) % 2)); ctx.rectangle(0, 0, PW, PH); ctx.fill()

def il_mairie(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 30) % 1300) - 200, 60, 1.1)
    rect(ctx, 0, 600, PW, 100, (.87, .87, .87))
    rect(ctx, 220, 260, 520, 340, (.96, .96, .96)); poly(ctx, [(200, 260), (480, 140), (760, 260)], (.92, .92, .92))
    for i in range(5): rect(ctx, 260 + i * 92, 300, 50, 300, WHITE)
    rect(ctx, 400, 200, 160, 40, PINK2); text(ctx, "MAIRIE", 480, 233, XB_F, 36, RED, "c")
    flag(ctx, 480, 40, t, 80, 48)
    walker(ctx, ((t * 80) % 1200) - 100, 690, 1.1, INK, t); walker(ctx, 1100 - ((t * 60 + 400) % 1200), 690, 1.1, RED, t, 1.2, RED)

def il_economie(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98))
    rect(ctx, 0, 560, PW, 140, (.87, .87, .87))
    rect(ctx, 120, 300, 520, 260, (.93, .93, .93))
    for i in range(4): poly(ctx, [(120 + i * 130, 300), (250 + i * 130, 300), (250 + i * 130, 230)], (.88, .88, .88))
    rect(ctx, 700, 160, 60, 400, GREY)
    for k in range(4):
        ph = (t * .5 + k * .25) % 1
        circ(ctx, 730 + ph * 60, 140 - ph * 160, 26 + ph * 30, (.8, .8, .8), 1 - ph)
    for i in range(4): rect(ctx, 160 + i * 120, 400, 70, 60, (.78, .89, .97))
    rect(ctx, 300, 480, 90, 80, RED)
    # graphique qui monte
    ctx.set_source_rgb(*RED); ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    pts = [(780, 520), (830, 470), (870, 490), (930, 400)]
    n = clamp((t % 4) / 2)
    ctx.move_to(*pts[0])
    for a, b in zip(pts, pts[1:]):
        ctx.line_to(a[0] + (b[0] - a[0]) * n, a[1] + (b[1] - a[1]) * n)
    ctx.stroke()

def il_campagne(ctx, t):
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98))
    ctx.save(); ctx.translate(820, 120); ctx.rotate(t * .5)
    for i in range(8): ctx.rotate(math.pi / 4); line(ctx, 0, 58, 0, 80, (1, .79, .3), 8)
    ctx.restore(); circ(ctx, 820, 120, 48, (1, .79, .3))
    ctx.set_source_rgb(.89, .94, .85); ctx.move_to(0, 400); ctx.curve_to(300, 300, 600, 420, PW, 360); ctx.line_to(PW, PH); ctx.line_to(0, PH); ctx.fill()
    ctx.set_source_rgb(.81, .89, .75); ctx.move_to(0, 520); ctx.curve_to(300, 450, 650, 560, PW, 500); ctx.line_to(PW, PH); ctx.line_to(0, PH); ctx.fill()
    x = ((t * 90) % 1300) - 200; bump = math.sin(t * 20) * 2
    ctx.save(); ctx.translate(x, 600 + bump)
    rect(ctx, 60, -150, 80, 70, RED); rect(ctx, 72, -138, 56, 40, WHITE); rect(ctx, 0, -84, 190, 40, RED); rect(ctx, 20, -130, 14, 50, GREY)
    for wx, r in ((90, 50), (10, 28)):
        circ(ctx, wx, -30 + (50 - r), r, INK); circ(ctx, wx, -30 + (50 - r), r * .4, (.86, .86, .86))
    ctx.restore()

def il_generic(ctx, t):
    rect(ctx, 0, 0, PW, PH, WHITE)
    ctx.save(); ctx.translate(0, PH - 520); street(ctx, t, 0); ctx.restore()
    text(ctx, "LE 71", PW / 2, 200, BLACK_F, 160, RED, "c", alpha=.12)

ILL.update(route=il_route, secours=il_secours, mairie=il_mairie, economie=il_economie, campagne=il_campagne,
           sport=il_basket, culture=il_theatre, generic=il_generic)

# ---------- météo : pictos ----------
def wx_icon(ctx, x, y, s, kind, t):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    def cl(dx=0, dy=0, col=(.62, .66, .70)):
        ctx.set_source_rgb(*col)
        for cx, cy, r in ((-18, 6, 16), (2, -4, 22), (22, 6, 16)): ctx.new_path(); ctx.arc(cx + dx, cy + dy, r, 0, 2 * math.pi); ctx.fill()
        rect(ctx, -34 + dx, 6 + dy, 72, 16, col)
    if kind in ("soleil", "eclaircies"):
        sx, sy = (0, 0) if kind == "soleil" else (14, -14)
        ctx.save(); ctx.translate(sx, sy); ctx.rotate(t * .8)
        for i in range(8): ctx.rotate(math.pi / 4); line(ctx, 0, 26, 0, 38, (1, .69, 0), 5)
        ctx.restore(); circ(ctx, sx, sy, 20, (1, .69, 0))
    if kind in ("eclaircies", "nuages", "pluie", "orage", "neige"):
        col = (.43, .48, .53) if kind in ("pluie", "orage") else (.62, .66, .70)
        cl(math.sin(t * 1.5) * 3, 0, col)
    if kind == "pluie":
        for i, dx in enumerate((-16, 2, 20)):
            ph = (t * 1.6 + i * .33) % 1
            line(ctx, dx, 30 + ph * 18, dx - 4, 38 + ph * 18, (.12, .36, .85), 4, 1 - ph)
    if kind == "neige":
        for i, dx in enumerate((-16, 2, 20)):
            ph = (t * .8 + i * .33) % 1; circ(ctx, dx + math.sin(t * 3 + i) * 3, 30 + ph * 20, 4, (.6, .75, .95), 1 - ph)
    if kind == "orage":
        poly(ctx, [(2, 24), (-10, 46), (0, 46), (-6, 62), (14, 38), (4, 38), (10, 24)], (1, .8, .1), .4 + .6 * (int(t * 3) % 2))
    ctx.restore()

# ---------- scènes ----------
def scene_intro(ctx, t, dur):
    """générique LE 71 identique et COURT (1,5 s), puis l'accroche du jour à l'écran"""
    rect(ctx, 0, 0, W, H, WHITE)
    rect(ctx, 0, 0, W * eio(prog(t, 0, .3)), 28, RED)
    acc = EP.get("accroche")
    k = eio(prog(t, 1.5, 1.9)) if acc else 0.0      # 0 = générique plein écran, 1 = logo en haut + accroche
    a = 0.3 + 0.7 * (0.5 + 0.5 * math.cos(t * 2 * math.pi / 1.2))
    circ(ctx, 92, 112, 12, RED, a)
    text(ctx, "EN DIRECT DU 71", 116, 124, "Inter", 32, INK, italic=False, bold=True)
    text(ctx, EP.get("date_label", "").upper(), 1020, 124, "Inter", 28, INK, "r", italic=False, bold=True)
    # logo : grand au centre puis remonte et rétrécit
    ly = 760 + (330 - 760) * k; ls = 1 - .45 * k
    p = prog(t, .05, .45)
    if p > 0:
        s = (.6 + .4 * eback(p)) * ls
        ctx.save(); ctx.translate(W / 2, ly); ctx.scale(s, s)
        text(ctx, "LE 71", 0, 0, BLACK_F, 400, RED, "c", alpha=clamp(p * 2)); ctx.restore()
    q = eo(prog(t, .35, .8))
    if q > 0:
        ctx.save(); ctx.translate(W / 2, ly); ctx.scale(ls, ls); ctx.translate(-W / 2, -760)
        ctx.set_source_rgb(*RED); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        n = 60; ctx.new_path()
        for i in range(int(n * q) + 1):
            u = i / n
            bx = (1 - u) ** 3 * 120 + 3 * (1 - u) ** 2 * u * 360 + 3 * (1 - u) * u * u * 720 + u ** 3 * 960
            by = (1 - u) ** 3 * 860 + 3 * (1 - u) ** 2 * u * 800 + 3 * (1 - u) * u * u * 792 + u ** 3 * 808
            (ctx.move_to if i == 0 else ctx.line_to)(bx, by)
        ctx.stroke()
        b = eo(prog(t, .6, 1.0))
        font(ctx, XB_F, 84); bw = tw(ctx, "FLASH NEWS") + 56
        dx = -600 * (1 - b)
        ctx.save(); ctx.rectangle(0, 880, W, 140); ctx.clip()
        skew_band(ctx, 110 + dx, 900, bw, 104, RED); text(ctx, "FLASH NEWS", 138 + dx, 982, XB_F, 84, WHITE)
        ctx.restore()
        rect(ctx, 110 + bw + 30, 908, 6, 88, INK, b)
        text(ctx, "SAÔNE-ET-LOIRE", 110 + bw + 60, 982, BOLD_F, 66, INK, alpha=b)
        ctx.restore()
    if acc and k > 0:
        tag = EP.get("accroche_tag", "À LA UNE")
        font(ctx, XB_F, 52); tgw = tw(ctx, tag) + 50
        skew_band(ctx, 70 - 300 * (1 - k), 720, tgw, 76, RED); text(ctx, tag, 95 - 300 * (1 - k), 776, XB_F, 52, WHITE)
        size = 128
        lines = wrap(ctx, acc.upper(), BLACK_F, size, 940)
        while len(lines) > 4 and size > 80:
            size -= 8; lines = wrap(ctx, acc.upper(), BLACK_F, size, 940)
        y = 820 + size
        for i, ln in enumerate(lines):
            lp = eo(prog(t, 1.6 + i * .12, 2.0 + i * .12))
            text(ctx, ln, 70 + 60 * (1 - lp), y, BLACK_F, size, INK, alpha=lp); y += size * .95
    street(ctx, t, H - 520)
    rect(ctx, 0, H - 28, W * eio(prog(t, 0, .3)), 28, RED)

FORMATS = {
    "matin": dict(title=["LE RÉVEIL 71"], sub="L'actu pour bien commencer la journée", label="LE RÉVEIL 71", sky=(1, .957, .878), night=False),
    "soir": dict(title=["LE 20H", "DU 71"], sub="L'essentiel de la journée", label="LE 20H DU 71", sky=(.078, .106, .176), night=True),
    "special": dict(title=["FLASH", "SPÉCIAL"], sub="L'actu de la Saône-et-Loire", label="FLASH NEWS", sky=(1, .92, .925), night=False),
    "meteo": dict(title=["LA MÉTÉO", "DE LA SEMAINE"], sub="En Saône-et-Loire", label="MÉTÉO", sky=(.88, .94, 1), night=False),
    "alerte": dict(title=["ALERTE 71"], sub="Information importante", label="ALERTE 71", sky=(1, .92, .925), night=False),
}

def scene_alerte(ctx, t, dur):
    """ouverture choc du format ALERTE 71 : fond rouge, gyrophare, titre qui claque"""
    on = int(t * 4) % 2
    rect(ctx, 0, 0, W, H, RED)
    rect(ctx, 0, 0, W, H, (.62, .03, .09), .35 if on else 0)
    for i in range(14):
        rect(ctx, -200 + i * 160 - (t * 240) % 160, 0, 70, 70, WHITE, .12)
        rect(ctx, -200 + i * 160 + (t * 240) % 160, H - 70, 70, 70, WHITE, .12)
    circ(ctx, W / 2, 360, 70 + 10 * on, (.12, .36, .85) if on else WHITE)
    rect(ctx, W / 2 - 110, 420, 220, 50, INK)
    p = eback(prog(t, .1, .5))
    ctx.save(); ctx.translate(W / 2, 820); ctx.scale(max(p, .01), max(p, .01))
    text(ctx, "ALERTE", 0, 0, BLACK_F, 260, WHITE, "c"); text(ctx, "71", 0, 230, BLACK_F, 260, WHITE, "c")
    ctx.restore()
    q = eo(prog(t, .5, .9))
    font(ctx, XB_F, 60); bw = tw(ctx, "FLASH NEWS · SAÔNE-ET-LOIRE") + 60
    rect(ctx, (W - bw) / 2, 1160 + 40 * (1 - q), bw, 96, WHITE, q)
    text(ctx, "FLASH NEWS · SAÔNE-ET-LOIRE", W / 2, 1228 + 40 * (1 - q), XB_F, 60, RED, "c", alpha=q)
    it = EP["items"][0]
    r = eo(prog(t, .9, 1.4))
    for i, ln in enumerate(wrap(ctx, it.get("short", it["title"]).upper(), BLACK_F, 84, 940)[:2]):
        text(ctx, ln, W / 2, 1420 + i * 90 + 30 * (1 - r), BLACK_F, 84, WHITE, "c", alpha=r)
    text(ctx, (EP.get("date_label", "") + "  ·  " + it.get("commune", "")).upper(), W / 2, 1660, "Inter", 36, WHITE, "c", italic=False, bold=True, alpha=r)

def sky_band(ctx, t, f):
    rect(ctx, 0, 0, W, 560, f["sky"])
    if f["night"]:
        for i, (sx, sy) in enumerate(((120, 200), (280, 300), (460, 160), (600, 320), (900, 360), (1000, 200), (760, 120))):
            circ(ctx, sx, sy, 5, WHITE, .3 + .7 * abs(math.sin(t * 1.5 + i)))
        ctx.save(); ctx.translate(820, 260)
        ctx.set_source_rgb(.96, .9, .72); ctx.arc(0, 0, 70, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgb(*f["sky"]); ctx.arc(34, -22, 62, 0, 2 * math.pi); ctx.fill(); ctx.restore()
    else:
        r = eo(prog(t, 0, 2.5)); sy = 520 - 300 * r
        ctx.save(); ctx.translate(540, sy); ctx.rotate(t * .4)
        for i in range(10): ctx.rotate(math.pi / 5); line(ctx, 0, 130, 0, 175, (1, .69, 0), 12)
        ctx.restore(); circ(ctx, 540, sy, 110, (1, .69, 0))
    # toits
    g = 560
    col = (.16, .16, .16) if f["night"] else (.96, .84, .85)
    col2 = (.14, .14, .14) if f["night"] else (.93, .89, .83)
    for x, w, h, c in ((40, 140, 160, col), (220, 110, 190, col2), (350, 160, 120, col), (560, 120, 200, col2), (720, 150, 140, col), (900, 130, 210, col2)):
        rect(ctx, x, g - h, w, h, c)
        if f["night"]:
            for k in range(2):
                on = int(t * .7 + x + k) % 3 != 0
                rect(ctx, x + 24 + k * 50, g - h + 30, 26, 30, (1, .84, .42) if on else (.25, .25, .25))
    rect(ctx, 0, g - 12, W, 12, RED if f["night"] else INK)

def scene_ouverture(ctx, t, dur):
    """habillage du format + sommaire + carte des lieux"""
    f = dict(FORMATS[EP["format"]])
    if EP.get("titre"): f["title"] = EP["titre"]
    if EP.get("sous_titre"): f["sub"] = EP["sous_titre"]
    rect(ctx, 0, 0, W, H, WHITE)
    sky_band(ctx, t, f)
    hc = WHITE if f["night"] else RED
    text(ctx, "LE 71", 60, 110, BLACK_F, 72, hc)
    font(ctx, XB_F, 36); bw = tw(ctx, "FLASH NEWS") + 36
    skew_band(ctx, 214, 66, bw, 50, RED); text(ctx, "FLASH NEWS", 232, 104, XB_F, 36, WHITE)
    text(ctx, EP.get("date_label", "").upper(), 1020, 104, "Inter", 28, WHITE if f["night"] else INK, "r", italic=False, bold=True)
    p = eback(prog(t, .2, .8))
    y = 690
    for ln in f["title"]:
        ctx.save(); ctx.translate(60, y); ctx.scale(max(p, .01), max(p, .01)); text(ctx, ln, 0, 0, BLACK_F, 150, RED); ctx.restore(); y += 140
    text(ctx, f["sub"], 62, y - 60, XB_F, 54, INK, alpha=prog(t, .6, 1.0))
    y += 10
    text(ctx, "AU SOMMAIRE", 62, y, "Inter", 30, GREY, italic=False, bold=True, alpha=prog(t, .8, 1.1)); y += 30
    items = EP["items"]
    for i, it in enumerate(items):
        rp = eo(prog(t, 1.0 + i * .35, 1.4 + i * .35))
        if rp <= 0: y += 116; continue
        dx = 160 * (1 - rp)
        tag = it.get("tag", str(i + 1))
        font(ctx, XB_F, 44); tw_ = max(110, tw(ctx, tag) + 40)
        rect(ctx, 60 + dx, y, tw_, 96, RED, rp); text(ctx, tag, 60 + dx + tw_ / 2, y + 64, XB_F, 44, WHITE, "c", alpha=rp)
        ctx.set_source_rgba(*RED, rp); ctx.set_line_width(5); ctx.rectangle(60 + dx + tw_, y + 2.5, 960 - tw_ - 2.5, 91); ctx.stroke()
        ttl = wrap(ctx, it.get("short", it["title"]), "Inter", 34, 960 - tw_ - 50, italic=False, bold=True)[0]
        text(ctx, ttl, 60 + dx + tw_ + 24, y + 60, "Inter", 34, INK, italic=False, bold=True, alpha=rp)
        y += 116
    # carte des lieux
    top = y + 20; avail = H - 100 - top
    mw = min(560, avail / M()["h"])
    mx = (W - mw) / 2
    md = eo(prog(t, .8, 1.8)); mf = prog(t, 1.4, 2.0)
    to_xy = draw_map(ctx, mx, top, mw, md, mf, 5)
    seen, placed, k = set(), [], 0
    for it in items:
        lbl = it.get("label_carte", it["commune"])
        if lbl in seen: continue
        seen.add(lbl)
        pp = prog(t, 1.6 + k * .2, 2.0 + k * .2)
        x0, y0 = to_xy(*it["lonlat"])
        font(ctx, XB_F, 30); lw = tw(ctx, lbl) + 18; lh = 40
        cands = [(x0 + 22, y0 - 60), (x0 - 22 - lw, y0 - 60), (x0 + 22, y0 + 4), (x0 - 22 - lw, y0 + 4), (x0 - lw / 2, y0 - 110), (x0 - lw / 2, y0 + 30)]
        lx, ly = cands[0]
        for cx, cy in cands:
            if cx < 10 or cx + lw > W - 10: continue
            if all(cx + lw < px or cx > px + pw or cy + lh < py or cy > py + ph for px, py, pw, ph in placed):
                lx, ly = cx, cy; break
        placed.append((lx, ly, lw, lh))
        if pp > 0:
            pin(ctx, x0, y0 - 120 * (1 - eback(pp)), .8, RED)
            lb = eo(prog(t, 1.8 + k * .2, 2.1 + k * .2))
            rect(ctx, lx, ly, lw, lh, INK, lb); text(ctx, lbl, lx + 9, ly + 30, XB_F, 30, WHITE, alpha=lb)
        k += 1
    rect(ctx, 0, H - 28, W, 28, RED)
    wipe_in(ctx, t)

def scene_item(ctx, t, dur, it, idx, total):
    rect(ctx, 0, 0, W, H, WHITE)
    rect(ctx, 0, 0, W * clamp(t / dur), 12, RED)
    header(ctx, t, f"{FORMATS[EP['format']]['label']} · {idx}/{total}")
    px, py = 60, 180
    ctx.save(); ctx.rectangle(px, py, PW, PH); ctx.clip(); ctx.translate(px, py)
    z = 1 + .04 * (t / dur)
    ctx.translate(PW / 2, PH / 2); ctx.scale(z, z); ctx.translate(-PW / 2, -PH / 2)
    global CUR_ITEM; CUR_ITEM = it
    ILL.get(it.get("theme", "generic"), il_generic)(ctx, t)
    ctx.restore()
    ctx.set_source_rgb(*RED); ctx.set_line_width(8); ctx.rectangle(px, py, PW, PH); ctx.stroke()
    nb = eback(prog(t, .3, .8))
    if nb > 0:
        ctx.save(); ctx.translate(px + 90, py + PH - 10); ctx.scale(nb, nb)
        rect(ctx, -90, -90, 180, 180, RED); text(ctx, str(idx), 0, 62, BLACK_F, 190, WHITE, "c"); ctx.restore()
    db = eo(prog(t, .5, 1.0))
    band = it.get("band", it.get("tag", "")).upper()
    if band:
        font(ctx, XB_F, 56); bw = tw(ctx, band) + 60
        ctx.save(); ctx.rectangle(0, 920, W, 110); ctx.clip()
        dx = -(bw + 300) * (1 - db)
        skew_band(ctx, 280 + dx, 930, bw, 84, INK); text(ctx, band, 310 + dx, 993, XB_F, 56, WHITE)
        ctx.restore()
    tp = eo(prog(t, .8, 1.3))
    size = 112
    lines = wrap(ctx, it["title"].upper(), BLACK_F, size, 950)
    while len(lines) > 3 and size > 70:
        size -= 8; lines = wrap(ctx, it["title"].upper(), BLACK_F, size, 950)
    y = 1150
    for ln in lines:
        text(ctx, ln, 60, y + 40 * (1 - tp), BLACK_F, size, INK, alpha=tp); y += size * .96
    dp = eo(prog(t, 1.2, 1.7))
    for ln in wrap(ctx, it.get("desc", ""), "Inter Medium", 42, 950, italic=False)[:3]:
        text(ctx, ln, 62, y + 10 + 30 * (1 - dp), "Inter Medium", 42, (.2, .2, .2), italic=False, alpha=dp); y += 58
    mp = eo(prog(t, 1.5, 2.1))
    mtop = max(1500, y + 30)
    to_xy = draw_map(ctx, 760, mtop, 260, 1.0, mp, 4)
    tx, ty = to_xy(*it["lonlat"])
    pp = prog(t, 1.9, 2.4)
    if pp > 0:
        pin(ctx, tx, ty - 80 * (1 - eback(pp)), .8, RED)
        rr = (t * .9) % 1
        ctx.new_path(); ctx.set_source_rgba(*RED, 1 - rr); ctx.set_line_width(4); ctx.arc(tx, ty, 10 + rr * 40, 0, 2 * math.pi); ctx.stroke()
    pl = eo(prog(t, 1.7, 2.2))
    yy = max(y + 50, 1560)
    pin(ctx, 84, yy + 6, .8, RED)
    for ln in wrap(ctx, it.get("place", it["commune"]), XB_F, 58, 600)[:2]:
        text(ctx, ln, 124 - 30 * (1 - pl), yy, XB_F, 58, RED, alpha=pl); yy += 64
    if it.get("source"):
        text(ctx, "Source : " + it["source"], 126, yy + 6, "Inter", 30, GREY, italic=False, bold=True, alpha=pl)
    ticker(ctx, t, EP.get("ticker", "Abonnez-vous à LE 71 Flash News  •  L'actu de la Saône-et-Loire  •"))
    wipe_in(ctx, t)

def scene_meteo_carte(ctx, t, dur):
    mt = EP["meteo"]
    rect(ctx, 0, 0, W, H, WHITE)
    header(ctx, t, "MÉTÉO")
    p = eback(prog(t, .2, .8))
    ctx.save(); ctx.translate(60, 330); ctx.scale(max(p, .01), max(p, .01))
    text(ctx, "LA MÉTÉO", 0, 0, BLACK_F, 150, RED); text(ctx, "DE LA SEMAINE", 0, 136, BLACK_F, 120, RED); ctx.restore()
    text(ctx, mt.get("periode", ""), 62, 540, XB_F, 54, INK, alpha=prog(t, .6, 1.0))
    md = eo(prog(t, .8, 2.0)); mf = prog(t, 1.6, 2.2)
    to_xy = draw_map(ctx, 70, 620, 940, md, mf, 6)
    for i, v in enumerate(mt["villes"]):
        pp = eback(prog(t, 2.0 + i * .2, 2.4 + i * .2))
        if pp <= 0: continue
        x0, y0 = to_xy(*v["lonlat"])
        ctx.save(); ctx.translate(x0, y0); ctx.scale(pp, pp)
        wx_icon(ctx, 0, -46, 1.15, v["ciel"], t)
        lbl = v.get("label", v["nom"])
        font(ctx, "Inter", 28, False, True); lw = tw(ctx, lbl) + 20
        rect(ctx, -lw / 2, 4, lw, 40, WHITE, .85)
        text(ctx, lbl, 0, 34, "Inter", 28, INK, "c", italic=False, bold=True)
        text(ctx, f"{v['tmax']}°", 0, 100, BLACK_F, 64, RED, "c")
        ctx.restore()
    text(ctx, "Source : Météo-France · Présenté par Léa", 60, H - 120, "Inter", 30, GREY, italic=False, bold=True)
    rect(ctx, 0, H - 28, W, 28, RED)
    wipe_in(ctx, t)

def scene_meteo_semaine(ctx, t, dur):
    mt = EP["meteo"]
    rect(ctx, 0, 0, W, H, WHITE)
    header(ctx, t, "MÉTÉO")
    text(ctx, "JOUR PAR JOUR", 60, 300, BLACK_F, 120, RED)
    text(ctx, "Températures max / min en Saône-et-Loire", 62, 370, "Inter", 34, GREY, italic=False, bold=True)
    days = mt["jours"]; n = len(days)
    rh = (H - 560) / n
    for i, d in enumerate(days):
        rp = eo(prog(t, .5 + i * .25, .9 + i * .25))
        if rp <= 0: continue
        y = 430 + i * rh; dx = 200 * (1 - rp)
        rect(ctx, 60 + dx, y, 960, rh - 16, PINK if i % 2 == 0 else LIGHT, rp)
        text(ctx, d["jour"].upper(), 90 + dx, y + rh / 2 + 14, XB_F, 54, INK, alpha=rp)
        ctx.save(); ctx.translate(dx, 0); wx_icon(ctx, 470, y + rh / 2 - 8, 1.25, d["ciel"], t); ctx.restore()
        text(ctx, f"{d['tmax']}°", 820 + dx, y + rh / 2 + 22, BLACK_F, 76, RED, "r", alpha=rp)
        text(ctx, f"{d['tmin']}°", 990 + dx, y + rh / 2 + 18, BLACK_F, 56, GREY, "r", alpha=rp)
    rect(ctx, 0, H - 28, W, 28, RED)
    wipe_in(ctx, t)

def scene_fin(ctx, t, dur):
    rect(ctx, 0, 0, W, H, WHITE)
    rect(ctx, 0, 0, W * eio(prog(t, 0, .5)), 28, RED)
    p = prog(t, .1, .6); s = 1.6 - .6 * eo(p)
    ctx.save(); ctx.translate(W / 2, 520); ctx.scale(s, s)
    text(ctx, "LE 71", 0, 0, BLACK_F, 290, RED, "c", alpha=p)
    font(ctx, XB_F, 66); bw = tw(ctx, "FLASH NEWS") + 48
    if p > .5: skew_band(ctx, -bw / 2, 40, bw, 86, RED); text(ctx, "FLASH NEWS", 0, 108, XB_F, 66, WHITE, "c")
    ctx.restore()
    q = eo(prog(t, .7, 1.2))
    nxt = {"matin": "Rendez-vous ce soir à 20h !", "soir": "Rendez-vous demain matin !", "meteo": "Bonne semaine à tous !", "special": "Rendez-vous au prochain flash !", "alerte": "Restez prudents. Plus d'infos dans nos flashs."}[EP["format"]]
    if EP.get("question"):
        lines = wrap(ctx, EP["question"], XB_F, 70, 900)[:2]
        bh = 100 + 76 * len(lines); top = 690 + 40 * (1 - q)
        rect(ctx, 80, top, 920, bh, PINK, q)
        for i, ln in enumerate(lines):
            text(ctx, ln, W / 2, top + 76 + i * 76, XB_F, 70, INK, "c", alpha=q)
        text(ctx, "Répondez en commentaire", W / 2, top + bh - 26, "Inter", 32, RED, "c", italic=False, bold=True, alpha=q)
    else:
        text(ctx, "Toute l'actu du 71,", W / 2, 790 + 40 * (1 - q), XB_F, 86, INK, "c", alpha=q)
        text(ctx, "près de chez vous.", W / 2, 880 + 40 * (1 - q), XB_F, 86, INK, "c", alpha=q)
    b = eo(prog(t, 1.1, 1.6)); bounce = abs(math.sin(t * math.pi)) * 16
    by = 960 + 60 * (1 - b) - bounce
    rect(ctx, 100, by, 880, 128, RED, b)
    text(ctx, "Abonnez-vous", W / 2 + 30, by + 84, "Inter", 52, WHITE, "c", italic=False, bold=True, alpha=b)
    ix = 300; iy = by + 64
    ctx.new_path(); ctx.set_source_rgba(1, 1, 1, b); ctx.set_line_width(6); ctx.arc(ix, iy - 14, 14, 0, 2 * math.pi); ctx.stroke()
    ctx.new_path(); ctx.arc(ix, iy + 30, 26, math.pi * 1.15, math.pi * 1.85); ctx.stroke()
    c = eo(prog(t, 1.3, 1.8)); cy = 1120 + 60 * (1 - c)
    ctx.new_path(); ctx.set_source_rgba(*RED, c); ctx.set_line_width(7); ctx.rectangle(100, cy, 880, 116); ctx.stroke()
    text(ctx, "Partagez autour de vous", W / 2, cy + 76, "Inter", 46, RED, "c", italic=False, bold=True, alpha=c)
    text(ctx, nxt, W / 2, 1320, "Inter", 38, GREY, "c", italic=False, bold=True, alpha=prog(t, 1.8, 2.3))
    street(ctx, t, H - 520)
    rect(ctx, 0, H - 28, W * eio(prog(t, 0, .5)), 28, RED)

# ---------- voix (Piper, voix française douce) ----------
VOICE = os.environ.get("LE71_VOICE", os.path.join(HERE, "voice", "fr_FR-siwis-medium.onnx"))

import re as _re
def diction(s):
    """Léa ne lit jamais « 20h » : on écrit les heures en toutes lettres pour la synthèse."""
    s = _re.sub(r"\b(\d{1,2})\s?[hH]\s?(\d{2})\b", lambda m: f"{int(m.group(1))} heures {int(m.group(2))}", s)
    s = _re.sub(r"\b(\d{1,2})\s?[hH]\b", lambda m: f"{int(m.group(1))} heure" + ("" if int(m.group(1)) == 1 else "s"), s)
    # sigles épelés lettre par lettre (la synthèse lit « RCEA » comme un mot anglais)
    for sig in ("RCEA", "SNCF", "TGV", "TER", "SDIS", "CHU", "EDF", "RN"):
        s = _re.sub(rf"\b{sig}\b", " ".join(sig), s)
    s = _re.sub(r"\bR\.\s?C\.\s?E\.\s?A\.?", "R C E A", s)
    s = _re.sub(r"\bA\s?(\d{1,2})\b", r"A \1", s)
    return s

def tts(textv, out):
    textv = diction(textv)
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "--length-scale", str(EP.get("voice_speed", 1.05)),
                    "--sentence-silence", "0.12", "-f", out], input=textv.encode(), check=True, capture_output=True)
    w = wave.open(out); d = w.getnframes() / w.getframerate(); w.close(); return d

# ---------- pipeline ----------
def plan():
    sc = [("intro", scene_intro, EP["voix"]["intro"], .35)]
    if EP["format"] == "alerte":
        sc = [("alerte", scene_alerte, EP["voix"]["intro"], .3)]
        n = len(EP["items"])
        for i, it in enumerate(EP["items"]):
            sc.append((f"sujet{i+1}", (lambda it, i: (lambda c, t, d: scene_item(c, t, d, it, i + 1, n)))(it, i), it["voix"], .25))
        sc.append(("fin", scene_fin, EP["voix"]["fin"], .8))
        return sc
    if EP["format"] == "meteo":
        sc.append(("carte", scene_meteo_carte, EP["voix"]["carte"], .3))
        sc.append(("semaine", scene_meteo_semaine, EP["voix"]["semaine"], .3))
    else:
        sc.append(("ouverture", scene_ouverture, EP["voix"]["sommaire"], .3))
        n = len(EP["items"])
        for i, it in enumerate(EP["items"]):
            sc.append((f"sujet{i+1}", (lambda it, i: (lambda c, t, d: scene_item(c, t, d, it, i + 1, n)))(it, i), it["voix"], .25))
    sc.append(("fin", scene_fin, EP["voix"]["fin"], .9))
    return sc

def render_scene(fn, dur, out):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
    n = int(round(dur * FPS)); tmp = out[:-4] + ".tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    for i in range(n):
        ctx.save(); fn(ctx, i / FPS, dur); ctx.restore(); surf.flush(); p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    if p.wait() != 0: raise SystemExit("ffmpeg a échoué sur " + out)
    os.replace(tmp, out)

def main():
    global EP
    import argparse, numpy as np
    from concurrent.futures import ProcessPoolExecutor
    ap = argparse.ArgumentParser(); ap.add_argument("episode"); ap.add_argument("out"); ap.add_argument("--stills")
    a = ap.parse_args()
    EP = json.load(open(a.episode))
    for it in EP.get("items", []): it.setdefault("lonlat", locate(it["commune"]))
    if EP["format"] == "meteo":
        for v in EP["meteo"]["villes"]: v.setdefault("lonlat", locate(v["nom"]))
    json.dump(EP, open(a.episode, "w"), ensure_ascii=False, indent=1)
    work = tempfile.mkdtemp(prefix="le71_")
    sc = plan(); durs = {}; audio = []; sr = None
    for k, fn, v, extra in sc:
        wav = os.path.join(work, k + ".wav"); vd = tts(v, wav)
        durs[k] = round((vd + .15 + extra) * FPS) / FPS
        w = wave.open(wav); sr = w.getframerate(); arr = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16); w.close()
        seg = np.zeros(int(round(durs[k] * sr)), dtype=np.int16); lead = int(.15 * sr); seg[lead:lead + len(arr)] = arr[:len(seg) - lead]; audio.append(seg)
    o = wave.open(os.path.join(work, "voix.wav"), "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(np.concatenate(audio).tobytes()); o.close()
    if a.stills:
        os.makedirs(a.stills, exist_ok=True)
        for k, fn, v, extra in sc:
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
            fn(ctx, min(4.0, durs[k] - .5), durs[k]); surf.write_to_png(os.path.join(a.stills, k + ".png"))
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as ex:
        futs = [ex.submit(_render_worker, a.episode, k, durs[k], os.path.join(work, k + ".mp4")) for k, *_ in sc]
        for f in futs: f.result()
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.join(work, k + '.mp4')}'\n" for k, *_ in sc))
    vid = os.path.join(work, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    tmp = a.out[:-4] + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", os.path.join(work, "voix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-af", "loudnorm=I=-16:TP=-1.5", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, a.out)
    print("OK", a.out, round(sum(durs.values()), 1), "s")

def _render_worker(ep_path, key, dur, out):
    global EP
    EP = json.load(open(ep_path))
    for k, fn, v, extra in plan():
        if k == key: render_scene(fn, dur, out); return

if __name__ == "__main__":
    main()
