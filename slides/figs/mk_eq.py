#!/usr/bin/env python3
"""Equation panels for the deck, rendered to PNG so glyph coverage never
depends on whatever fonts the presenting machine happens to have."""
import os, subprocess, sys
OUT, TMP = sys.argv[1], sys.argv[2]
DARK, WHITE, MINT, DIM = "#14243A", "#FFFFFF", "#7FD1B9", "#B4C1D1"
SER  = "'DejaVu Serif', Georgia, serif"
SANS = "'DejaVu Sans', Helvetica, Arial, sans-serif"

def T(x, y, s, size=17, anchor="middle", fill=WHITE, weight="normal",
      font=SANS, ls=None):
    e = f' letter-spacing="{ls}"' if ls else ''
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}"'
            f'{e} xml:space="preserve">{s}</text>')

def sub(t, sz=22, d=9):
    return f'<tspan dy="{d}" font-size="{sz}">{t}</tspan><tspan dy="{-d}">'

def render(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>'
           f'<rect width="{w}" height="{h}" rx="11" fill="{DARK}"/>'
           + "".join(body) + '</svg>')
    hp = os.path.join(TMP, name + ".html")
    open(hp, "w").write(f'<html><body style="margin:0">{svg}</body></html>')
    png = os.path.join(OUT, name + ".png")
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu",
                    "--no-sandbox", "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={w},{h}", "--force-device-scale-factor=2",
                    "file://" + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", png)

# ---- the two regimes -------------------------------------------------------
render("fig_eq_regimes", 912, 318, [
    T(46, 44, "THE TWO REGIMES", 18, "start", MINT, "bold", ls=4),
    T(46, 132, "E" + sub("CMOS") + "&#160;&#160;=&#160;&#160;&#189; C V"
      "<tspan dy='-14' font-size='26'>2</tspan></tspan>",
      40, "start", WHITE, "bold", SER),
    T(48, 172, "the same energy however slowly you switch", 21, "start", DIM),
    T(46, 246, "E" + sub("adiabatic") + "&#160;&#160;&#8776;&#160;&#160;"
      "(2RC / T) &#183; C V<tspan dy='-14' font-size='26'>2</tspan></tspan>",
      40, "start", MINT, "bold", SER),
    T(48, 286, "falls as the transition time T is stretched", 21, "start", DIM),
])

# ---- the measurement -------------------------------------------------------
render("fig_eq_measure", 860, 352, [
    T(46, 46, "THE MEASUREMENT", 18, "start", MINT, "bold", ls=4),
    T(430, 138, "E&#160;&#160;=&#160;&#160;&#8747; &#8722; V" + sub("&#934;", 24)
      + "(t) &#183; I</tspan>" + sub("&#934;", 24) + "(t)&#160;&#160;dt</tspan>",
      40, "middle", WHITE, "bold", SER),
    T(430, 184, "over one full T" + sub("clock", 17, 6)
      + ", for one gate</tspan>", 22, "middle", DIM),
    T(430, 246, "1 &#215; 10<tspan dy='-12' font-size='18'>&#8722;15</tspan>"
      "<tspan dy='12'> J&#160;&#160;=&#160;&#160;1 fJ</tspan>",
      27, "middle", MINT, "bold"),
    T(430, 300, "ngspice defines source current into the + terminal,",
      19, "middle", DIM),
    T(430, 324, "so the power delivered to the circuit is &#8722;V&#183;I.",
      19, "middle", DIM),
])
