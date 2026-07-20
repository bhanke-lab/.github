"""Pixel-art ride, v18.
"""

import math
from xml.dom import minidom

TICK = 0.8
REPAIR = 6.0

    
LEG1 = [(-70, 271, 1.5), (30, 264, 1.45), (130, 257, 1.4), (230, 250, 1.34),
        (330, 243, 1.28), (430, 236, 1.22), (520, 228, 1.16), (600, 219, 1.1),
        (660, 210, 1.05), (695, 202, 1.0)]
    
LEG2 = [(655, 195, 0.95), (580, 188, 0.9), (500, 181, 0.85), (420, 175, 0.8),
        (345, 166, 0.76), (300, 153, 0.73), (272, 142, 0.7), (175, 140, 0.66)]


def l1_raw(x):
        
    return 122 - 0.024 * x + 10 * math.sin(x / 95.0) + 6 * math.sin(x / 41.0 + 2.0)


    
LEG3_X = [290, 360, 430, 500, 570, 640, 710, 780, 850, 920, 1045]
LEG3 = [(x, round(l1_raw(x) + 8), 0.62 - 0.34 * i / (len(LEG3_X) - 1.0))
        for i, x in enumerate(LEG3_X)]
WPS = ([(x, y, s, -1) for x, y, s in LEG1] +
       [(x, y, s, 1) for x, y, s in LEG2] +
       [(x, y, s, -1) for x, y, s in LEG3])
N = len(WPS)
    
STOPS = [12, 4, 27]

LAP = N * TICK + REPAIR
T = 3 * LAP

TIMES = []
for lap, stop in enumerate(STOPS):
    t = lap * LAP
    for i in range(N):
        TIMES.append(t)
        t += TICK
        if i == stop:
            t += REPAIR
BREAK_FLAT = TIMES[STOPS[0]]
BREAK_WELD = TIMES[N + STOPS[1]]
BREAK_FLAT2 = TIMES[2 * N + STOPS[2]]


def f(x):
    s = '%.6f' % x
    s = s.rstrip('0').rstrip('.')
    return s if s else '0'


KEYTIMES = ';'.join(f(tt / T) for tt in TIMES)
DUR = f(T) + 's'


def R(x, y, w, h, c):
    return ('<rect x="' + f(x) + '" y="' + f(y) + '" width="' + f(w) +
            '" height="' + f(h) + '" fill="' + c + '"/>')


def multi_window(pairs, start='0'):
    kt = '0'
    vals = start
    a, b = ('1', '0') if start == '0' else ('0', '1')
    for on, off in pairs:
        kt += ';' + f(on / T) + ';' + f(off / T)
        vals += ';' + a + ';' + b
    return ('<animate attributeName="opacity" calcMode="discrete" values="' + vals +
            '" keyTimes="' + kt + '" dur="' + DUR + '" repeatCount="indefinite"/>')


def q4(v):
    return round(v / 4.0) * 4


def mountains_backdrop(p):
    out = ''
    peaks_far = [(80, 60), (260, 40), (420, 70), (590, 34), (760, 56), (930, 28), (1100, 48)]
    peaks_near = [(10, 92), (180, 76), (350, 96), (530, 70), (700, 88), (880, 62), (1060, 72)]
    for peaks, col, slope in ((peaks_far, p['haze_far'], 0.30), (peaks_near, p['haze_near'], 0.34)):
        for cx in range(0, 1160, 8):
            yy = min(py + slope * abs(cx - px) for px, py in peaks)
            yy = q4(min(yy, 140))
            out += R(cx, yy, 8, 148 - yy, col)
    return out


LAYERS = [
    (122, -0.024, ((10, 95, 0.0), (6, 41, 2.0)), 'l1', 'l1_lit'),
    (164, 0.0, ((12, 80, 1.0), (7, 37, 0.0)), 'l2', 'l2_lit'),
    (214, 0.0, ((14, 70, 3.0), (8, 33, 1.0)), 'l3', 'l3_lit'),
    (262, 0.0, ((10, 60, 2.0), (6, 28, 0.0)), 'l4', 'l4_lit'),
]


def ridge_y(base, tilt, amps, x):
    v = base + tilt * x
    for amp, per, ph in amps:
        v += amp * math.sin(x / per + ph)
    return q4(v)


def layer(base, tilt, amps, col, lit):
    out = ''
    for cx in range(0, 1160, 8):
        yy = ridge_y(base, tilt, amps, cx)
        out += R(cx, yy, 8, 284 - yy, col)
        out += R(cx, yy, 8, 4, lit)
    return out


def bush(p):
    return (R(-10, -8, 20, 8, p['bush']) + R(-6, -12, 12, 4, p['bush']) +
            R(-2, -14, 6, 4, p['bush_lit']))


def cypress(p):
    return (R(-4, -30, 8, 26, p['bush']) + R(-6, -20, 12, 8, p['bush']) +
            R(-2, -36, 4, 8, p['bush']) + R(-4, -32, 4, 4, p['bush_lit']))


def dome(p, col, lit):
    out = []
    H = 40.0
    y = -40
    while y < 0:
        tt = (y + H) / H
        hw = 56.0 * math.sqrt(max(tt * (2 - tt), 0.02))
        hw = max(4.0, round(hw / 4.0) * 4)
        out.append(R(-hw, y, hw * 2, 4, lit if y < -32 else col))
        y += 4
    for bx, by in ((-24, -12), (10, -18), (-4, -6)):
        out.append(R(bx, by, 12, 6, p['bush']))
    return ''.join(out)


def tri_runs(cx, apex_y, base_hw, y):
    if y < apex_y:
        return None
    frac = (y - apex_y + 4.0) / (0.0 - apex_y)
    hw = base_hw * min(frac, 1.0)
    hw = max(4.0, round(hw / 4.0) * 4)
    return (cx - hw, cx + hw)


def crag(p):
        
    tris = [(-16, -44, 24), (12, -56, 28)]
    jit = [0, 2, 0, 2, 0, -2, 2, 0, 0, 2, 0, 2, -2, 0]
    off = [0, 2, 0, -2, 0, 2, 0, 0, 2, 0, 0, 2, 0, 0]
    out = []
    y = -56
    row = 0
    while y < 0:
        runs = []
        for cx, ay, hw in tris:
            r = tri_runs(cx, ay, hw, y)
            if r:
                a, b = r
                j = jit[row % len(jit)]
                o = off[row % len(off)]
                a = a - j + o
                b = b + j + o
                if b - a < 8:
                    b = a + 8
                runs.append((a, b))
        runs.sort()
        merged = []
        for a, b in runs:
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        for a, b in merged:
            w = b - a
            if w <= 0:
                continue
            lit_w = max(4.0, round(w * 0.35 / 4.0) * 4)
            mid_w = max(4.0, round(w * 0.25 / 4.0) * 4)
            sh_w = w - lit_w - mid_w
            if sh_w < 0:
                sh_w = 0
                mid_w = w - lit_w
            x = a
            for sw, sc in ((lit_w, p['rock_lit']), (mid_w, p['rock_mid']), (sh_w, p['rock_sh'])):
                if sw > 0:
                    out.append(R(x, y, sw, 4, sc))
                    x += sw
        for cx, ay, hw in tris:
            if y >= ay and y - ay <= 10:
                r = tri_runs(cx, ay, hw, y)
                if r:
                    a, b = r
                    out.append(R(a, y, (b - a) / 2.0, 4, p['snow']))
        y += 4
        row += 1
        
    out.append(R(-50, -8, 92, 8, p['l2']))
    for bx, by in ((-44, -10), (30, -12), (-8, -6)):
        out.append(R(bx, by, 14, 6, p['bush']))
    return ''.join(out)


def place(x, y, s, body):
    return ('<g transform="translate(' + f(x) + ',' + f(y) + ') scale(' + f(s) +
            ')">' + body + '</g>')


    
ROAD_PTS = [(-90, 272)] + [(x, y) for x, y, s, fc in WPS] + [(1090, round(l1_raw(1090) + 8))]


def smooth_path(pts):
    d = 'M' + f(pts[0][0]) + ',' + f(pts[0][1])
    d += ' L' + f((pts[0][0] + pts[1][0]) / 2.0) + ',' + f((pts[0][1] + pts[1][1]) / 2.0)
    for i in range(1, len(pts) - 1):
        mx = (pts[i][0] + pts[i + 1][0]) / 2.0
        my = (pts[i][1] + pts[i + 1][1]) / 2.0
        d += ' Q' + f(pts[i][0]) + ',' + f(pts[i][1]) + ' ' + f(mx) + ',' + f(my)
    d += ' L' + f(pts[-1][0]) + ',' + f(pts[-1][1])
    return d


ROAD_D = smooth_path(ROAD_PTS)

    
    
W_ANCH = [(117, 10.0), (165, 15.0), (195, 19.0), (225, 24.0), (266, 30.0)]
DW_ANCH = [(117, 2.0), (165, 3.0), (195, 3.0), (225, 4.0), (266, 5.0)]
DA_ANCH = [(117, 6.0), (165, 9.0), (195, 11.0), (225, 13.0), (266, 16.0)]
DG_ANCH = [(117, 5.0), (165, 7.0), (195, 8.0), (225, 10.0), (266, 12.0)]


def anch(y, table):
    if y <= table[0][0]:
        return table[0][1]
    if y >= table[-1][0]:
        return table[-1][1]
    for (y0, v0), (y1, v1) in zip(table, table[1:]):
        if y <= y1:
            return v0 + (v1 - v0) * (y - y0) / (y1 - y0)
    return table[-1][1]


def road_samples():
    pts = ROAD_PTS
    sam = []
    mx0 = (pts[0][0] + pts[1][0]) / 2.0
    my0 = (pts[0][1] + pts[1][1]) / 2.0
    for k in range(6):
        t = k / 6.0
        sam.append((pts[0][0] + (mx0 - pts[0][0]) * t,
                    pts[0][1] + (my0 - pts[0][1]) * t))
    px, py = mx0, my0
    for i in range(1, len(pts) - 1):
        mx = (pts[i][0] + pts[i + 1][0]) / 2.0
        my = (pts[i][1] + pts[i + 1][1]) / 2.0
        for k in range(1, 9):
            t = k / 8.0
            a = (1 - t) * (1 - t)
            b = 2 * (1 - t) * t
            c = t * t
            sam.append((a * px + b * pts[i][0] + c * mx,
                        a * py + b * pts[i][1] + c * my))
        px, py = mx, my
    for k in range(1, 7):
        t = k / 6.0
        sam.append((px + (pts[-1][0] - px) * t, py + (pts[-1][1] - py) * t))
    return sam


SAM = road_samples()
NRM = []
for i in range(len(SAM)):
    x0, y0 = SAM[max(i - 1, 0)]
    x1, y1 = SAM[min(i + 1, len(SAM) - 1)]
    dx, dy = x1 - x0, y1 - y0
    ln = (dx * dx + dy * dy) ** 0.5 or 1.0
    NRM.append((-dy / ln, dx / ln))


def ribbon(halves, col):
    left = []
    right = []
    for (x, y), (nx, ny), h in zip(SAM, NRM, halves):
        left.append(f(x + nx * h) + ',' + f(y + ny * h))
        right.append(f(x - nx * h) + ',' + f(y - ny * h))
    return ('<polygon points="' + ' '.join(left + right[::-1]) +
            '" fill="' + col + '"/>')


def road(p):
    halves = [anch(y, W_ANCH) / 2.0 for x, y in SAM]
    s = ribbon([h + 2.0 for h in halves], p['edge'])
    s += ribbon(halves, p['road'])
    cum = [0.0]
    for i in range(1, len(SAM)):
        dx = SAM[i][0] - SAM[i - 1][0]
        dy = SAM[i][1] - SAM[i - 1][1]
        cum.append(cum[-1] + (dx * dx + dy * dy) ** 0.5)
    total = cum[-1]

    def at(sd):
        j = 1
        while j < len(cum) - 1 and cum[j] < sd:
            j += 1
        seg = cum[j] - cum[j - 1] or 1.0
        t = (sd - cum[j - 1]) / seg
        x = SAM[j - 1][0] + (SAM[j][0] - SAM[j - 1][0]) * t
        y = SAM[j - 1][1] + (SAM[j][1] - SAM[j - 1][1]) * t
        nx = NRM[j - 1][0] + (NRM[j][0] - NRM[j - 1][0]) * t
        ny = NRM[j - 1][1] + (NRM[j][1] - NRM[j - 1][1]) * t
        return x, y, nx, ny

    sd = 4.0
    while sd < total - 6.0:
        x0, y0, _, _ = at(sd)
        da = anch(y0, DA_ANCH)
        dg = anch(y0, DG_ANCH)
        dwh = anch(y0, DW_ANCH) / 2.0
        s1 = min(sd + da, total - 2.0)
        x1, y1, nx, ny = at((sd + s1) / 2.0)
        hx = (at(s1)[0] - x0) / 2.0
        hy = (at(s1)[1] - y0) / 2.0
        quad = [(x1 - hx + nx * dwh, y1 - hy + ny * dwh),
                (x1 + hx + nx * dwh, y1 + hy + ny * dwh),
                (x1 + hx - nx * dwh, y1 + hy - ny * dwh),
                (x1 - hx - nx * dwh, y1 - hy - ny * dwh)]
        s += ('<polygon points="' + ' '.join(f(a) + ',' + f(b) for a, b in quad) +
              '" fill="' + p['dash'] + '"/>')
        sd = s1 + dg
    return s


def slope_angles():
    angs = []
    for i in range(N):
        x0, y0 = WPS[max(0, i - 1)][0], WPS[max(0, i - 1)][1]
        x1, y1 = WPS[min(N - 1, i + 1)][0], WPS[min(N - 1, i + 1)][1]
        dx, dy = x1 - x0, y1 - y0
        if dx == 0:
            ang = 0.0
        else:
            ang = math.degrees(math.atan2(dy, dx))
            if ang > 90:
                ang -= 180
            if ang < -90:
                ang += 180
        angs.append(max(-10, min(10, round(ang))))
    return angs


def disc(cx, cy, r, c):
    out = []
    y = -r
    while y < r:
        yc = abs(y + 2)
        if yc >= r:
            hw = 4
        else:
            hw = math.sqrt(r * r - yc * yc)
            hw = max(4.0, round(hw / 4.0) * 4)
        out.append(R(cx - hw, cy + y, hw * 2, 4, c))
        y += 4
    return ''.join(out)


def bike(p):
    flat_pair = [(BREAK_FLAT, BREAK_FLAT + REPAIR), (BREAK_FLAT2, BREAK_FLAT2 + REPAIR)]
    both = [(BREAK_FLAT, BREAK_FLAT + REPAIR), (BREAK_WELD, BREAK_WELD + REPAIR),
            (BREAK_FLAT2, BREAK_FLAT2 + REPAIR)]
    angs = slope_angles()

    tvals = []
    svals = []
    rvals = []
    for (x, y, s, fc), ang in zip(WPS * 3, angs * 3):
        oy = y - 15.0 * 1.2 * s
        tvals.append(f(x) + ',' + f(oy))
        svals.append(f(fc * 1.2 * s) + ',' + f(1.2 * s))
        rvals.append(f(ang) + ',0,' + f(15.0 * 1.2 * s))
    bx, by, bs, bf = WPS[4]
    g = '<g transform="translate(' + f(bx) + ',' + f(by - 15.0 * 1.2 * bs) + ')">'
    g += ('<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
          'values="' + ';'.join(tvals) + '" keyTimes="' + KEYTIMES + '" dur="' + DUR +
          '" repeatCount="indefinite"/>')
        
    g += '<g transform="rotate(' + rvals[4] + ')">'
    g += ('<animateTransform attributeName="transform" type="rotate" calcMode="discrete" '
          'values="' + ';'.join(rvals) + '" keyTimes="' + KEYTIMES + '" dur="' + DUR +
          '" repeatCount="indefinite"/>')
    g += '<g transform="scale(' + f(bf * 1.2 * bs) + ',' + f(1.2 * bs) + ')">'
    g += ('<animateTransform attributeName="transform" type="scale" calcMode="discrete" '
          'values="' + ';'.join(svals) + '" keyTimes="' + KEYTIMES + '" dur="' + DUR +
          '" repeatCount="indefinite"/>')
    kt = '0'
    vals = '0,0,12'
    for b in (BREAK_FLAT, BREAK_WELD, BREAK_FLAT2):
        kt += ';' + f(b / T) + ';' + f((b + REPAIR) / T)
        vals += ';-8,0,12;0,0,12'
    g += '<g>'
    g += ('<animateTransform attributeName="transform" type="rotate" calcMode="discrete" '
          'values="' + vals + '" keyTimes="' + kt + '" dur="' + DUR +
          '" repeatCount="indefinite"/>')
    g += disc(0, 0, 15, p['tire'])
    g += disc(0, 0, 8, p['road'])
    g += R(-2, -2, 4, 4, p['metal'])
    g += disc(-32, -6, 12, p['tire'])
    g += disc(-32, -6, 6, p['road'])
    g += R(-34, -8, 4, 4, p['metal'])
    g += R(-14, 0, 14, 4, p['frame'])
    g += R(-10, -8, 4, 8, p['frame'])
    g += R(-8, -16, 4, 8, p['frame'])
    g += R(-6, -24, 4, 8, p['frame'])
    g += R(-26, -24, 22, 4, p['frame'])
    g += R(-28, -16, 4, 8, p['frame'])
    g += R(-24, -10, 4, 6, p['frame'])
    g += R(-18, -4, 4, 6, p['frame'])
    g += R(-30, -26, 4, 10, p['frame'])
    g += R(-33, -16, 4, 10, p['frame'])
    g += R(-12, -30, 14, 4, p['dark'])
    g += R(-38, -32, 12, 4, p['dark'])
    g += R(-38, -28, 4, 8, p['dark'])
    g += R(-16, 2, 10, 4, p['metal'])
    g += '<g opacity="0">' + R(-9, 12, 18, 3, p['tire']) + multi_window(flat_pair) + '</g>'
    crack = (R(-19, -27, 3, 3, p['crack']) + R(-16, -25, 3, 3, p['crack']) +
             R(-13, -23, 3, 3, p['crack']))
    g += ('<g opacity="0">' + crack +
          multi_window([(BREAK_WELD, BREAK_WELD + 5.6)]) + '</g>')
    g += '</g>'
    d = '<g opacity="1">' + multi_window(both, start='1')
    d += ('<g>' + R(15, 13, 4, 4, p['dust']) + R(22, 8, 4, 4, p['dust']) +
          R(28, 15, 4, 4, p['dust']) +
          '<animate attributeName="opacity" calcMode="discrete" values="1;0" ' +
          'keyTimes="0;0.5" dur="0.4s" repeatCount="indefinite"/></g></g>')
    g += d

    def rw(bases, on, off):
        return multi_window([(b + on, b + off) for b in bases])

    g += ('<g transform="translate(20,-58)" opacity="0">' +
          R(0, 0, 20, 24, p['bubble']) + R(8, 4, 4, 10, p['dark']) +
          R(8, 17, 4, 4, p['dark']) +
          rw([BREAK_FLAT, BREAK_WELD, BREAK_FLAT2], 0.0, 1.0) + '</g>')
    lev = '<g transform="translate(23,0)" opacity="0">' + rw([BREAK_FLAT, BREAK_FLAT2], 1.0, 2.4)
    lev += '<g>'
    lev += ('<animateTransform attributeName="transform" type="rotate" calcMode="discrete" '
            'values="-18;14" keyTimes="0;0.5" dur="0.6s" repeatCount="indefinite"/>')
    lev += R(-2, -18, 4, 18, p['lever']) + R(-4, -22, 8, 4, p['lever'])
    lev += '</g></g>'
    g += lev
    g += ('<g transform="translate(33,-20)" opacity="0">' + rw([BREAK_FLAT, BREAK_FLAT2], 2.4, 3.8) +
          R(-8, -12, 16, 4, p['tube']) + R(-8, 4, 16, 4, p['tube']) +
          R(-12, -8, 4, 12, p['tube']) + R(8, -8, 4, 12, p['tube']) + '</g>')
    pmp = '<g transform="translate(35,-13)" opacity="0">' + rw([BREAK_FLAT, BREAK_FLAT2], 3.8, 5.8)
    pmp += R(-6, 22, 16, 4, p['pump']) + R(0, 0, 4, 22, p['pump'])
    pmp += ('<rect x="-6" y="-6" width="16" height="4" fill="' + p['dark'] + '">' +
            '<animate attributeName="y" calcMode="discrete" values="-6;8" keyTimes="0;0.5" ' +
            'dur="0.5s" repeatCount="indefinite"/></rect>')
    pmp += '</g>'
    g += pmp
    wld = '<g transform="translate(-16,-26)" opacity="0">' + rw([BREAK_WELD], 1.0, 5.4)
    wld += R(-10, -16, 4, 12, p['metal']) + R(-13, -19, 10, 4, p['dark'])
    wld += ('<rect x="-7" y="-5" width="6" height="6" fill="' + p['glow'] + '">' +
            '<animate attributeName="opacity" calcMode="discrete" values="1;0.3" ' +
            'keyTimes="0;0.5" dur="0.24s" repeatCount="indefinite"/></rect>')
    for sx, sy, sc, du in ((-2, -10, 'spark_hi', 0.16), (4, -4, 'spark', 0.22), (-8, 4, 'spark', 0.18)):
        wld += ('<rect x="' + f(sx) + '" y="' + f(sy) + '" width="3" height="3" fill="' +
                p[sc] + '"><animate attributeName="opacity" calcMode="discrete" ' +
                'values="0;1" keyTimes="0;0.5" dur="' + f(du) +
                's" repeatCount="indefinite"/></rect>')
    wld += '</g>'
    g += wld
    fx = '<g opacity="0">' + multi_window([(BREAK_FLAT + 5.6, BREAK_FLAT + 6.6),
                                           (BREAK_WELD + 5.6, BREAK_WELD + 6.6),
                                           (BREAK_FLAT2 + 5.6, BREAK_FLAT2 + 6.6)])
    for dx, dy in ((-18, -30), (8, -35), (-3, -16)):
        fx += R(dx, dy, 4, 4, p['ok'])
    fx += '</g>'
    g += fx
    g += '</g></g></g>'
    return g


def fir(col):
        
    return (R(-2, -14, 4, 6, col) + R(-4, -9, 8, 6, col) + R(-6, -4, 12, 4, col))


def tree(p, sway_dur=None, leaves=()):
    s = '<g>'
    if sway_dur:
        s += ('<animateTransform attributeName="transform" type="rotate" '
              'values="-1.6;1.6;-1.6" keyTimes="0;0.5;1" dur="' + sway_dur +
              '" repeatCount="indefinite"/>')
    s += R(-7, -44, 14, 44, p['trunk'])
    s += R(-46, -76, 92, 26, p['canopy'])
    s += R(-38, -94, 76, 22, p['canopy'])
    s += R(-26, -108, 52, 16, p['canopy'])
    s += R(-18, -104, 32, 6, p['canopy_lit'])
    s += R(-34, -88, 24, 6, p['canopy_lit'])
    s += R(10, -72, 24, 6, p['canopy_lit'])
    s += '</g>'
        
    for lx, ly, dur, beg in leaves:
        drop = -ly - 6
        s += ('<g transform="translate(' + f(lx) + ',' + f(ly) + ')"><g>'
              '<animateTransform attributeName="transform" type="translate" '
              'values="0,0;-10,' + f(drop * 0.5) + ';-16,' + f(drop) + ';-16,' + f(drop) +
              '" keyTimes="0;0.08;0.16;1" dur="' + dur + '" begin="' + beg +
              '" repeatCount="indefinite"/>'
              '<rect x="0" y="0" width="4" height="4" fill="' + p['canopy_lit'] +
              '" opacity="0"><animate attributeName="opacity" '
              'values="0;1;1;0;0" keyTimes="0;0.015;0.13;0.16;1" dur="' + dur + '" begin="' + beg +
              '" repeatCount="indefinite"/></rect></g></g>')
    return s


def build(p):
    s = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 280" width="1160" height="280" '
    s += 'shape-rendering="crispEdges" role="img" aria-label="Pixel bike rides a winding asphalt road through terraced hills, around a craggy mountain, fixing a flat, welding a cracked frame, then fixing another flat across three laps.">'
    s += '<title>roll, break, fix, roll again</title>'
    s += R(0, 0, 1160, 44, p['sky_hi'])
    s += R(0, 44, 1160, 32, p['sky_lo'])
    s += R(0, 76, 1160, 28, p['sky_haze'])
    s += '<g>'
    s += ('<animateTransform attributeName="transform" type="translate" '
          'values="0,0;-1160,0" keyTimes="0;1" dur="90s" repeatCount="indefinite"/>')
    for ox in (0, 1160):
        for cx, cy in ((150, 22), (520, 10), (900, 32)):
            s += R(cx + ox, cy, 48, 8, p['cloud'])
            s += R(cx + ox + 10, cy - 6, 28, 6, p['cloud'])
            s += R(cx + ox + 6, cy + 8, 32, 4, p['cloud_dk'])
    s += '</g>'
    s += mountains_backdrop(p)
    for basev, tiltv, ampsv, cv, lv in LAYERS[:1]:
        s += layer(basev, tiltv, ampsv, p[cv], p[lv])
    for bx, by, bs in ((520, 128, 0.6), (840, 112, 0.5)):
        s += place(bx, by, bs, bush(p))
    basev, tiltv, ampsv, cv, lv = LAYERS[1]
    s += layer(basev, tiltv, ampsv, p[cv], p[lv])
    for bx, by, bs in ((640, 186, 0.9), (100, 182, 0.9)):
        s += place(bx, by, bs, bush(p))
    s += place(760, 180, 0.9, cypress(p))
    s += place(784, 182, 0.8, cypress(p))
    basev, tiltv, ampsv, cv, lv = LAYERS[2]
    s += layer(basev, tiltv, ampsv, p[cv], p[lv])
    for bx, by, bs in ((900, 226, 1.2), (60, 236, 1.0), (1060, 230, 1.1)):
        s += place(bx, by, bs, bush(p))
    s += place(960, 228, 1.0, cypress(p))
    basev, tiltv, ampsv, cv, lv = LAYERS[3]
    s += layer(basev, tiltv, ampsv, p[cv], p[lv])
    for bx, by, bs in ((560, 276, 1.4), (900, 278, 1.4), (60, 208, 1.1)):
        s += place(bx, by, bs, bush(p))
        
    s += place(300, 172, 1.0, dome(p, p['l2'], p['l2_lit']))
    s += road(p)
    s += bike(p)
        
    s += place(140, 176, 2.7, crag(p))
    s += place(1060, 114, 1.2, dome(p, p['l1'], p['l1_lit']))
    s += '</svg>'
    return s


COLOR = dict(
    sky_hi='#a9d6ea', sky_lo='#bfe2ef', sky_haze='#d3ecf2',
    cloud='#f6fbfd', cloud_dk='#dceef4',
    haze_far='#8fb4a0', haze_near='#7aa287',
    l1='#9dbd80', l1_lit='#b2cd94',
    l2='#8bb06d', l2_lit='#a1c184',
    l3='#79a25e', l3_lit='#8fb576',
    l4='#5f8a4c', l4_lit='#749c60',
    bush='#39592f', bush_lit='#54754a',
    rock_lit='#a8adbf', rock_mid='#7d84a0', rock_sh='#4e5570', snow='#f4f7fb',
    road='#55565e', edge='#d8d8de', dash='#f2f2ec',
    dust='#bdbdb9',
    frame='#d8433f', tire='#17171c', metal='#c0c6cf', dark='#26262c',
    crack='#101010', glow='#ff9c3f', spark='#ffe25a', spark_hi='#fff6c8',
    bubble='#fffef2', lever='#3f7fd4', tube='#2b2b31', pump='#d8433f', ok='#2f9e57',
    trunk='#6b4a32', canopy='#47703c', canopy_lit='#61894f', fir_far='#6d9479')

MONO = dict(
    sky_hi='#f2f2f2', sky_lo='#e9e9e9', sky_haze='#dedede',
    cloud='#ffffff', cloud_dk='#f0f0f0',
    haze_far='#c2c2c2', haze_near='#aeaeae',
    l1='#9a9a9a', l1_lit='#a8a8a8',
    l2='#888888', l2_lit='#969696',
    l3='#747474', l3_lit='#828282',
    l4='#5e5e5e', l4_lit='#6c6c6c',
    bush='#2e2e2e', bush_lit='#484848',
    rock_lit='#b6b6b6', rock_mid='#8e8e8e', rock_sh='#606060', snow='#f8f8f8',
    road='#303034', edge='#d4d4d4', dash='#ffffff',
    dust='#cccccc',
    frame='#ececec', tire='#0e0e0e', metal='#bcbcbc', dark='#1c1c1c',
    crack='#000000', glow='#e0e0e0', spark='#ffffff', spark_hi='#ffffff',
    bubble='#ffffff', lever='#c8c8c8', tube='#222222', pump='#ececec', ok='#f4f4f4',
    trunk='#242424', canopy='#3c3c3c', canopy_lit='#585858', fir_far='#989898')

for name, pal in (('ride_color.svg', COLOR), ('ride_mono.svg', MONO)):
    out = build(pal)
    with open(name, 'w') as fh:
        fh.write(out)
    minidom.parseString(out)
    print(name, 'ok', len(out), 'bytes')
print('lap', LAP, 'loop', T, 'flat at', BREAK_FLAT, 'weld at', BREAK_WELD,
      'flat2 at', BREAK_FLAT2)
