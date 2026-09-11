#!/usr/bin/env python3
"""Render the schematic / diagram figures for the ECRL-2LAL slide deck.

Each figure is emitted as standalone SVG, then rasterised with headless
Chrome at 2x so it can be dropped straight into the .pptx.
"""
import os, subprocess, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
TMP = sys.argv[2] if len(sys.argv) > 2 else "/tmp"

INK   = "#1F2937"
WIRE  = "#263043"
MUT   = "#6B7280"
ECRL  = "#A4237A"
LAL   = "#12866B"
BLUE  = "#0969DA"
WARN  = "#C0242C"
GOLD  = "#B8860B"
FONT  = "Helvetica, Arial, sans-serif"
MONO  = "'DejaVu Sans Mono', monospace"

def T(x, y, s, size=17, anchor="middle", fill=INK, weight="normal",
      style="normal", font=None):
    return (f'<text x="{x}" y="{y}" font-family="{font or FONT}" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}" '
            f'font-style="{style}">{s}</text>')

def L(x1, y1, x2, y2, w=2.5, c=WIRE, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" '
            f'stroke-width="{w}" stroke-linecap="round"{d}/>')

def DOT(x, y, r=5, c=WIRE):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'

def CIRC(x, y, r, c=WIRE, w=2.5, fill="#ffffff"):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{c}" stroke-width="{w}"/>'

def BOX(x, y, w, h, fill="#ffffff", stroke=WIRE, sw=2.5, rx=6):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

def ARROW(x1, y1, x2, y2, c=WIRE, w=2.5):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" '
            f'stroke-width="{w}" marker-end="url(#ah)"/>')

DEFS = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#263043"/></marker>'
        '<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#12866B"/></marker>'
        '<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#C0242C"/></marker></defs>')

def svg(w, h, body, bg="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">{DEFS}<rect width="{w}" height="{h}" fill="{bg}"/>'
            + "".join(body) + '</svg>')

def render(name, w, h, body, scale=2):
    html = f'<html><body style="margin:0;padding:0">{svg(w,h,body)}</body></html>'
    hp = os.path.join(TMP, name + ".html")
    open(hp, "w").write(html)
    png = os.path.join(OUT, name + ".png")
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={w},{h}", f"--force-device-scale-factor={scale}",
                    "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", png)

# ---------------------------------------------------------------- ground symbol
def GND(x, y, s=1.0):
    o = []
    o.append(L(x, y, x, y + 12 * s))
    for i, wdt in enumerate((26, 17, 9)):
        yy = y + (12 + i * 8) * s
        o.append(L(x - wdt * s, yy, x + wdt * s, yy, w=2.5))
    return o

# ================================================================ 1. ECRL cell
def mosfet(X, yc, gate_right, pmos, gate_len=112, gy=0):
    """Vertical-channel MOSFET.  X = the terminal column x.
    gate_right=True puts the gate lead on the +x side; gy shifts the
    gate lead off the device centre so cross-couple wires can be routed."""
    s = -1 if gate_right else 1
    ch  = X - 34 * s
    gp  = X - 50 * s
    bub = X - 58 * s
    end = X - gate_len * s
    gyy = yc + gy
    o = []
    o.append(L(ch, yc - 38, ch, yc + 38, w=3))
    o.append(L(gp, yc - 42, gp, yc + 42, w=3))
    if pmos:
        o.append(CIRC(bub, gyy, 7.5))
        o.append(L(bub - 7.5 * s, gyy, end, gyy))
    else:
        o.append(L(gp, gyy, end, gyy))
    if gy:
        o.append(L(gp, gyy, gp, yc, w=3))
    o.append(L(ch, yc - 26, X, yc - 26))
    o.append(L(ch, yc + 26, X, yc + 26))
    o.append(L(ch, yc, X, yc))
    o.append(L(X, yc, X, yc - 26) if pmos else L(X, yc, X, yc + 26))
    return o, end

def ecrl_cell():
    W, H = 940, 660
    XL, XR = 310, 610
    yPHI, yP, yM, yGND = 78, 185, 455, 570
    o = []
    o.append(L(40, yPHI, 880, yPHI, w=3, c=ECRL))
    o.append(T(460, 56, "&#934;   power clock   (replaces the DC VDD rail)",
               18, "middle", ECRL, "bold"))
    o.append(L(40, yGND, 880, yGND, w=3))
    o += GND(460, yGND)
    p1, g1 = mosfet(XL, yP, True,  True,  210, -20)
    p2, g2 = mosfet(XR, yP, False, True,  180, +20)
    n1, h1 = mosfet(XL, yM, False, False, 112)
    n2, h2 = mosfet(XR, yM, True,  False, 112)
    o += p1 + p2 + n1 + n2
    o.append(T(318, yP - 60, "MP1", 16, "start", MUT, "bold"))
    o.append(T(602, yP - 60, "MP2", 16, "end",   MUT, "bold"))
    o.append(T(302, yM - 60, "MN1", 16, "end",   MUT, "bold"))
    o.append(T(618, yM - 60, "MN2", 16, "start", MUT, "bold"))
    # rails
    o.append(L(XL, yP - 26, XL, yPHI));  o.append(L(XR, yP - 26, XR, yPHI))
    o.append(L(XL, yM + 26, XL, yGND));  o.append(L(XR, yM + 26, XR, yGND))
    o.append(L(XL, yP + 26, XL, yM - 26)); o.append(L(XR, yP + 26, XR, yM - 26))
    # cross-couple: MP1 gate -> OUT ,  MP2 gate -> OUTB.  They cross once, at (520,205).
    o.append(L(g1, yP - 20, 520, yP - 20)); o.append(L(520, yP - 20, 520, 300))
    o.append(L(520, 300, XR, 300)); o.append(DOT(XR, 300))
    o.append(L(g2, yP + 20, 430, yP + 20)); o.append(L(430, yP + 20, 430, 255))
    o.append(L(430, 255, XL, 255)); o.append(DOT(XL, 255))
    o.append(T(460, 350, "cross-coupled PMOS pair", 15, "middle", ECRL, "bold"))
    o.append(T(296, 348, "OUTB", 19, "end", INK, "bold"))
    o.append(T(624, 348, "OUT", 19, "start", INK, "bold"))
    o.append(T(h1 - 10, yM + 6, "INB", 19, "end", GOLD, "bold"))
    o.append(T(h2 + 10, yM + 6, "IN", 19, "start", GOLD, "bold"))
    for X, cx in ((XL, 80), (XR, 840)):
        o.append(DOT(X, 372))
        o.append(L(X, 372, cx, 372)); o.append(L(cx, 372, cx, 424))
        o.append(L(cx - 30, 424, cx + 30, 424, w=3))
        o.append(L(cx - 30, 442, cx + 30, 442, w=3))
        o.append(L(cx, 442, cx, yGND)); o.append(DOT(cx, yGND))
    for X in (XL, XR):
        o.append(DOT(X, yPHI)); o.append(DOT(X, yGND))
    o.append(T(460, 620,
               "all four devices:  sky130 tt,  W = 1.0 &#181;m,  L = 0.15 &#181;m",
               16, "middle", MUT))
    o.append(T(460, 644,
               "load capacitance  C<tspan baseline-shift='sub' font-size='12'>L</tspan>"
               " = 25 fF  on OUT and on OUTB", 16, "middle", MUT))
    render("fig_ecrl_cell", W, H, o)

# ============================================================== 2. 2LAL cell
def lal_cell():
    W, H = 1020, 500
    o = []
    lanes = [
        (78,  "&#966;<tspan baseline-shift='sub' font-size='13'>t</tspan>",
         "outT", "(inT, inC)", LAL),
        (168, "&#966;<tspan baseline-shift='sub' font-size='13'>t+2</tspan>",
         "outC", "(inT, inC)", LAL),
        (300, "&#966;<tspan baseline-shift='sub' font-size='13'>t-1</tspan>",
         "inT", "(outT, outC)", ECRL),
        (390, "&#966;<tspan baseline-shift='sub' font-size='13'>t+1</tspan>",
         "inC", "(outT, outC)", ECRL),
    ]
    for y, rail, dest, ctrl, col in lanes:
        o.append(T(300, y + 6, rail, 21, "end", col, "bold"))
        o.append(L(318, y, 430, y, c=col))
        o.append(BOX(430, y - 26, 132, 52, "#F7F9FB", col))
        o.append(T(496, y - 2, "TG", 19, "middle", col, "bold"))
        o.append(T(496, y + 16, "nFET &#8741; pFET", 11, "middle", MUT))
        o.append(ARROW(562, y, 700, y, col))
        o.append(T(714, y + 6, dest, 19, "start", INK, "bold"))
        o.append(T(830, y + 6, "gated by " + ctrl, 15, "start", MUT))
    # grouping brackets
    for y0, y1, txt, sub, col in (
            (52, 194, "FORWARD pair",
             "drives this stage's output from the clock", LAL),
            (274, 416, "REVERSE pair",
             "returns the PREVIOUS stage's charge to the clock", ECRL)):
        o.append(f'<path d="M 250 {y0} L 232 {y0} L 232 {y1} L 250 {y1}" '
                 f'fill="none" stroke="{col}" stroke-width="2.5"/>')
        o.append(f'<g transform="translate(206,{(y0+y1)//2}) rotate(-90)">'
                 + T(0, 0, txt, 16, "middle", col, "bold") + '</g>')
    o.append(L(60, 232, 990, 232, w=1.5, c="#D9DEE6", dash="6 6"))
    o.append(T(510, 462,
               "4 transmission gates = 8 FETs per cell.  Without the reverse pair the "
               "cell latches high and never recovers &#8212;", 15, "middle", MUT))
    o.append(T(510, 484,
               "that pair, not the forward pair, is what makes 2LAL adiabatic.",
               15, "middle", MUT))
    render("fig_2lal_cell", W, H, o)

# =========================================================== 3. quad-rail
def quadrail():
    W, H = 1060, 470
    o = []
    o.append(T(275, 36, "&#10007;   Naive inverter: cross the two rails of one pair",
               19, "middle", WARN, "bold"))
    o.append(T(795, 36, "&#10003;   Quad-rail inverter: swap the two sub-chains",
               19, "middle", LAL, "bold"))
    o.append(L(530, 20, 530, 448, w=1.5, c="#D9DEE6", dash="7 7"))

    # ---- left: the crossing that does not work -----------------------------
    yT, yC = 100, 160
    o.append(T(88, yT + 6, "T", 16, "end", MUT, "bold"))
    o.append(T(88, yC + 6, "C", 16, "end", MUT, "bold"))
    o.append(L(98, yT, 200, yT, c=WARN)); o.append(L(200, yT, 320, yC, c=WARN))
    o.append(L(320, yC, 392, yC, c=WARN))
    o.append(L(98, yC, 200, yC, c=WARN)); o.append(L(200, yC, 320, yT, c=WARN))
    o.append(L(320, yT, 392, yT, c=WARN))
    o.append(BOX(398, 74, 98, 112, "#FFFFFF", WARN))
    o.append(T(447, 122, "next", 15, "middle", WARN, "bold"))
    o.append(T(447, 142, "stage", 15, "middle", WARN, "bold"))
    o.append(T(150, 208, "at rest = (0, VDD)", 15, "middle", MUT))
    o.append(T(150, 228, "which means FALSE", 15, "middle", MUT))
    o.append(T(447, 208, "now (VDD, 0)", 15, "middle", WARN, "bold"))
    o.append(T(447, 228, "= permanent TRUE", 15, "middle", WARN, "bold"))
    o.append(BOX(70, 252, 420, 88, "#FDF1F1", WARN, 2, 8))
    o.append(T(280, 280, "The pass gates now hold both clock rails connected.",
               15, "middle", INK))
    o.append(T(280, 314, "6.0 pJ per stage  =  625&#215; the correct cell",
               17, "middle", WARN, "bold"))
    o.append(T(280, 380, "Costs 0 transistors &#8212; and does not work.",
               15, "middle", MUT, "normal", "italic"))

    # ---- right: quad-rail --------------------------------------------------
    yA, yN = 100, 172
    def stage(x, y, lbl, col, w=62, h=38):
        return [BOX(x, y - h // 2, w, h, "#FFFFFF", col),
                T(x + w // 2, y + 6, lbl, 16, "middle", col, "bold")]
    o.append(T(596, yA + 6, "A", 17, "end", LAL, "bold"))
    o.append(T(596, yN + 6, "A&#772;", 17, "end", LAL, "bold"))
    xs = [612, 762, 912]
    for i, x in enumerate(xs):
        o += stage(x, yA, "S%d" % (i + 1), LAL)
        o += stage(x, yN, "S%d'" % (i + 1), LAL)
    for i in range(len(xs) - 1):
        a, b = xs[i] + 62, xs[i + 1]
        o.append(L(a, yA, b, yN, c=LAL)); o.append(L(a, yN, b, yA, c=LAL))
    o.append(ARROW(974, yA, 1024, yA, LAL)); o.append(ARROW(974, yN, 1024, yN, LAL))
    o.append(T(795, 228, "Each chain stays a valid dual-rail pair;", 15, "middle", INK))
    o.append(T(795, 250, "the SWAP is the inversion.", 16, "middle", INK, "bold"))
    o.append(BOX(590, 274, 420, 66, "#F1F9F5", LAL, 2, 8))
    o.append(T(800, 300, "Correct at both bit values, at every frequency;", 15, "middle", INK))
    o.append(T(800, 322, "measured exactly 2.000&#215; the buffer energy.", 15, "middle", INK))
    o.append(T(795, 380, "Costs 0 transistors in the cell, but doubles the datapath:",
               15, "middle", MUT, "normal", "italic"))
    o.append(T(795, 402, "16 FETs per quad-rail column against ECRL's 4.",
               15, "middle", MUT, "normal", "italic"))
    render("fig_quadrail", W, H, o)

# ============================================================== 4. work flow
def flow():
    W, H = 1180, 470
    o = []
    steps = [
        ("1", "Read the 1996\nECRL paper", MUT),
        ("2", "Build the ECRL\ncell in SPICE", MUT),
        ("3", "SKY130 + ngspice\nmodel set-up", MUT),
        ("4", "Functional\nwaveform check", LAL),
        ("5", "Power-clock energy\nby integration", LAL),
    ]
    steps2 = [
        ("6", "Find + fix 3 defects\nin the methodology", WARN),
        ("7", "Width & frequency\nsweeps, automated", BLUE),
        ("8", "Build 2LAL cell\n(3 corrections)", WARN),
        ("9", "Matched-condition\ncomparison", ECRL),
        ("10", "Next: multi-gate\nchains, layout", MUT),
    ]
    def row(items, y):
        x0, bw, gap = 40, 196, 30
        for i, (n, txt, col) in enumerate(items):
            x = x0 + i * (bw + gap)
            o.append(BOX(x, y, bw, 108, "#FFFFFF", col, 2.5, 10))
            o.append(f'<circle cx="{x+24}" cy="{y+24}" r="15" fill="{col}"/>')
            o.append(T(x + 24, y + 29, n, 14, "middle", "#FFFFFF", "bold"))
            for j, line in enumerate(txt.split("\n")):
                o.append(T(x + bw // 2 + 12, y + 62 + j * 21, line, 15, "middle", INK))
            if i < len(items) - 1:
                o.append(ARROW(x + bw + 4, y + 54, x + bw + gap - 4, y + 54, "#9AA4B2"))
    row(steps, 60)
    row(steps2, 258)
    # wrap arrow
    o.append(f'<path d="M 1146 114 L 1166 114 L 1166 200 L 34 200 L 34 312 L 30 312" '
             f'fill="none" stroke="#9AA4B2" stroke-width="2.5" marker-end="url(#ah)"/>')
    o.append(T(590, 226, "where the work actually got interesting", 14,
               "middle", MUT, "normal", "italic"))
    o.append(T(590, 420,
               "Steps 1-5 reproduce the method.  Steps 6-9 are what we contribute: "
               "a measurement definition we can defend, and a comparison made under it.",
               16, "middle", INK))
    render("fig_flow", W, H, o)

for f in (ecrl_cell, lal_cell, quadrail, flow):
    f()
