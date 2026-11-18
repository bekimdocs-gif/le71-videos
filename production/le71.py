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
# charte « sombre » (nov. 2026) : fond nuit, titres blancs, rouge pour les bandeaux
BG = (0.047, 0.055, 0.078)
BG2 = (0.102, 0.114, 0.153)
MUTE = (0.74, 0.76, 0.82)
DRED = (0.50, 0.03, 0.08)
# zones TikTok à laisser libres de texte : boutons à droite (x > SAFE_R entre y 850 et 1560), légende en bas (y > SAFE_B)
SAFE_R, SAFE_B = 920, 1565

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
def fond(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.086, 0.094, 0.137); g.add_color_stop_rgb(.55, *BG); g.add_color_stop_rgb(1, 0.03, 0.035, 0.05)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    for i in range(3):                                   # bandes diagonales discrètes, façon habillage d'info en continu
        x = ((t * 26 + i * 520) % 1700) - 400
        poly(ctx, [(x + 520, 0), (x + 700, 0), (x + 180, H), (x, H)], RED, .045)

def header(ctx, t, label):
    text(ctx, "LE 71", 60, 128, BLACK_F, 80, RED)
    font(ctx, XB_F, 40)
    bw = tw(ctx, "FLASH NEWS") + 40
    skew_band(ctx, 224, 80, bw, 54, RED)
    text(ctx, "FLASH NEWS", 244, 122, XB_F, 40, WHITE)
    if label:
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.cos(t * 2 * math.pi / 1.2))
        x = text(ctx, label, 1020, 120, "Inter", 30, WHITE, "r", italic=False, bold=True)
        circ(ctx, 1020 - x - 24, 110, 10, RED, a)

# ---------- transitions « breaking news » : volets rouges en biais + logo ----------
_SK = 170
def _volet(ctx, x1, x2, col, a=1.0):
    poly(ctx, [(x1 + _SK, 0), (x2 + _SK, 0), (x2 - _SK, H), (x1 - _SK, H)], col, a)

def _logo_volet(ctx, a):
    if a <= 0: return
    text(ctx, "LE 71", W / 2, 960, BLACK_F, 330, WHITE, "c", alpha=a)
    font(ctx, XB_F, 70); bw = tw(ctx, "FLASH NEWS") + 60
    rect(ctx, (W - bw) / 2, 1010, bw, 96, WHITE, a); text(ctx, "FLASH NEWS", W / 2, 1081, XB_F, 70, RED, "c", alpha=a)

def wipe_in(ctx, t):
    """début de scène : le volet rouge qui couvrait l'écran s'en va vers la droite"""
    p = prog(t, 0, .42)
    if p >= 1: return
    e = eio(p); x = -_SK - 40 + (W + 2 * _SK + 420) * e
    _volet(ctx, x - 330, x - 190, DRED); _volet(ctx, x - 150, x - 110, WHITE); _volet(ctx, x - 60, x - 30, RED)
    _volet(ctx, x, W + 2 * _SK + 500, RED)
    _logo_volet(ctx, clamp(1 - p * 4))

def wipe_out(ctx, t, dur):
    """fin de scène : le volet rouge arrive par la gauche et couvre l'écran"""
    p = prog(t, dur - .24, dur - 1 / FPS)
    if p <= 0: return
    e = eio(p); x = -_SK - 380 + (W + 2 * _SK + 420) * e
    _volet(ctx, x + 190, x + 330, DRED); _volet(ctx, x + 110, x + 150, WHITE); _volet(ctx, x + 30, x + 60, RED)
    _volet(ctx, -2 * _SK - 500, x, RED)
    _logo_volet(ctx, clamp(p * 4 - 3))

def ticker(ctx, t, msg):
    y = H - 84
    rect(ctx, 0, y, W, 84, BG2); rect(ctx, 0, y, W, 4, RED)
    font(ctx, "Inter", 32, False, True)
    ww = tw(ctx, msg) + 80
    off = (t * 110) % ww
    ctx.save(); ctx.rectangle(200, y, W - 200, 84); ctx.clip()
    for k in range(3):
        text(ctx, msg, 220 + k * ww - off, y + 56, "Inter", 32, WHITE, italic=False, bold=True)
    ctx.restore()
    skew_band(ctx, -20, y, 220, 84, RED, 0.1)
    text(ctx, "EN BREF", 30, y + 58, XB_F, 46, WHITE)

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

# ---------- carte du 71 en 3D : contour exact, inclinée, en relief ----------
MAINV = [("Mâcon", 4.828, 46.307), ("Chalon", 4.853, 46.781), ("Autun", 4.299, 46.951), ("Le Creusot", 4.424, 46.801),
         ("Montceau", 4.366, 46.668), ("Paray", 4.120, 46.451), ("Louhans", 5.225, 46.627)]

def map3d_h(w, ky=.6):
    """hauteur approximative occupée à l'écran par la carte 3D de largeur w"""
    return w * M()["h"] * ky * 1.1 + w * .075

def draw_map3d(ctx, cx, cy, w, t, grow=1.0, ky=.6, sway=True, villes=None):
    """(cx, cy) = centre de la carte. grow 0→1 : la carte sort du sol. villes = (lon, lat) du sujet pour afficher les repères."""
    m = M(); hh = m["h"]; g = clamp(grow)
    ws = w * (.84 + .16 * g)
    a = math.radians(-5 + (4 * math.sin(t * .7) if sway else 0)); ca, sa = math.cos(a), math.sin(a)
    D = w * .075 * g
    def f(px, py, lift=0.0):
        u, v = px - .5, py - hh / 2
        u, v = u * ca - v * sa, u * sa + v * ca
        k = 1 + v * .30
        return (cx + u * ws * k, cy + v * ws * ky * k - lift)
    to_xy = lambda lon, lat: f(*proj(lon, lat), D)
    if g <= 0: return to_xy
    pts = m["pts"]
    def path(lift, step=1):
        P = pts[::step]; ctx.new_path(); ctx.move_to(*f(P[0][0], P[0][1], lift))
        for q in P[1:]: ctx.line_to(*f(q[0], q[1], lift))
        ctx.close_path()
    ctx.push_group()
    path(-22, 4); ctx.set_source_rgba(0, 0, 0, .5); ctx.fill()                       # ombre au sol
    n = max(1, int(D / 3))
    for i in range(n + 1):                                                           # tranche (relief)
        k = i / n; path(D * k, 3); ctx.set_source_rgb(.36 + .22 * k, .02 + .02 * k, .06 + .03 * k); ctx.fill()
    path(D)
    lg = cairo.LinearGradient(cx, cy - ws * .3, cx, cy + ws * .3)
    lg.add_color_stop_rgb(0, 1, .975, .975); lg.add_color_stop_rgb(1, *PINK2)
    ctx.set_source(lg); ctx.fill_preserve()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_source_rgb(*RED); ctx.set_line_width(max(4, w * .007)); ctx.stroke()
    if villes is not None and g > .9:
        sx, sy = to_xy(*villes)
        for nom, lon, lat in MAINV:
            x, y = to_xy(lon, lat)
            if math.hypot(x - sx, y - sy) < 90: continue
            circ(ctx, x, y, 6, (.55, .16, .2))
            text(ctx, nom, x + 12, y + 9, "Inter", 24, (.42, .22, .25), italic=False, bold=True)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(clamp(g * 1.8))
    return to_xy

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

def il_course(ctx, t):
    """course à pied en ville : coureurs (bonnets de Père Noël) qui défilent, arche d'arrivée"""
    rect(ctx, 0, 0, PW, PH, WHITE)
    ctx.save(); ctx.translate(0, PH - 520); street(ctx, t, 0); ctx.restore()
    g = PH - 140
    # arche d'arrivée
    line(ctx, 690, g, 690, g - 330, RED, 16); line(ctx, 950, g, 950, g - 330, RED, 16)
    rect(ctx, 670, g - 370, 300, 70, RED); text(ctx, "ARRIVÉE", 820, g - 320, BLACK_F, 52, WHITE, "c")
    # coureurs
    for i, (off, col, sc) in enumerate(((0, INK, 1.25), (260, RED, 1.15), (520, INK, 1.3), (780, RED, 1.2), (1040, INK, 1.1))):
        x = ((t * 190 + off) % 1300) - 150
        walker(ctx, x, g, sc, col, t + i * .13, 2.6, RED if col == INK else INK)
        bob = abs(math.sin((t + i * .13) * 2.6 * 2 * math.pi)) * 3 * sc
        hx, hy = x, g - bob - 104 * sc
        poly(ctx, [(hx - 15 * sc, hy - 6 * sc), (hx + 15 * sc, hy - 6 * sc), (hx - 26 * sc, hy - 40 * sc)], RED)
        rect(ctx, hx - 17 * sc, hy - 9 * sc, 34 * sc, 8 * sc, WHITE); circ(ctx, hx - 27 * sc, hy - 41 * sc, 6 * sc, WHITE)

ILL.update(course=il_course, running=il_course, corrida=il_course)

def il_batiment(ctx, t):
    """chantier : maison en construction, échafaudage, grue, artisan"""
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 26) % 1300) - 200, 90, 1)
    rect(ctx, 0, 600, PW, 100, (.87, .87, .87))
    # maison en construction (murs en parpaings, charpente apparente)
    rect(ctx, 150, 380, 400, 220, (.93, .93, .93))
    for r in range(5):
        y = 380 + r * 44
        line(ctx, 150, y, 550, y, (.84, .84, .84), 3)
        for c in range(6):
            x = 150 + c * 80 + (40 if r % 2 else 0)
            if 150 < x < 550: line(ctx, x, y, x, y + 44, (.84, .84, .84), 3)
    rect(ctx, 300, 470, 90, 130, WHITE); rect(ctx, 430, 440, 80, 70, (.78, .89, .97))
    for a, b in (((130, 380), (350, 250)), ((350, 250), (570, 380)), ((130, 380), (570, 380)),
                 ((350, 250), (350, 380)), ((240, 315), (240, 380)), ((460, 315), (460, 380))):
        line(ctx, a[0], a[1], b[0], b[1], (.72, .52, .3), 12)
    # échafaudage
    for x in (40, 120):
        line(ctx, x, 300, x, 600, GREY, 7)
    for y in (360, 470):
        rect(ctx, 28, y, 104, 12, (.72, .52, .3)); line(ctx, 40, y + 12, 120, y + 110, (.6, .6, .6), 4)
    # grue : la charge monte et descend
    line(ctx, 760, 110, 760, 600, RED, 16); rect(ctx, 720, 580, 80, 20, INK)
    line(ctx, 640, 130, 930, 130, RED, 12); line(ctx, 760, 70, 640, 130, RED, 5); line(ctx, 760, 70, 930, 130, RED, 5)
    rect(ctx, 630, 132, 50, 44, GREY)
    hx = 870 + math.sin(t * .8) * 30; hy = 330 + math.sin(t * 1.1) * 90
    line(ctx, hx, 130, hx, hy, INK, 4); rect(ctx, hx - 44, hy, 88, 50, (.72, .52, .3)); line(ctx, hx - 44, hy + 25, hx + 44, hy + 25, (.6, .42, .22), 4)
    # artisan casqué
    wx = ((t * 70) % 1200) - 100
    walker(ctx, wx, 690, 1.15, INK, t, 1.2, (1, .75, .1))
    bob = abs(math.sin(t * 1.2 * 2 * math.pi)) * 3 * 1.15
    ctx.set_source_rgb(1, .75, .1); ctx.arc(wx, 690 - bob - 108 * 1.15, 16, math.pi, 2 * math.pi); ctx.fill()

def il_football(ctx, t):
    """terrain, but et ballon"""
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 30) % 1300) - 200, 80, 1)
    for i in range(6):
        rect(ctx, 0, 400 + i * 50, PW, 50, (.80, .90, .76) if i % 2 else (.85, .93, .81))
    line(ctx, 0, 402, PW, 402, WHITE, 6)
    ctx.set_source_rgb(*WHITE); ctx.set_line_width(6); ctx.save(); ctx.translate(250, 560); ctx.scale(1, .34); ctx.arc(0, 0, 150, 0, 2 * math.pi); ctx.restore(); ctx.stroke()
    # but et filet
    gx, gy, gw, gh = 610, 250, 290, 260
    ctx.set_source_rgba(.6, .6, .6, .55); ctx.set_line_width(2)
    for i in range(1, 12):
        ctx.move_to(gx + i * gw / 12, gy); ctx.line_to(gx + i * gw / 12, gy + gh)
    for j in range(1, 10):
        ctx.move_to(gx, gy + j * gh / 10); ctx.line_to(gx + gw, gy + j * gh / 10)
    ctx.stroke()
    for a, b in (((gx, gy + gh), (gx, gy)), ((gx, gy), (gx + gw, gy)), ((gx + gw, gy), (gx + gw, gy + gh))):
        line(ctx, a[0], a[1], b[0], b[1], WHITE, 16); line(ctx, a[0], a[1], b[0], b[1], (.8, .8, .8), 3)
    # ballon : tir en cloche vers le but, en boucle
    u = (t % 2.4) / 2.4
    bx = 200 + u * 520; by = 600 - math.sin(u * math.pi) * 240 - u * 190
    circ(ctx, bx, 640 - u * 120, 22 - u * 6, (0, 0, 0), .10)
    circ(ctx, bx, by, 30, WHITE); ctx.set_source_rgb(*INK); ctx.set_line_width(4); ctx.arc(bx, by, 30, 0, 2 * math.pi); ctx.stroke()
    ctx.save(); ctx.translate(bx, by); ctx.rotate(t * 6)
    poly(ctx, [(0, -12), (11, -4), (7, 10), (-7, 10), (-11, -4)], INK); ctx.restore()
    walker(ctx, 130 + math.sin(t * 1.5) * 30, 680, 1.25, INK, t, 1.6, RED)
    walker(ctx, 470 + math.sin(t * 1.2 + 1) * 40, 640, 1.05, INK, t, 1.4, (.2, .35, .7))

def il_justice(ctx, t):
    """palais de justice et balance"""
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 24) % 1300) - 200, 70, 1)
    rect(ctx, 0, 600, PW, 100, (.87, .87, .87))
    rect(ctx, 90, 300, 520, 300, (.96, .96, .96)); poly(ctx, [(70, 300), (350, 190), (630, 300)], (.92, .92, .92))
    rect(ctx, 70, 292, 560, 18, (.86, .86, .86))
    for i in range(5):
        x = 130 + i * 98; rect(ctx, x, 330, 46, 250, WHITE); rect(ctx, x - 8, 322, 62, 12, (.86, .86, .86)); rect(ctx, x - 8, 576, 62, 12, (.86, .86, .86))
    rect(ctx, 250, 236, 200, 40, PINK2); text(ctx, "TRIBUNAL", 350, 268, XB_F, 34, RED, "c")
    rect(ctx, 70, 588, 560, 12, (.8, .8, .8))
    # balance (léger balancement)
    cx, cy = 770, 250; a = math.sin(t * 1.3) * .09
    line(ctx, cx, cy, cx, 560, RED, 14); rect(ctx, cx - 70, 556, 140, 20, RED); circ(ctx, cx, cy, 18, RED)
    dx, dy = math.cos(a) * 118, math.sin(a) * 118
    line(ctx, cx - dx, cy - dy, cx + dx, cy + dy, RED, 12)
    for sgn in (-1, 1):
        px_, py_ = cx + sgn * dx, cy + sgn * dy
        line(ctx, px_, py_, px_ - 48, py_ + 120, INK, 3); line(ctx, px_, py_, px_ + 48, py_ + 120, INK, 3)
        ctx.set_source_rgb(*INK); ctx.arc(px_, py_ + 120, 54, 0, math.pi); ctx.fill()
    walker(ctx, ((t * 60) % 1200) - 100, 690, 1.1, INK, t, 1.1)

def il_sante(ctx, t):
    """hôpital et tracé du pouls"""
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 26) % 1300) - 200, 80, 1)
    rect(ctx, 0, 600, PW, 100, (.87, .87, .87))
    rect(ctx, 140, 250, 460, 350, (.95, .95, .95)); rect(ctx, 600, 360, 220, 240, (.92, .92, .92))
    for r in range(3):
        for c in range(4): rect(ctx, 180 + c * 104, 330 + r * 80, 64, 48, (.78, .89, .97))
    for r in range(2):
        for c in range(2): rect(ctx, 632 + c * 90, 400 + r * 80, 60, 48, (.78, .89, .97))
    rect(ctx, 320, 520, 100, 80, RED); rect(ctx, 290, 506, 160, 14, (.8, .8, .8))
    rect(ctx, 310, 170, 120, 100, (.12, .36, .85)); text(ctx, "H", 370, 254, BLACK_F, 104, WHITE, "c", italic=False)
    # pouls
    ctx.set_source_rgb(*RED); ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    base, n = 262, clamp(((t * .6) % 1.4))
    pts = [(630, base), (700, base), (724, base - 50), (752, base + 40), (780, base - 76), (808, base), (930, base)]
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])); left = tot * n
    ctx.move_to(*pts[0])
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1]); k = clamp(left / d) if d else 0
        ctx.line_to(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k); left -= d
        if left <= 0: break
    ctx.stroke()
    walker(ctx, ((t * 70) % 1200) - 100, 690, 1.1, INK, t, 1.2, (.95, .95, .95))
    walker(ctx, 1100 - ((t * 55 + 300) % 1200), 690, 1.1, INK, t, 1.1, RED)

def il_ecole(ctx, t):
    """école, horloge et élèves"""
    rect(ctx, 0, 0, PW, PH, (.98, .98, .98)); cloud(ctx, ((t * 26) % 1300) - 200, 70, 1)
    rect(ctx, 0, 600, PW, 100, (.87, .87, .87))
    rect(ctx, 160, 320, 560, 280, (.96, .96, .96)); poly(ctx, [(140, 320), (440, 200), (740, 320)], PINK3)
    circ(ctx, 440, 276, 30, WHITE); ctx.set_source_rgb(*INK); ctx.set_line_width(4); ctx.arc(440, 276, 30, 0, 2 * math.pi); ctx.stroke()
    line(ctx, 440, 276, 440 + math.sin(t * .8) * 20, 276 - math.cos(t * .8) * 20, INK, 4); line(ctx, 440, 276, 452, 276, INK, 4)
    rect(ctx, 350, 340, 180, 44, PINK2); text(ctx, "ÉCOLE", 440, 376, XB_F, 38, RED, "c")
    for c in (0, 1, 3, 4): rect(ctx, 200 + c * 104, 420, 70, 80, (.78, .89, .97))
    rect(ctx, 395, 470, 90, 130, RED)
    flag(ctx, 790, 250, t, 70, 44); line(ctx, 790, 340, 790, 600, (.74, .74, .74), 5)
    # arbre
    rect(ctx, 60, 500, 18, 100, (.72, .52, .3)); circ(ctx, 69, 460, 60, (.81, .89, .75))
    for i, col in enumerate(((1, .75, .1), RED, (.2, .35, .7))):
        x = ((t * (55 + i * 12) + i * 300) % 1200) - 100
        walker(ctx, x, 690, .8, INK, t + i * .3, 1.7, col)
        rect(ctx, x - 22, 690 - 86 * .8, 14, 30, col)

ILL.update(batiment=il_batiment, chantier=il_batiment, artisanat=il_batiment,
           football=il_football, foot=il_football,
           justice=il_justice, tribunal=il_justice,
           sante=il_sante, hopital=il_sante,
           ecole=il_ecole, education=il_ecole)

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
    fond(ctx, t)
    rect(ctx, 0, 0, W * eio(prog(t, 0, .3)), 28, RED)
    acc = EP.get("accroche")
    k = eio(prog(t, 1.5, 1.9)) if acc else 0.0      # 0 = générique plein écran, 1 = logo en haut + accroche
    a = 0.3 + 0.7 * (0.5 + 0.5 * math.cos(t * 2 * math.pi / 1.2))
    circ(ctx, 92, 112, 12, RED, a)
    text(ctx, "EN DIRECT DU 71", 116, 124, "Inter", 32, WHITE, italic=False, bold=True)
    text(ctx, EP.get("date_label", "").upper(), 1020, 124, "Inter", 28, WHITE, "r", italic=False, bold=True)
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
        rect(ctx, 110 + bw + 30, 908, 6, 88, WHITE, b)
        text(ctx, "SAÔNE-ET-LOIRE", 110 + bw + 60, 982, BOLD_F, 66, WHITE, alpha=b)
        ctx.restore()
    if acc and k > 0:
        tag = EP.get("accroche_tag", "À LA UNE")
        font(ctx, XB_F, 52); tgw = tw(ctx, tag) + 50
        skew_band(ctx, 70 - 300 * (1 - k), 720, tgw, 76, RED); text(ctx, tag, 95 - 300 * (1 - k), 776, XB_F, 52, WHITE)
        size = 128
        lines = wrap(ctx, acc.upper(), BLACK_F, size, SAFE_R - 70)
        while len(lines) > 4 and size > 80:
            size -= 8; lines = wrap(ctx, acc.upper(), BLACK_F, size, SAFE_R - 70)
        y = 820 + size
        for i, ln in enumerate(lines):
            lp = eo(prog(t, 1.6 + i * .12, 2.0 + i * .12))
            text(ctx, ln, 70 + 60 * (1 - lp), y, BLACK_F, size, WHITE, alpha=lp); y += size * .95
    street(ctx, t, H - 520); rect(ctx, 0, H - 520, W, 520, BG, .55)
    rect(ctx, 0, H - 28, W * eio(prog(t, 0, .3)), 28, RED)
    wipe_out(ctx, t, dur)

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
    wipe_out(ctx, t, dur)

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
    """habillage du format + sommaire + grande carte 3D des lieux"""
    f = dict(FORMATS[EP["format"]])
    if EP.get("titre"): f["title"] = EP["titre"]
    if EP.get("sous_titre"): f["sub"] = EP["sous_titre"]
    fond(ctx, t)
    header(ctx, t, EP.get("date_label", "").upper())
    p = eback(prog(t, .2, .8))
    y = 330
    for ln in f["title"]:
        ctx.save(); ctx.translate(60, y); ctx.scale(max(p, .01), max(p, .01)); text(ctx, ln, 0, 0, BLACK_F, 150, WHITE); ctx.restore(); y += 140
    text(ctx, f["sub"], 62, y - 62, XB_F, 54, MUTE, alpha=prog(t, .6, 1.0))
    y += 4
    font(ctx, XB_F, 34); sw = tw(ctx, "AU SOMMAIRE") + 36
    sp = eo(prog(t, .8, 1.1))
    skew_band(ctx, 66 - 200 * (1 - sp), y - 40, sw, 48, RED); text(ctx, "AU SOMMAIRE", 82 - 200 * (1 - sp), y - 4, XB_F, 34, WHITE); y += 26
    items = EP.get("sommaire_items") or EP["items"]; n = len(items)
    rh = 116 if n <= 3 else 92
    for i, it in enumerate(items):
        rp = eo(prog(t, 1.0 + i * .3, 1.4 + i * .3))
        if rp <= 0: y += rh; continue
        dx = 160 * (1 - rp); bh = rh - 20
        tag = it.get("tag", str(i + 1))
        font(ctx, XB_F, 44 if n <= 3 else 38); tw_ = max(110, tw(ctx, tag) + 40)
        rect(ctx, 60 + dx + tw_, y, 960 - tw_, bh, BG2, rp)
        rect(ctx, 60 + dx, y, tw_, bh, RED, rp); text(ctx, tag, 60 + dx + tw_ / 2, y + bh / 2 + 16, XB_F, 44 if n <= 3 else 38, WHITE, "c", alpha=rp)
        ttl = wrap(ctx, it.get("short", it["title"]), "Inter", 34, 960 - tw_ - 50, italic=False, bold=True)[0]
        text(ctx, ttl, 60 + dx + tw_ + 24, y + bh / 2 + 12, "Inter", 34, WHITE, italic=False, bold=True, alpha=rp)
        y += rh
    # grande carte 3D des lieux
    top = y + 10; avail = SAFE_B - 20 - top
    mw = 840
    if map3d_h(mw) > avail: mw *= avail / map3d_h(mw)
    cx = 490; cy = top + map3d_h(mw) / 2 + mw * .05
    to_xy = draw_map3d(ctx, cx, cy, mw, t, eo(prog(t, .7, 1.6)))
    seen, placed, k = set(), [], 0
    for it in EP["items"]:
        lbl = it.get("label_carte", it["commune"])
        if lbl in seen: continue
        seen.add(lbl)
        pp = prog(t, 1.6 + k * .2, 2.0 + k * .2)
        x0, y0 = to_xy(*it["lonlat"])
        font(ctx, XB_F, 32); lw = tw(ctx, lbl) + 20; lh = 44
        cands = [(x0 + 24, y0 - 66), (x0 - 24 - lw, y0 - 66), (x0 + 24, y0 + 4), (x0 - 24 - lw, y0 + 4), (x0 - lw / 2, y0 - 122), (x0 - lw / 2, y0 + 30)]
        lx, ly = cands[0]
        for qx, qy in cands:
            if qx < 10 or qx + lw > SAFE_R + 20: continue
            if all(qx + lw < px or qx > px + pw or qy + lh < py or qy > py + ph for px, py, pw, ph in placed):
                lx, ly = qx, qy; break
        placed.append((lx, ly, lw, lh))
        if pp > 0:
            pin(ctx, x0, y0 - 120 * (1 - eback(pp)), .9, RED)
            lb = eo(prog(t, 1.8 + k * .2, 2.1 + k * .2))
            rect(ctx, lx, ly, lw, lh, BG, lb); rect(ctx, lx, ly + lh - 5, lw, 5, RED, lb); text(ctx, lbl, lx + 10, ly + 32, XB_F, 32, WHITE, alpha=lb)
        k += 1
    rect(ctx, 0, H - 28, W, 28, RED)
    wipe_in(ctx, t); wipe_out(ctx, t, dur)

_PHOTOS = {}
def draw_photo(ctx, path, w, h):
    if path not in _PHOTOS:
        _PHOTOS[path] = cairo.ImageSurface.create_from_png(path)
    img = _PHOTOS[path]; iw, ih = img.get_width(), img.get_height()
    k = max(w / iw, h / ih)
    ctx.save(); ctx.translate((w - iw * k) / 2, (h - ih * k) / 2); ctx.scale(k, k)
    ctx.set_source_surface(img, 0, 0); ctx.paint(); ctx.restore()

def scene_item(ctx, t, dur, it, idx, total):
    """1) grande carte 3D qui situe le lieu  2) volet rouge  3) illustration ou photo. Titre et texte visibles dès le début."""
    fond(ctx, t)
    rect(ctx, 0, 0, W * clamp(t / dur), 12, RED)
    header(ctx, t, f"{FORMATS[EP['format']]['label']} · {idx}/{total}")
    px, py = 60, 160
    tm = min(2.9, dur * .3)                      # durée de la carte avant le visuel
    e = eio(prog(t, tm, tm + .45)); edge = px - 140 + (PW + 280) * e
    if e < 1:                                    # --- carte 3D (à droite du volet)
        ctx.save(); ctx.rectangle(max(0, edge), py - 60, W, PH + 120); ctx.clip()
        to_xy = draw_map3d(ctx, W / 2 - 10, py + PH / 2 + 40, 830, t, eo(prog(t, .1, .9)), villes=tuple(it["lonlat"]))
        tx, ty = to_xy(*it["lonlat"])
        pp = prog(t, .8, 1.3)
        if pp > 0:
            rr = (t * .9) % 1
            ctx.save(); ctx.translate(tx, ty); ctx.scale(1, .6); ctx.new_path()
            ctx.set_source_rgba(*RED, 1 - rr); ctx.set_line_width(6); ctx.arc(0, 0, 16 + rr * 70, 0, 2 * math.pi); ctx.stroke(); ctx.restore()
            pin(ctx, tx, ty - 160 * (1 - eback(pp)), 1.5, RED)
            lb = eo(prog(t, 1.1, 1.5))
            lbl = it.get("label_carte", it["commune"]).upper()
            font(ctx, XB_F, 60); lw = tw(ctx, lbl) + 44
            lx = clamp(tx - lw / 2, 70, W - 70 - lw); ly = ty - 200
            if ly < py - 40: ly = ty + 36
            rect(ctx, lx, ly + 20 * (1 - lb), lw, 84, BG, lb); rect(ctx, lx, ly + 76 + 20 * (1 - lb), lw, 8, RED, lb)
            text(ctx, lbl, lx + 22, ly + 60 + 20 * (1 - lb), XB_F, 60, WHITE, alpha=lb)
        ctx.restore()
    if e > 0:                                    # --- visuel (à gauche du volet)
        vw = clamp(edge - px, 0, PW)
        ctx.save(); ctx.rectangle(px - 6, py - 6, vw + 6, PH + 12); ctx.clip()
        ctx.save(); ctx.rectangle(px, py, PW, PH); ctx.clip(); ctx.translate(px, py)
        z = 1 + .04 * (t / dur)
        ctx.translate(PW / 2, PH / 2); ctx.scale(z, z); ctx.translate(-PW / 2, -PH / 2)
        global CUR_ITEM; CUR_ITEM = it
        if it.get("photo"):                        # photo de terrain (plaques floutées en amont) à la place de l'illustration
            draw_photo(ctx, it["photo"], PW, PH)
        else:
            ILL.get(it.get("theme", "generic"), il_generic)(ctx, t)
        ctx.restore()
        ctx.new_path(); ctx.set_source_rgb(*RED); ctx.set_line_width(8); ctx.rectangle(px, py, PW, PH); ctx.stroke()
        ctx.restore()
        if e < 1:
            o = 60
            poly(ctx, [(edge + o, py - 60), (edge + 70 + o, py - 60), (edge + 70 - o, py + PH + 60), (edge - o, py + PH + 60)], RED)
            poly(ctx, [(edge + 86 + o, py - 60), (edge + 104 + o, py - 60), (edge + 104 - o, py + PH + 60), (edge + 86 - o, py + PH + 60)], WHITE)
    nb = eback(prog(t, tm + .4, tm + .9))
    if nb > 0:
        ctx.save(); ctx.translate(px + 90, py + PH - 10); ctx.scale(nb, nb)
        rect(ctx, -90, -90, 180, 180, RED); text(ctx, str(idx), 0, 62, BLACK_F, 190, WHITE, "c"); ctx.restore()
    db = eo(prog(t, .5, 1.0))
    band = it.get("band", it.get("tag", "")).upper()
    if band:
        bsz = 56; font(ctx, XB_F, bsz)
        while tw(ctx, band) + 60 > SAFE_R - 290 and bsz > 34: bsz -= 4; font(ctx, XB_F, bsz)
        bw = tw(ctx, band) + 60
        ctx.save(); ctx.rectangle(0, 880, W, 110); ctx.clip()
        dx = -(bw + 300) * (1 - db)
        skew_band(ctx, 280 + dx, 890, bw, 84, WHITE); text(ctx, band, 310 + dx, 890 + 42 + bsz * .36, XB_F, bsz, INK)
        ctx.restore()
    # bloc texte : tout doit tenir au-dessus de SAFE_B et à gauche de SAFE_R (boutons et légende TikTok)
    TW = SAFE_R - 60
    size, nd = 104, 3
    while True:
        lines = wrap(ctx, it["title"].upper(), BLACK_F, size, TW)
        dl = wrap(ctx, it.get("desc", ""), "Inter Medium", 40, TW, italic=False)[:nd]
        pls = wrap(ctx, it.get("place", it["commune"]), XB_F, 54, TW - 70)[:2]
        bot = 1010 + size * .78 + (len(lines) - 1) * size * .96 + (62 + (len(dl) - 1) * 54 if dl else 0) + 80 + (len(pls) - 1) * 60 + (44 if it.get("source") else 0)
        if (bot <= SAFE_B and len(lines) <= 3) or size <= 64:
            if bot > SAFE_B and nd > 1: nd -= 1; continue
            break
        size -= 8
    tp = eo(prog(t, .3, .8))
    y = 1010 + size * .78
    for ln in lines:
        text(ctx, ln, 60, y + 40 * (1 - tp), BLACK_F, size, WHITE, alpha=tp); y += size * .96
    y -= size * .96
    dp = eo(prog(t, .7, 1.2))
    if dl:
        y += 62
        for ln in dl:
            text(ctx, ln, 62, y + 30 * (1 - dp), "Inter Medium", 40, MUTE, italic=False, alpha=dp); y += 54
        y -= 54
    pl = eo(prog(t, 1.0, 1.5))
    y += 80
    pin(ctx, 84, y + 6, .8, RED)
    for ln in pls:
        text(ctx, ln, 124 - 30 * (1 - pl), y, XB_F, 54, WHITE, alpha=pl); y += 60
    if it.get("source"):
        text(ctx, "Source : " + it["source"], 126, y - 16, "Inter", 28, MUTE, italic=False, bold=True, alpha=pl)
    ticker(ctx, t, EP.get("ticker", "Abonnez-vous à LE 71 Flash News  •  L'actu de la Saône-et-Loire  •"))
    wipe_in(ctx, t); wipe_out(ctx, t, dur)

def scene_meteo_carte(ctx, t, dur):
    mt = EP["meteo"]
    fond(ctx, t)
    header(ctx, t, "MÉTÉO")
    p = eback(prog(t, .2, .8))
    ctx.save(); ctx.translate(60, 330); ctx.scale(max(p, .01), max(p, .01))
    text(ctx, mt.get("titre1", "LA MÉTÉO"), 0, 0, BLACK_F, 150, WHITE); text(ctx, mt.get("titre2", "DE LA SEMAINE"), 0, 136, BLACK_F, 120, WHITE); ctx.restore()
    font(ctx, XB_F, 50); pw_ = tw(ctx, mt.get("periode", "")) + 44; pa = eo(prog(t, .6, 1.0))
    if mt.get("periode"):
        skew_band(ctx, 70 - 300 * (1 - pa), 500, pw_, 70, RED); text(ctx, mt["periode"], 90 - 300 * (1 - pa), 552, XB_F, 50, WHITE)
    to_xy = draw_map3d(ctx, 490, 1100, 880, t, eo(prog(t, .7, 1.7)), ky=.9, sway=False)
    # Placement des étiquettes : position réelle de la ville, puis écartement automatique
    # des étiquettes qui se chevauchent (Digoin/Paray, Autun/Montceau…), avec un trait de rappel.
    anc = [to_xy(*v["lonlat"]) for v in mt["villes"]]
    pos = [[x + v.get("decal", [0, 0])[0], y + v.get("decal", [0, 0])[1]] for (x, y), v in zip(anc, mt["villes"])]
    BW, BH = 140, 220
    for _ in range(80):
        moved = False
        for a in range(len(pos)):
            for b in range(a + 1, len(pos)):
                dx = pos[b][0] - pos[a][0]; dy = pos[b][1] - pos[a][1]
                ox = BW - abs(dx); oy = BH - abs(dy)
                if ox > 0 and oy > 0:
                    moved = True
                    if ox * 1.6 < oy or abs(dx) > abs(dy):
                        s_ = (1 if dx >= 0 else -1) * (ox / 2 + 2); pos[a][0] -= s_; pos[b][0] += s_
                    else:
                        s_ = (1 if dy >= 0 else -1) * (oy / 2 + 2); pos[a][1] -= s_; pos[b][1] += s_
        for q in pos: q[0] = min(max(q[0], 90), W - 90)
        if not moved: break
    for i, v in enumerate(mt["villes"]):
        pp = eback(prog(t, 1.8 + i * .2, 2.2 + i * .2))
        if pp <= 0: continue
        (ax, ay), (x0, y0) = anc[i], pos[i]
        if abs(x0 - ax) + abs(y0 - ay) > 12:
            ctx.save(); ctx.set_source_rgba(1, 1, 1, .85 * min(pp, 1)); ctx.set_line_width(4)
            ctx.move_to(ax, ay); ctx.line_to(x0, y0 + 4); ctx.stroke()
            ctx.set_source_rgba(*RED, min(pp, 1)); ctx.arc(ax, ay, 10, 0, 6.2832); ctx.fill(); ctx.restore()
        ctx.save(); ctx.translate(x0, y0); ctx.scale(pp, pp)
        wx_icon(ctx, 0, -46, 1.15, v["ciel"], t)
        lbl = v.get("label", v["nom"])
        font(ctx, "Inter", 28, False, True); lw = tw(ctx, lbl) + 20
        rect(ctx, -lw / 2, 4, lw, 40, BG, .9)
        text(ctx, lbl, 0, 34, "Inter", 28, WHITE, "c", italic=False, bold=True)
        rect(ctx, -46, 50, 92, 62, RED); text(ctx, f"{v['tmax']}°", 4, 100, BLACK_F, 56, WHITE, "c")
        ctx.restore()
    text(ctx, "Source : " + mt.get("source", "Météo-France") + " · Présenté par Léa", 60, 1560, "Inter", 28, MUTE, italic=False, bold=True)
    rect(ctx, 0, H - 28, W, 28, RED)
    wipe_in(ctx, t); wipe_out(ctx, t, dur)

def scene_meteo_semaine(ctx, t, dur):
    mt = EP["meteo"]
    fond(ctx, t)
    header(ctx, t, "MÉTÉO")
    text(ctx, "JOUR PAR JOUR", 60, 300, BLACK_F, 120, WHITE)
    text(ctx, "Températures max / min en Saône-et-Loire", 62, 370, "Inter", 32, MUTE, italic=False, bold=True)
    days = mt["jours"]; n = len(days)
    rh = (SAFE_B - 430) / n; RW = SAFE_R - 60
    for i, d in enumerate(days):
        rp = eo(prog(t, .5 + i * .25, .9 + i * .25))
        if rp <= 0: continue
        y = 430 + i * rh; dx = 200 * (1 - rp)
        rect(ctx, 60 + dx, y, RW, rh - 14, BG2 if i % 2 == 0 else (.14, .155, .2), rp); rect(ctx, 60 + dx, y, 10, rh - 14, RED, rp)
        text(ctx, d["jour"].upper(), 96 + dx, y + rh / 2 + 12, XB_F, 54, WHITE, alpha=rp)
        ctx.save(); ctx.translate(dx, 0); wx_icon(ctx, 470, y + rh / 2 - 12, 1.2, d["ciel"], t); ctx.restore()
        text(ctx, f"{d['tmax']}°", 740 + dx, y + rh / 2 + 20, BLACK_F, 76, WHITE, "r", alpha=rp)
        text(ctx, f"{d['tmin']}°", 890 + dx, y + rh / 2 + 16, BLACK_F, 56, MUTE, "r", alpha=rp)
    rect(ctx, 0, H - 28, W, 28, RED)
    wipe_in(ctx, t); wipe_out(ctx, t, dur)

def scene_fin(ctx, t, dur):
    fond(ctx, t)
    rect(ctx, 0, 0, W * eio(prog(t, 0, .5)), 28, RED)
    CX = (60 + SAFE_R) / 2 + 25
    p = prog(t, .1, .6); s = 1.6 - .6 * eo(p)
    ctx.save(); ctx.translate(W / 2, 520); ctx.scale(s, s)
    text(ctx, "LE 71", 0, 0, BLACK_F, 290, RED, "c", alpha=p)
    font(ctx, XB_F, 66); bw = tw(ctx, "FLASH NEWS") + 48
    if p > .5: skew_band(ctx, -bw / 2, 40, bw, 86, RED); text(ctx, "FLASH NEWS", 0, 108, XB_F, 66, WHITE, "c")
    ctx.restore()
    q = eo(prog(t, .7, 1.2))
    nxt = {"matin": "Rendez-vous ce soir à 20h !", "soir": "Rendez-vous demain matin !", "meteo": "Bonne semaine à tous !", "special": "Rendez-vous au prochain flash !", "alerte": "Restez prudents. Plus d'infos dans nos flashs."}[EP["format"]]
    if EP.get("question"):
        lines = wrap(ctx, EP["question"], XB_F, 70, SAFE_R - 150)[:2]
        bh = 100 + 76 * len(lines); top = 690 + 40 * (1 - q)
        rect(ctx, 80, top, SAFE_R - 60, bh, BG2, q); rect(ctx, 80, top, 12, bh, RED, q)
        for i, ln in enumerate(lines):
            text(ctx, ln, CX, top + 76 + i * 76, XB_F, 70, WHITE, "c", alpha=q)
        text(ctx, "Répondez en commentaire", CX, top + bh - 26, "Inter", 32, MUTE, "c", italic=False, bold=True, alpha=q)
    else:
        text(ctx, "Toute l'actu du 71,", CX, 790 + 40 * (1 - q), XB_F, 86, WHITE, "c", alpha=q)
        text(ctx, "près de chez vous.", CX, 880 + 40 * (1 - q), XB_F, 86, WHITE, "c", alpha=q)
    b = eo(prog(t, 1.1, 1.6)); bounce = abs(math.sin(t * math.pi)) * 16
    by = 980 + 60 * (1 - b) - bounce
    rect(ctx, 80, by, SAFE_R - 60, 128, RED, b)
    text(ctx, "Abonnez-vous", CX + 30, by + 84, "Inter", 52, WHITE, "c", italic=False, bold=True, alpha=b)
    ix = CX - 210; iy = by + 64
    ctx.new_path(); ctx.set_source_rgba(1, 1, 1, b); ctx.set_line_width(6); ctx.arc(ix, iy - 14, 14, 0, 2 * math.pi); ctx.stroke()
    ctx.new_path(); ctx.arc(ix, iy + 30, 26, math.pi * 1.15, math.pi * 1.85); ctx.stroke()
    c = eo(prog(t, 1.3, 1.8)); cy = 1140 + 60 * (1 - c)
    ctx.new_path(); ctx.set_source_rgba(1, 1, 1, c); ctx.set_line_width(6); ctx.rectangle(80, cy, SAFE_R - 60, 116); ctx.stroke()
    text(ctx, "Partagez autour de vous", CX, cy + 76, "Inter", 46, WHITE, "c", italic=False, bold=True, alpha=c)
    text(ctx, nxt, CX, 1340, "Inter", 38, MUTE, "c", italic=False, bold=True, alpha=prog(t, 1.8, 2.3))
    street(ctx, t, H - 520); rect(ctx, 0, H - 520, W, 520, BG, .55)
    rect(ctx, 0, H - 28, W * eio(prog(t, 0, .5)), 28, RED)
    wipe_in(ctx, t)

SAFE_TOP, SAFE_BOT, VUES_Y, VUES_W = 240, 1680, 1500, 440

def _fit(ctx, s, fam, size, maxw, maxlines, mini):
    lines = wrap(ctx, s, fam, size, maxw)
    while (len(lines) > maxlines or any(tw(ctx, l) > maxw for l in lines)) and size > mini:
        size -= 6; lines = wrap(ctx, s, fam, size, maxw)
    return size, lines[:maxlines]

# Couverture : instant de l'animation où le sujet est bien au centre, et hauteur de ciel masquée, par thème
COVER_T = dict(secours=2.3, route=1.85, economie=3.0, sante=3.6)
COVER_CADRAGE = dict(generic=215)

def _wrap_titre(ctx, s, size, maxw):
    """Comme wrap(), mais ne laisse jamais « : », « ? » ou « ! » seul en début de ligne."""
    font(ctx, BLACK_F, size)
    mots = []
    for wd in s.split():
        if wd in (":", "?", "!", ";", "»") and mots: mots[-1] += " " + wd
        elif mots and mots[-1] == "«": mots[-1] += " " + wd
        else: mots.append(wd)
    lines, cur = [], ""
    for wd in mots:
        tst = (cur + " " + wd).strip()
        if tw(ctx, tst) <= maxw: cur = tst
        else:
            if cur: lines.append(cur)
            cur = wd
    if cur: lines.append(cur)
    return lines

def _fit_titre(ctx, s, maxw, haut):
    """Titre de couverture le plus gros possible : 2 lignes de préférence, 3 si le titre est long."""
    for maxlines, sizes in ((2, range(216, 148, -6)), (3, range(180, 92, -6))):
        for size in sizes:
            ls = _wrap_titre(ctx, s, size, maxw)
            if len(ls) <= maxlines and all(tw(ctx, l) <= maxw for l in ls) and (len(ls) - 1) * size * .94 + size * .70 <= haut:
                return size, ls
    return 96, _wrap_titre(ctx, s, 96, maxw)[:3]

def scene_couverture(ctx, t=0, dur=0):
    f = FORMATS[EP["format"]]; cv = EP.get("couverture") or {}
    if not isinstance(cv, dict): cv = {}
    it = (EP.get("items") or [{}])[0]
    alerte = EP["format"] == "alerte"
    titre = cv.get("titre") or (it.get("title") if alerte else EP.get("accroche")) or it.get("short") or it.get("title") \
        or EP.get("meteo", {}).get("periode", "") or f["sub"]
    lieu = cv.get("lieu", it.get("commune", "Saône-et-Loire"))
    rect(ctx, 0, 0, W, H, BG)
    # 1. bandeau du rendez-vous, plus discret que le titre (visible dans la grille à partir de y=240)
    BAN = 440
    rect(ctx, 0, 0, W, BAN, RED)
    size, ls = _fit(ctx, " ".join(EP.get("titre") or f["title"]), BLACK_F, 156, 980, 1, 96)
    text(ctx, ls[0], W / 2, 378, BLACK_F, size, WHITE, "c")
    text(ctx, "FLASH NEWS · SAÔNE-ET-LOIRE", W / 2, 424, XB_F, 40, WHITE, "c")
    # 2. visuel : photo de terrain ou illustration du thème (cadrée sur le sujet, pas sur le ciel)
    vy, vh = BAN, 520
    ctx.save(); ctx.rectangle(0, vy, W, vh); ctx.clip(); ctx.translate(0, vy)
    photo = cv.get("photo") or it.get("photo")
    if photo and os.path.exists(photo):
        draw_photo(ctx, photo, W, vh)
    else:
        # illustration dessinée à part, puis posée entière en largeur ; les bords (ciel, sol) sont prolongés
        global CUR_ITEM; CUR_ITEM = it
        ill = cairo.ImageSurface(cairo.FORMAT_RGB24, PW, PH)
        th = it.get("theme", "generic") if it.get("theme", "generic") in ILL else "generic"
        ILL[th](cairo.Context(ill), cv.get("instant", COVER_T.get(th, 4.0)))
        haut = cv.get("cadrage", COVER_CADRAGE.get(th, 150))   # on masque le haut (ciel) de l'illustration
        k = vh / (PH - haut)
        ctx.translate((W - PW * k) / 2, -haut * k); ctx.scale(k, k)
        pat = cairo.SurfacePattern(ill); pat.set_extend(cairo.EXTEND_PAD)
        ctx.set_source(pat); ctx.paint()
    ctx.restore()
    rect(ctx, 0, vy + vh, W, 16, RED)
    # 3. titre = l'info principale : le plus gros élément de la couverture
    top, bot = vy + vh + 16, VUES_Y
    size, ls = _fit_titre(ctx, titre.upper(), 1000, bot - top - 70)
    lh, cap = size * .94, size * .70
    y = top + (bot - top - ((len(ls) - 1) * lh + cap)) / 2 + cap
    for ln in ls:
        text(ctx, ln, W / 2, y, BLACK_F, size, WHITE, "c"); y += lh
    # 4. bande sombre : à gauche, RIEN (le compteur de vues TikTok s'y pose) ; à droite, le lieu et la date
    rect(ctx, 0, VUES_Y, W, H - VUES_Y, INK)
    rect(ctx, 0, VUES_Y, W, 10, RED)
    if lieu:
        size, ls = _fit(ctx, lieu.upper(), XB_F, 84, W - VUES_W - 50, 1, 44)
        text(ctx, ls[0], W - 50, 1606, XB_F, size, WHITE, "r")
    text(ctx, EP.get("date_label", "").upper(), W - 50, 1656, "Inter", 30, (.8, .8, .8), "r", italic=False, bold=True)
    # 5. hors grille (plein écran seulement) : la signature du compte
    text(ctx, "@flashnews71000", W / 2, 1800, "Inter", 34, (.55, .55, .55), "c", italic=False, bold=True)

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

# ---------- voix de Léa : OmniVoice (clone de la voix créée dans VoiceStudio), repli Piper ----------
# La voix de référence est dans voice/lea_ref.wav (+ voice/lea_ref.txt = texte exact lu).
# LE71_TTS=piper force l'ancienne voix. Si OmniVoice n'est pas installé ou plante, Piper prend le relais.
LEA_REF = os.path.join(HERE, "voice", "lea_ref.wav")
LEA_SR = 24000
_LEA = {"model": None, "prompt": None, "off": os.environ.get("LE71_TTS", "lea").lower() == "piper"}

def _lea_load():
    if _LEA["model"] is None:
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1"); os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
        import torch
        from omnivoice import OmniVoice
        torch.set_num_threads(max(1, os.cpu_count() or 1))
        m = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cpu", dtype=torch.float32)
        ref_text = open(LEA_REF[:-4] + ".txt", encoding="utf-8").read().strip()
        _LEA["prompt"] = m.create_voice_clone_prompt(ref_audio=LEA_REF, ref_text=ref_text)
        _LEA["model"] = m
    return _LEA["model"]

def _tts_lea(textv, out):
    import numpy as np
    m = _lea_load()
    a = m.generate(text=textv, voice_clone_prompt=_LEA["prompt"],
                   num_step=int(EP.get("lea_steps", 16)), speed=float(EP.get("lea_speed", 0.92)))[0]
    a = np.asarray(a, dtype=np.float32)
    nz = np.nonzero(np.abs(a) > 0.01)[0]                   # retire les silences de début/fin
    if len(nz): a = a[max(0, nz[0] - 240): nz[-1] + 2400]
    a = a / max(1e-6, float(np.abs(a).max())) * 0.75          # niveau constant d'une scène à l'autre
    w = wave.open(out, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(LEA_SR)
    w.writeframes((a * 32767).astype(np.int16).tobytes()); w.close()

def _tts_piper(textv, out):
    raw = out[:-4] + ".piper.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "--length-scale", str(EP.get("voice_speed", 1.05)),
                    "--sentence-silence", "0.12", "-f", raw], input=textv.encode(), check=True, capture_output=True)
    # même fréquence que la voix de Léa, pour pouvoir mélanger les scènes sans souci
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", str(LEA_SR), "-ac", "1", out], check=True)

def tts(textv, out):
    textv = diction(textv)
    if not _LEA["off"] and os.path.exists(LEA_REF):
        try:
            _tts_lea(textv, out)
        except Exception as e:
            _LEA["off"] = True
            print("ATTENTION : voix de Léa (OmniVoice) indisponible, repli sur Piper :", repr(e)[:300], file=sys.stderr)
    if _LEA["off"] or not os.path.exists(out):
        _tts_piper(textv, out)
    w = wave.open(out); d = w.getnframes() / w.getframerate(); w.close(); return d

# ---------- pipeline ----------
COVER_DUR = .3   # durée de la couverture en tête de vidéo (TikTok prend la 1re image comme couverture)

def plan():
    sc = _plan()
    if EP.get("couverture", True) is not False:
        sc.insert(0, ("couverture", scene_couverture, None, COVER_DUR))
    return sc

def _plan():
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
        if EP.get("meteo") and EP["voix"].get("meteo"):
            sc.append(("meteo_jour", scene_meteo_carte, EP["voix"]["meteo"], .3))
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
    ap = argparse.ArgumentParser(); ap.add_argument("episode"); ap.add_argument("out"); ap.add_argument("--stills"); ap.add_argument("--cover", help="exporte la couverture seule (PNG)")
    a = ap.parse_args()
    EP = json.load(open(a.episode))
    for it in EP.get("items", []): it.setdefault("lonlat", locate(it["commune"]))
    if EP.get("meteo"):
        for v in EP["meteo"]["villes"]: v.setdefault("lonlat", locate(v["nom"]))
    json.dump(EP, open(a.episode, "w"), ensure_ascii=False, indent=1)
    if a.cover:
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); scene_couverture(cairo.Context(surf)); surf.write_to_png(a.cover)
        if a.out == "-": print("OK", a.cover); return
    work = tempfile.mkdtemp(prefix="le71_")
    sc = plan(); durs = {}; audio = []; sr = None
    for k, fn, v, extra in sc:
        if v is None:                               # scène muette (couverture)
            durs[k] = round(extra * FPS) / FPS; audio.append(None); continue
        wav = os.path.join(work, k + ".wav"); vd = tts(v, wav)
        durs[k] = round((vd + .15 + extra) * FPS) / FPS
        w = wave.open(wav); sr = w.getframerate(); arr = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16); w.close()
        seg = np.zeros(int(round(durs[k] * sr)), dtype=np.int16); lead = int(.15 * sr); seg[lead:lead + len(arr)] = arr[:len(seg) - lead]; audio.append(seg)
    audio = [np.zeros(int(round(durs[k] * sr)), dtype=np.int16) if seg is None else seg for (k, *_), seg in zip(sc, audio)]
    mix = np.concatenate(audio).astype(np.float32)
    if EP.get("son_transitions", True):
        rng = np.random.default_rng(71); L = int(.5 * sr); x = np.arange(L) / sr
        noise = np.convolve(rng.standard_normal(L + 40), np.ones(40) / 40, "valid")[:L]
        env = np.where(x < .25, (x / .25) ** 2, np.exp(-(x - .25) * 14))
        souffle = noise / np.abs(noise).max() * env * 2600 + np.sin(2 * np.pi * 62 * x) * np.exp(-np.clip(x - .25, 0, None) * 16) * (x >= .25) * 3000
        tc = 0.0
        for k, *_ in sc[:-1]:
            tc += durs[k]
            if k == "couverture": continue
            i0 = int((tc - .25) * sr)
            if i0 > 0 and i0 + L < len(mix): mix[i0:i0 + L] += souffle
    audio = [np.clip(mix, -32000, 32000).astype(np.int16)]
    o = wave.open(os.path.join(work, "voix.wav"), "wb"); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(np.concatenate(audio).tobytes()); o.close()
    if a.stills:
        os.makedirs(a.stills, exist_ok=True)
        for k, fn, v, extra in sc:
            surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(surf)
            fn(ctx, max(0, min(4.0, durs[k] - .5)), durs[k]); surf.write_to_png(os.path.join(a.stills, k + ".png"))
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
