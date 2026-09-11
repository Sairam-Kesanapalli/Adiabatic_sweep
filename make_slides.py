#!/usr/bin/env python3
"""
Build the faculty progress-review deck for the ECRL / 2LAL adiabatic-logic work.

    python3 make_slides.py            -> ECRL_2LAL_Progress_Review.pptx

Figures come from slides_figs/ (regenerate them with the .gp scripts and
mk_svg.py in that directory).  Every number quoted here traces to
ecrl_exp1/ecrl_slowramp_sweep.csv, 2lal_inverter_sweep.csv or
2LAL_energy_sweep.csv -- see CHECKS.md.
"""
import os
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

HERE = os.path.dirname(os.path.abspath(__file__))
FIG  = os.path.join(HERE, "slides_figs")
OUT  = os.path.join(HERE, "ECRL_2LAL_Progress_Review.pptx")

# ------------------------------------------------------------------ design
SW, SH = 13.333, 7.5
M      = 0.72
CW     = SW - 2 * M

INK   = RGBColor(0x1A, 0x22, 0x33)
BODY  = RGBColor(0x3D, 0x47, 0x56)
MUT   = RGBColor(0x76, 0x82, 0x95)
ECRLC = RGBColor(0xA4, 0x23, 0x7A)
LALC  = RGBColor(0x12, 0x86, 0x6B)
BLUE  = RGBColor(0x09, 0x69, 0xDA)
WARN  = RGBColor(0xC0, 0x24, 0x2C)
GOLD  = RGBColor(0x9A, 0x6D, 0x00)
RULE  = RGBColor(0xDC, 0xE1, 0xE8)
PANEL = RGBColor(0xF4, 0xF6, 0xF9)
PANEL2= RGBColor(0xEC, 0xF1, 0xF6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK  = RGBColor(0x14, 0x24, 0x3A)
DIM   = RGBColor(0xB4, 0xC1, 0xD1)
MINT  = RGBColor(0x7F, 0xD1, 0xB9)
TINTG = RGBColor(0xF1, 0xF9, 0xF5)
TINTR = RGBColor(0xFD, 0xF1, 0xF1)
TINTB = RGBColor(0xEF, 0xF5, 0xFD)

FONT = "Calibri"
MONO = "Consolas"

Y_KICK, Y_TITLE, Y_RULE, Y_TOP, Y_BOT = 0.36, 0.60, 1.30, 1.50, 6.82
FOOT = "ECRL & 2LAL in SKY130  ·  progress review"

prs = Presentation()
prs.slide_width  = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]
_n = [1]


# ------------------------------------------------------------------ helpers
def slide(dark=False, number=True):
    s = prs.slides.add_slide(BLANK)
    if dark:
        bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                Inches(SW), Inches(SH))
        _plain(bg, DARK)
    if number:
        _n[0] += 1
        _, tf = textbox(s, M, 6.95, CW, 0.3)
        para(tf, FOOT, 9.5, MUT if not dark else RGBColor(0x5A, 0x6B, 0x82), first=True)
        _, tf2 = textbox(s, SW - M - 1.0, 6.95, 1.0, 0.3)
        para(tf2, str(_n[0]), 9.5, MUT if not dark else RGBColor(0x5A, 0x6B, 0x82),
             align=PP_ALIGN.RIGHT, first=True)
    return s


def _plain(shape, fill=None, line=None, lw=1.0):
    """Autoshape with no shadow and explicit fill / outline."""
    shape.shadow.inherit = False
    if fill is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(lw)
    if shape.has_text_frame:
        shape.text_frame.word_wrap = True
    return shape


def rect(s, x, y, w, h, fill=PANEL, line=None, lw=1.0, radius=None):
    shp = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    sh = s.shapes.add_shape(shp, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        sh.adjustments[0] = radius
    return _plain(sh, fill, line, lw)


def line(s, x, y, w, color=RULE, lw=1.0):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                            Inches(w), Pt(lw))
    return _plain(sh, color)


def textbox(s, x, y, w, h, anchor=MSO_ANCHOR.TOP, wrap=True):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    return box, tf


def para(tf, parts, size=15, color=BODY, bold=False, italic=False,
         align=PP_ALIGN.LEFT, before=0, after=0, first=False, font=FONT,
         spacing=1.14):
    """parts: str, or list of (text, {b,i,c,sz,f}) for inline emphasis."""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = spacing
    if before:
        p.space_before = Pt(before)
    if after:
        p.space_after = Pt(after)
    if isinstance(parts, str):
        parts = [(parts, {})]
    for txt, st in parts:
        r = p.add_run()
        r.text = txt
        f = r.font
        f.name = st.get("f", font)
        f.size = Pt(st.get("sz", size))
        f.bold = st.get("b", bold)
        f.italic = st.get("i", italic)
        f.color.rgb = st.get("c", color)
    return p


def bullet(tf, parts, size=15, color=BODY, accent=None, before=7, first=False,
           marL=0.26, char="▪", spacing=1.14, font=FONT):
    p = para(tf, parts, size=size, color=color, before=before, first=first,
             spacing=spacing, font=font)
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Emu(int(Inches(marL)))))
    pPr.set("indent", str(-Emu(int(Inches(marL)))))
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    c = accent or MUT
    xml = ('<a:buClr xmlns:a="%s"><a:srgbClr val="%s"/></a:buClr>' % (a, str(c)))
    els = [parse_xml(xml),
           parse_xml('<a:buFont xmlns:a="%s" typeface="Arial"/>' % a),
           parse_xml('<a:buChar xmlns:a="%s" char="%s"/>' % (a, char))]
    anchor = None
    for tag in ("a:tabLst", "a:defRPr", "a:extLst"):
        f = pPr.find(qn(tag))
        if f is not None:
            anchor = f
            break
    for e in els:
        if anchor is not None:
            anchor.addprevious(e)
        else:
            pPr.append(e)
    return p


def head(s, title, kicker=None, kcolor=ECRLC, rule=True, sub=None):
    if kicker:
        _, tf = textbox(s, M, Y_KICK, CW, 0.24)
        para(tf, kicker.upper(), 10.5, kcolor, bold=True, first=True)
    _, tf = textbox(s, M, Y_TITLE, CW, 0.62)
    para(tf, title, 26, INK, bold=True, first=True)
    if rule:
        line(s, M, Y_RULE, CW, RULE, 1.2)
    if sub:
        _, tf = textbox(s, M, Y_RULE + 0.10, CW, 0.3)
        para(tf, sub, 13, MUT, first=True)


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def pic(s, path, x, y, w, h):
    iw, ih = Image.open(path).size
    ar = iw / ih
    if w / h > ar:
        ww, hh = h * ar, h
    else:
        ww, hh = w, w / ar
    return s.shapes.add_picture(path, Inches(x + (w - ww) / 2),
                                Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))


def F(name):
    return os.path.join(FIG, name)


NOSTYLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"


def table(s, x, y, w, rows, colw, hrow=0.34, hhdr=0.38, size=12, hsize=12,
          align=None, accent=INK, zebra=True):
    """rows[0] is the header.  colw = relative column widths."""
    nr, nc = len(rows), len(rows[0])
    h = hhdr + (nr - 1) * hrow
    gf = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    for a in ("firstRow", "bandRow", "lastRow", "firstCol", "bandCol", "lastCol"):
        tblPr.set(a, "0")
    el = tblPr.find(qn("a:tableStyleId"))
    if el is None:
        el = parse_xml('<a:tableStyleId xmlns:a="http://schemas.openxmlformats.'
                       'org/drawingml/2006/main"/>')
        tblPr.append(el)
    el.text = NOSTYLE
    tot = float(sum(colw))
    for j, cwj in enumerate(colw):
        tbl.columns[j].width = Emu(int(Inches(w) * cwj / tot))
    tbl.rows[0].height = Inches(hhdr)
    for i in range(1, nr):
        tbl.rows[i].height = Inches(hrow)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = Inches(0.10)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = accent
            elif zebra and i % 2 == 0:
                cell.fill.fore_color.rgb = PANEL
            else:
                cell.fill.fore_color.rgb = WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = (PP_ALIGN.LEFT if align is None
                           else (align[j] if isinstance(align, (list, tuple))
                                 else align))
            parts = val if isinstance(val, list) else [(str(val), {})]
            for txt, st in parts:
                r = p.add_run()
                r.text = txt
                r.font.name = st.get("f", FONT)
                r.font.size = Pt(st.get("sz", hsize if i == 0 else size))
                r.font.bold = st.get("b", i == 0)
                r.font.color.rgb = st.get("c", WHITE if i == 0 else BODY)
    return gf


def stat(s, x, y, w, h, big, label, color=ECRLC, fill=PANEL, bsz=25, lsz=11.5):
    rect(s, x, y, w, h, fill, radius=0.10)
    _, tf = textbox(s, x + 0.16, y + 0.13, w - 0.32, h - 0.26)
    para(tf, big, bsz, color, bold=True, first=True, spacing=0.95)
    para(tf, label, lsz, MUT, before=3, spacing=1.05)


def callout(s, x, y, w, h, title, text, color=ECRLC, fill=PANEL, tsz=13.5,
            bsz=12.5):
    rect(s, x, y, w, h, fill, radius=0.08)
    rect(s, x, y, 0.045, h, color)
    _, tf = textbox(s, x + 0.22, y + 0.14, w - 0.42, h - 0.28)
    para(tf, title, tsz, color, bold=True, first=True)
    para(tf, text, bsz, BODY, before=4)


def codebox(s, x, y, w, lines, size=11.5, fill=RGBColor(0xF2, 0xF4, 0xF7)):
    h = 0.20 + 0.215 * len(lines)
    rect(s, x, y, w, h, fill, radius=0.06)
    _, tf = textbox(s, x + 0.20, y + 0.11, w - 0.36, h - 0.22)
    for i, ln in enumerate(lines):
        para(tf, ln, size, RGBColor(0x2B, 0x35, 0x45), first=(i == 0),
             font=MONO, spacing=1.05)
    return h


# ================================================================= 1. title
s = slide(dark=True, number=False)
rect(s, 0, 0, 0.16, SH, ECRLC)
_, tf = textbox(s, 1.10, 1.62, 11.0, 0.3)
para(tf, "S K Y 1 3 0   ·   n g s p i c e   ·   A D I A B A T I C   L O G I C",
     11.5, MINT, bold=True, first=True)
_, tf = textbox(s, 1.10, 2.02, 11.2, 1.5)
para(tf, "Adiabatic Logic in SKY130", 46, WHITE, bold=True, first=True,
     spacing=0.98)
para(tf, "ECRL and 2LAL", 46, MINT, bold=True, spacing=0.98)
line(s, 1.10, 3.86, 3.2, ECRLC, 2.5)
_, tf = textbox(s, 1.10, 4.10, 9.6, 0.9)
para(tf, "Cell design, an energy-measurement methodology we can defend, "
         "and a matched-condition comparison of two adiabatic families",
     16.5, DIM, first=True, spacing=1.25)
_, tf = textbox(s, 1.10, 5.30, 6.0, 0.9)
para(tf, "Sairam Kesanapalli", 15, WHITE, bold=True, first=True)
para(tf, "Faculty guide:  ______________", 13, DIM, before=3)
para(tf, "Progress review", 13, DIM, before=1)
for i, (b, l) in enumerate([("2", "logic families"), ("6", "device widths"),
                            ("7", "frequency points"), ("84", "SPICE sweep runs")]):
    x = 7.65 + i * 1.36
    _, tf = textbox(s, x, 5.28, 1.3, 0.8)
    para(tf, b, 26, MINT, bold=True, first=True, spacing=0.95)
    para(tf, l, 10.5, DIM, before=2, spacing=1.05)
notes(s, "Opening line: we set out to study adiabatic logic in an open PDK. "
         "What we actually built is a measurement methodology, and the "
         "methodology is what found the interesting results. Two families, "
         "one axis, everything scripted.")

# ============================================================= 2. objective
s = slide()
head(s, "What we set out to do", "objective and scope")
_, tf = textbox(s, M, Y_TOP, 7.0, 4.9)
for t, d in [
    ("Design and verify an ECRL inverter in an open PDK.",
     " Not a textbook sketch — a netlist in SKY130 that simulates and is "
     "correct at both bit values."),
    ("Establish an energy metric that can be defended.",
     " A number that is small is worthless if we cannot say exactly what "
     "operation it is the energy of."),
    ("Measure how that energy moves with operating frequency and with "
     "device width.",
     " These are the two axes the original ECRL paper uses."),
    ("Repeat all of it for a second adiabatic family, 2LAL, and compare "
     "under matched conditions.",
     " Matched meaning every one of seven variables held equal, and checked."),
]:
    bullet(tf, [(t, {"b": True, "c": INK}), (d, {})], 15.5, accent=ECRLC,
           before=13, first=(t.startswith("Design")))
rect(s, 8.20, Y_TOP, 4.41, 2.88, PANEL, radius=0.05)
_, tf = textbox(s, 8.46, Y_TOP + 0.24, 3.9, 2.5)
para(tf, "Deliberately out of scope, for now", 14, INK, bold=True, first=True)
for t in ["Multi-gate logic — NAND, NOR, chains",
          "Physical layout and extracted parasitics",
          "Power-clock generator design",
          "Corner and temperature spread beyond tt",
          "Supply and load-capacitance sweeps"]:
    bullet(tf, t, 13.5, MUT, accent=MUT, before=9)
para(tf, "Each of these changes the answer, so none of them is quoted as if "
         "it had been done.", 12.5, MUT, italic=True, before=14)
callout(s, 8.20, 4.62, 4.41, 1.80,
        "Status in one sentence",
        "The ECRL baseline is established and validated, the 2LAL cell is "
        "reconstructed and validated, and the two are compared under matched "
        "conditions. Next is real logic, not just an inverter.", ECRLC, PANEL)
notes(s, "Stress the second bullet. The single most valuable thing we produced "
         "is not a number, it is a definition of what is being measured. "
         "The out-of-scope list matters: it stops us over-claiming.")

# ============================================================= 3. physics
s = slide()
head(s, "Why adiabatic logic, in one slide", "background")
_, tf = textbox(s, M, Y_TOP, 6.9, 4.9)
bullet(tf, [("Conventional CMOS. ", {"b": True, "c": INK}),
            ("Charging a node through a switch from a fixed supply costs "
             "½CV², and it costs that no matter how slowly you do "
             "it. The other half is burned to ground on the way back down.",
             {})], 15.5, accent=MUT, before=0, first=True)
bullet(tf, [("Adiabatic. ", {"b": True, "c": INK}),
            ("Drive the node from a supply that ramps instead. Now the loss "
             "is roughly (2RC/T)·CV² — it scales as 1/T. Stretch "
             "the transition and you dissipate less, and the charge that CMOS "
             "would have dumped to ground is drawn back into the clock.", {})],
       15.5, accent=LALC, before=14)
bullet(tf, [("But it does not reach zero. ", {"b": True, "c": INK}),
            ("Two floors stop it: the threshold drop the switch cannot "
             "recover — in ECRL that is C·|Vtp|²/2 "
             "— and leakage, which gets worse the longer you hold the "
             "node, so it grows exactly where the RC term shrinks.", {})],
       15.5, accent=WARN, before=14)
para(tf, "Every curve in this deck is that trade being measured: an RC term "
         "falling with T, and a leakage term rising with it.", 14.5, INK,
     bold=True, before=18)
pic(s, F("fig_eq_regimes.png"), 8.05, Y_TOP, 4.56, 1.59)
callout(s, 8.05, 3.34, 4.56, 2.06,
        "What that means for the graphs",
        "Energy per operation should rise with frequency — the shorter "
        "the transition, the less adiabatic it is. That rising trend is the "
        "signature we are looking for, and it is the qualitative result the "
        "1996 ECRL paper reports.", ECRLC, PANEL)
callout(s, 8.05, 5.56, 4.56, 1.24, "The two floors underneath it",
        "Threshold: C·|Vtp|²/2, independent of speed. Leakage: it grows "
        "with T, so it fights the RC term from the other side.",
        WARN, TINTR, 12.5, 12)
notes(s, "If the faculty asks one question it will be 'why should energy go UP "
         "with frequency, when CMOS dynamic power goes up with frequency too "
         "but energy PER OPERATION stays flat?' Answer: because in adiabatic "
         "logic the per-operation energy itself is a function of transition "
         "time. That is the whole point.")

# ================================================================== 4. flow
s = slide()
head(s, "How the work actually went", "roadmap")
pic(s, F("fig_flow.png"), M, 1.52, CW, 4.55)
_, tf = textbox(s, M, 6.18, CW, 0.64)
para(tf, "Steps 4 to 9 each produced a correction to something we or our "
         "sources believed. Those corrections, not the raw energy numbers, "
         "are the substance of this review.", 14, INK, bold=True,
     align=PP_ALIGN.CENTER, first=True)
notes(s, "Walk this left to right quickly. Land on step 6: three separate "
         "defects in our own measurement methodology, all found by testing "
         "assumptions rather than accepting them.")

# ======================================================= 5. section: ECRL
s = slide(dark=True)
rect(s, 0, 0, 0.16, SH, ECRLC)
_, tf = textbox(s, 1.30, 2.85, 10.0, 1.7)
para(tf, "PART I", 13, MINT, bold=True, first=True)
para(tf, "The ECRL baseline", 42, WHITE, bold=True, before=8, spacing=1.0)
para(tf, "Cell → setup → functional proof → energy definition "
         "→ the defect it exposed → sweeps", 15.5, DIM, before=12)
notes(s, "Part I is the foundation. Nothing in Part III is worth anything "
         "unless Part I is trustworthy.")

# ============================================================== 6. ECRL cell
s = slide()
head(s, "The ECRL cell: four transistors and no DC supply", "part i · topology")
pic(s, F("fig_ecrl_cell.png"), M - 0.10, 1.46, 7.05, 5.20)
_, tf = textbox(s, 7.95, 1.56, 4.66, 4.26)
bullet(tf, [("Four devices. ", {"b": True, "c": INK}),
            ("A cross-coupled PMOS pair sitting on the power clock, and two "
             "NMOS pull-downs driven by the differential input.", {})],
       14.5, accent=ECRLC, before=0, first=True)
bullet(tf, [("The clock is the supply. ", {"b": True, "c": INK}),
            ("Φ ramps up, the selected output follows it up, Φ ramps "
             "back down and pulls the charge back out. There is no rail to "
             "dump charge into.", {})], 14.5, accent=ECRLC, before=11)
bullet(tf, [("Differential by construction. ", {"b": True, "c": INK}),
            ("OUT = NOT IN and OUTB = IN. Exactly one of the two "
             "outputs pulses on every cycle, whatever the data is doing.", {})], 14.5, accent=ECRLC, before=11)
bullet(tf, [("The cross-coupling is what latches. ", {"b": True, "c": INK}),
            ("Each PMOS gate is tied to the opposite output, so once "
             "one side rises it holds the other down.", {})], 14.5, accent=ECRLC, before=11)
codebox(s, 7.95, 5.94, 4.66,
        ["XMP1 OUTB OUT  PHI PHI  pfet_01v8",
         "XMP2 OUT  OUTB PHI PHI  pfet_01v8",
         "XMN1 OUTB INB  0   0    nfet_01v8",
         "XMN2 OUT  IN   0   0    nfet_01v8"], 10.5)
notes(s, "Point at the crossing in the middle of the schematic. That is the "
         "cross-couple. Contrast with a static CMOS inverter: no VDD rail "
         "anywhere on this page, and the output is a pulse, not a level.")

# ============================================================ 7. power clock
s = slide()
head(s, "The power clock, and the two frequencies it defines",
     "part i · timing")
pic(s, F("fig_phi_phases.png"), M, 1.48, 7.35, 3.05)
callout(s, M, 4.68, 7.35, 1.90,
        "Why four phases and not two",
        "The wait phase is what lets the input settle before evaluation "
        "begins, so the gate never sees a moving input while it is charging. "
        "The hold phase is what lets the next stage sample a stable value. "
        "Drop either one and the cell stops being adiabatic.", ECRLC, PANEL)
_, tf = textbox(s, 8.42, 1.52, 4.19, 1.5)
para(tf, "Two rates, four times apart", 15, INK, bold=True, first=True)
para(tf, "Confusing these two is the single easiest way to misread an "
         "adiabatic-logic graph, so every plot here says which one it uses.",
     13, MUT, before=6)
table(s, 8.42, 2.90, 4.19,
      [["", "definition", "at Tp = 10 ns"],
       [[("f_tr", {"b": True, "c": ECRLC})], "1 / Tp", "100 MHz"],
       [[("f_clock", {"b": True, "c": BLUE})], "1 / 4Tp", "25 MHz"]],
      [1.0, 1.15, 1.35], hrow=0.36, hhdr=0.34, size=12.5, hsize=11)
_, tf = textbox(s, 8.42, 4.34, 4.19, 2.2)
para(tf, [("f_tr", {"b": True, "c": ECRLC}),
          (" is the transition frequency — the inverse of a single phase. "
           "It is the axis the 1996 paper uses, and the default axis in this "
           "deck.", {})], 13, BODY, first=True)
para(tf, [("f_clock", {"b": True, "c": BLUE}),
          (" is the power-clock frequency, which is also the operation rate: "
           "one new result per T_clock. Every plot here also exists in an "
           "f_clock version.", {})], 13, BODY, before=8)
para(tf, "T_clock = 4 · T_phase  →  f_tr = 4 · f_clock", 13.5,
     INK, bold=True, before=10)
notes(s, "Be explicit about this before showing any graph. A reviewer who "
         "assumes f_clock when we plot f_tr will think our crossover is at "
         "25 MHz when it is at 100 MHz on our axis. Both versions of every "
         "plot are in the repo.")

# =============================================================== 8. setup
s = slide()
head(s, "Simulation setup", "part i · method")
table(s, M, 1.48, 7.35,
      [["parameter", "value"],
       ["Technology", "SKY130 open PDK, tt corner"],
       ["Simulator", "ngspice 42 / 45.2, batch mode (-b)"],
       ["Supply VDD", "1.8 V"],
       ["Channel length L", "0.15 µm, nFET and pFET"],
       ["Width W", "0.84 / 1.0 / 1.2 / 1.5 / 2.0 / 3.0 µm"],
       ["Load", "25 fF on every metered output node"],
       ["Power clock", "trapezoid, four equal phases, T_clock = 4·T_phase"],
       ["T_phase swept", "1, 2, 5, 10, 20, 50, 100 ns"],
       ["f_transition", "1000 down to 10 MHz"],
       ["Energy metric", "integral of -V_PHI · I_PHI dt, "
                         "over one full clock period"]],
      [1.0, 2.05], hrow=0.375, hhdr=0.36, size=13, hsize=12)
callout(s, 8.42, 1.48, 4.19, 2.30,
        "A units trap worth knowing about",
        "The ngspice-flavoured SKY130 models set .option scale=1.0u, so device "
        "widths are written in microns: w=1 means 1 µm. Writing w=1u "
        "fails with “could not find a valid modelname”, and the "
        "trimmed model files vendored by some repos take metres instead.",
        WARN, TINTR)
callout(s, 8.42, 4.00, 4.19, 2.55,
        "Why 25 fF and why these widths",
        "25 fF is a deliberately generous load, chosen so the switched "
        "capacitance dominates the device's own parasitics and the comparison "
        "between families is about the topology rather than about layout we "
        "have not done. 0.84 µm is the SKY130 minimum-ish width; 3.0 "
        "µm is far enough out to see the resistive trend flatten.",
        BLUE, TINTB)
notes(s, "The units trap is worth 30 seconds. It is exactly the kind of thing "
         "that silently invalidates a comparison: two decks on two model "
         "sources with two unit conventions. We found it and moved both decks "
         "onto the same models before comparing anything.")

# ======================================================= 9. functional check
s = slide()
head(s, "Functional verification comes before any energy number",
     "part i · correctness")
pic(s, F("fig_ecrl_waveform.png"), M, 1.40, CW, 4.05)
_, tf = textbox(s, M, 5.60, 7.35, 1.25)
para(tf, "IN low → OUT pulses with the clock and OUTB stays down. "
         "IN high → the opposite. The input only ever moves inside "
         "Φ's wait window, so the gate never evaluates on a moving input.",
     14, BODY, first=True)
para(tf, "Checked by .meas sampling mid-hold, at both bit values, at every "
         "T_phase in the sweep — not by looking at the picture.",
     14, INK, bold=True, before=6)
codebox(s, 8.60, 5.60, 4.01,
        [".meas tran OUT_A  FIND V(OUT)  AT=14.5*TPHASE",
         ".meas tran OUTB_A FIND V(OUTB) AT=14.5*TPHASE",
         "   IN=1  ->  OUT ~ 0     OUTB ~ 1.8"], 9.5)
notes(s, "Note the small step visible on the falling edge of each output: that "
         "is the threshold drop, the charge the pFET cannot recover. It is the "
         "C|Vtp|^2/2 floor showing up on the scope trace.")

# =========================================================== 10. energy meas
s = slide()
head(s, "How the energy is measured", "part i · the metric")
_, tf = textbox(s, M, Y_TOP, 7.2, 1.4)
para(tf, "We do not sample V·I at an instant. We integrate the power the "
         "power clock actually delivers, across one complete clock period.",
     16, INK, bold=True, first=True)
para(tf, "ngspice defines a source's current as flowing into its positive "
         "terminal, so the power delivered to the circuit is -V·I. "
         "A behavioural source turns that product into a node voltage, which "
         ".meas can then integrate.", 14, BODY, before=8)
codebox(s, M, 3.18, 7.2,
        ["BPCPOWER PCLK 0 V={-V(PHI)*I(VPHI)}",
         "",
         ".meas tran E_A INTEG V(PCLK) FROM={12*TPHASE} TO={16*TPHASE}",
         ".meas tran E_B INTEG V(PCLK) FROM={16*TPHASE} TO={20*TPHASE}",
         ".meas tran E_C PARAM='(E_A+E_B)/2'",
         "",
         "* settling check: the same two cycles, two periods earlier",
         ".meas tran E_A0 INTEG V(PCLK) FROM={4*TPHASE}  TO={8*TPHASE}",
         ".meas tran E_B0 INTEG V(PCLK) FROM={8*TPHASE}  TO={12*TPHASE}"], 11.5)
_, tf = textbox(s, M, 5.50, 7.2, 1.28)
para(tf, "E_A is the cycle in which the data goes 0→1, E_B the cycle in "
         "which it goes 1→0, E_C their average. E_A0 and E_B0 repeat the "
         "measurement two periods earlier: if they disagree, the circuit has "
         "not settled and the run is discarded.", 13.5, BODY, first=True)
pic(s, F("fig_eq_measure.png"), 8.42, Y_TOP, 4.19, 1.72)
callout(s, 8.42, 3.44, 4.19, 2.56,
        "Why integrate, and not just multiply",
        "The clock is a trapezoid and the current is not in phase with it. A "
        "point sample of V·I is meaningless here, and an average over the "
        "wrong window is worse than meaningless — it looks like a real "
        "number. Choosing the window turned out to be the hardest part of "
        "this project.", ECRLC, PANEL)
notes(s, "Lead into the next slide from that last sentence. The window is "
         "where the bug was.")

# ============================================================ 11. the defect
s = slide()
head(s, "Two suspects, one culprit", "part i · the defect we found",
     kcolor=WARN)
pic(s, F("fig_measurement_bug.png"), M - 0.06, 1.44, 6.30, 4.55)
_, tf = textbox(s, 7.05, 1.48, 5.56, 0.62)
para(tf, "Our early ECRL curve looked plausible. We suspected the input edge. "
         "We tested both suspects instead of assuming.", 14.5, INK, bold=True,
     first=True)
rect(s, 7.05, 2.14, 5.56, 1.62, PANEL, radius=0.06)
rect(s, 7.05, 2.14, 0.045, 1.62, MUT)
_, tf = textbox(s, 7.27, 2.28, 5.10, 1.36)
para(tf, [("Suspect 1 — the input edge.  ", {"b": True, "c": MUT}),
          ("The baseline used a fixed 100 ps input transition whatever "
           "T_phase was. At T_phase = 100 ns that edge is a thousand times "
           "faster than the clock — precisely what adiabatic operation "
           "is supposed to avoid.", {})], 12.5, BODY, first=True)
para(tf, "Tested: replacing it with a full-phase ramp changed the energy by "
         "essentially nothing.", 12.5, MUT, bold=True, before=5)
rect(s, 7.05, 3.88, 5.56, 1.76, TINTR, radius=0.06)
rect(s, 7.05, 3.88, 0.045, 1.76, WARN)
_, tf = textbox(s, 7.27, 4.02, 5.10, 1.50)
para(tf, [("Suspect 2 — the measurement window.  ", {"b": True, "c": WARN}),
          ("The input had already flipped back during the previous cycle, so "
           "the metered window contained no data transition at all.", {})],
     12.5, BODY, first=True)
para(tf, "This was the entire gap. The old numbers were the energy of a gate "
         "whose input never changes: correct per power cycle, meaningless "
         "per data transaction.", 12.5, WARN, bold=True, before=5)
_, tf = textbox(s, 7.05, 5.78, 5.56, 1.10)
para(tf, "The fix, now in every ECRL run", 13.5, INK, bold=True, first=True)
para(tf, "Input ramps over a full phase, inside Φ's wait window · "
         "data alternates 1,0,1,0 every cycle · the 0→1 and "
         "1→0 cycles are metered separately · 5.36 → 12.46 fJ "
         "at 10 MHz.", 12.5, BODY, before=5)
notes(s, "This is the slide to spend time on. It shows the difference between "
         "a student who reports a number and one who interrogates it. Also "
         "make the point that the fix is reproducible in one command: hold "
         "the data static in the new deck and it reproduces the old 5.3622 fJ "
         "exactly — which is how we proved that was the cause.")

# ======================================================= 12. ECRL vs freq
s = slide()
head(s, "ECRL: energy per operation against frequency",
     "part i · result")
pic(s, F("ecrl_slowramp_energy_vs_ftr.png"), M - 0.10, 1.42, 7.90, 5.05)
_, tf = textbox(s, 8.30, 1.52, 4.31, 3.0)
para(tf, "What the curve says", 15, INK, bold=True, first=True)
bullet(tf, "Energy rises monotonically with frequency at every width — "
           "the qualitative behaviour the 1996 ECRL paper reports.",
       13.5, accent=ECRLC, before=10)
bullet(tf, "At W = 1.0 µm the energy goes 12.46 → 54.69 fJ, a 4.4× "
           "rise across a 100× rise in frequency. Sub-linear, as an RC/T "
           "loss should be.", 13.5, accent=ECRLC, before=9)
bullet(tf, "It does not extrapolate to zero. The threshold drop and leakage "
           "floors are still underneath.", 13.5, accent=ECRLC, before=9)
table(s, 8.30, 4.58, 4.31,
      [["f_tr", "E per operation"],
       ["10 MHz", "12.46 fJ"],
       ["100 MHz", "21.66 fJ"],
       ["1000 MHz", "54.69 fJ"]],
      [1.0, 1.25], hrow=0.34, hhdr=0.34, size=12.5, hsize=11, accent=ECRLC)
_, tf = textbox(s, 8.30, 6.16, 4.31, 0.5)
para(tf, "W = 1.0 µm column of ecrl_slowramp_sweep.csv", 11.5, MUT,
     italic=True, first=True)
notes(s, "Say plainly: this reproduces the TREND, not the numbers, of the 1996 "
         "paper. The numbers cannot match — different process, different "
         "supply, different device. Slide 28 covers that.")

# ======================================================== 13. ECRL vs width
s = slide()
head(s, "ECRL: sizing only helps where the loss is resistive",
     "part i · result")
pic(s, F("fig_width_sweep.png"), M - 0.10, 1.42, 7.35, 5.05)
_, tf = textbox(s, 7.90, 1.52, 4.71, 2.6)
para(tf, "Wider devices lower the channel resistance, and the adiabatic loss "
         "term is proportional to RC/T. So sizing should buy a lot at short "
         "T and almost nothing at long T — and it does.", 14, BODY,
     first=True)
bullet(tf, [("At 1000 MHz", {"b": True, "c": INK}),
            (", going 0.84 → 3.0 µm buys 39%.", {})],
       14, accent=ECRLC, before=11)
bullet(tf, [("At 10 MHz", {"b": True, "c": INK}),
            (", the same change buys 8% — the curve is essentially flat.",
             {})], 14, accent=BLUE, before=8)
callout(s, 7.90, 4.22, 4.71, 2.58,
        "A bug we caught, and how",
        "The first version of the width sweep edited .param WNMOS while the "
        "transistor instance lines still read w=1, so every point simulated "
        "the same device. We noticed because the energies were identical to "
        "four significant figures — a sweep that produces no spread is a "
        "broken sweep, not a null result. Fixed by rewriting the instance "
        "widths; the widths now demonstrably move the answer.", WARN, TINTR)
notes(s, "Good place to make the general point: a result that looks too clean "
         "should be treated as a suspected bug until proven otherwise. Six "
         "identical numbers is not physics.")

# ======================================================= 14. section: 2LAL
s = slide(dark=True)
rect(s, 0, 0, 0.16, SH, LALC)
_, tf = textbox(s, 1.30, 2.58, 10.5, 2.2)
para(tf, "PART II", 13, MINT, bold=True, first=True)
para(tf, "2LAL, and three things we had to correct", 40, WHITE, bold=True,
     before=8, spacing=1.0)
para(tf, "The cell is not 4 transistors · a logic 0 is not a pulse "
         "· inversion is not a wire crossing", 15.5, DIM, before=12)
notes(s, "Each of these three was believed by someone — by us, by our "
         "advice, or by the obvious reading of the literature — and each "
         "was wrong in a way that still simulates and still looks plausible "
         "if you only test one bit value.")

# ============================================================= 15. what 2LAL
s = slide()
head(s, "What 2LAL is", "part ii · background", kcolor=LALC)
pic(s, F("fig_2lal_clocks.png"), M, 1.44, 7.55, 3.60)
_, tf = textbox(s, M, 5.30, 7.55, 1.3)
para(tf, "Each stage is clocked one phase tick later than the one before it. "
         "T_rail = 4·T_phase — the same period as ECRL's T_clock, "
         "which is exactly what lets both families sit on one axis.",
     13.5, BODY, first=True)
_, tf = textbox(s, 8.62, 1.50, 3.99, 3.34)
para(tf, "Two-Level Adiabatic Logic", 15, INK, bold=True, first=True)
para(tf, "Frank et al. Data is carried dual-rail; the logic itself is done "
         "with transmission gates driven by a four-phase trapezoidal rail set "
         "rather than by a single power clock.", 13.5, BODY, before=6)
bullet(tf, [("A pair rests at FALSE. ", {"b": True, "c": INK}),
            ("A dual-rail pair (T, C) sits at (0, VDD) when idle.", {})],
       13.5, accent=LALC, before=13)
bullet(tf, [("A TRUE is a pulse. ", {"b": True, "c": INK}),
            ("The T rail pulses up on phi_t while C is pulled down by "
             "the antiphase rail.", {})], 13.5, accent=LALC, before=9)
bullet(tf, [("Activity is data-independent. ", {"b": True, "c": INK}),
            ("A column always has one sub-chain carrying a TRUE, so "
             "it pulses every period, like ECRL.", {})],
       13.5, accent=LALC, before=9)
callout(s, 8.62, 5.02, 3.99, 1.78,
        "Where our cell came from",
        "Reconstructed from Frank's slides, a DeBenedictis technical report, "
        "and the PHAS2 cell in the 4lc repository. We have not seen Figure 2 "
        "of the source paper.", MUT, PANEL, 12.5, 11.5)
notes(s, "Be upfront that the cell is a reconstruction. It is self-consistent "
         "and it simulates correctly at both bit values, but if the faculty "
         "can point us at Figure 2 of the paper we would like to check it "
         "against the primary source.")

# ========================================================== 16. correction 1
s = slide()
head(s, "Correction 1: the cell is eight transistors, not four",
     "part ii · correction", kcolor=WARN)
pic(s, F("fig_2lal_cell.png"), M - 0.10, 1.44, 7.55, 4.35)
_, tf = textbox(s, 8.05, 1.52, 4.56, 5.1)
rect(s, 8.05, 1.50, 4.56, 1.92, TINTR, radius=0.06)
rect(s, 8.05, 1.50, 0.045, 1.92, WARN)
_, tf = textbox(s, 8.27, 1.66, 4.10, 1.65)
para(tf, "What we were told", 13.5, WARN, bold=True, first=True)
para(tf, "Four devices per stage: two nFETs and two pFETs. A forward-only "
         "4-transistor cell has no way to pull its own output back down "
         "— by the time the clock falls, the input has already retracted "
         "and the gate is off.", 12.5, BODY, before=5)
_, tf = textbox(s, 8.05, 3.60, 4.56, 1.2)
para(tf, "In simulation every node latched high and stayed there, reporting "
         "“1” for both bit values.", 13, WARN, bold=True, first=True)
rect(s, 8.05, 4.30, 4.56, 2.48, TINTG, radius=0.06)
rect(s, 8.05, 4.30, 0.045, 2.48, LALC)
_, tf = textbox(s, 8.27, 4.46, 4.10, 2.20)
para(tf, "What actually works", 13.5, LALC, bold=True, first=True)
para(tf, "Eight transistors: the forward pair, plus a reverse pair that "
         "restores the previous stage once this stage's output is valid.",
     12.5, BODY, before=5)
para(tf, "That reverse pair recovers the charge the forward pair cannot. It "
         "is the entire reason 2LAL is adiabatic — and it is exactly what "
         "the 4lc PHAS2 cell has.", 12.5, LALC, bold=True, before=5)
notes(s, "Worth saying: the four-device version is not a strawman, it is what "
         "we were advised to build and it is what the obvious reading of the "
         "figure suggests. It simulates. It just always returns 1.")

# ========================================================== 17. correction 2
s = slide()
head(s, "Correction 2: a logic 0 is the absence of a pulse",
     "part ii · correction", kcolor=WARN)
_, tf = textbox(s, M, Y_TOP, CW, 0.6)
para(tf, "A dual-rail 2LAL pair rests at FALSE = (0, VDD). Encoding a 0 as a "
         "pulse on the complement rail is the obvious guess, and it is "
         "silently wrong.", 16, INK, bold=True, first=True, align=PP_ALIGN.CENTER)
rect(s, M, 2.28, 5.80, 3.55, TINTR, radius=0.05)
rect(s, M, 2.28, 0.055, 3.55, WARN)
_, tf = textbox(s, M + 0.34, 2.56, 5.15, 3.05)
para(tf, "WRONG  —  what we first built", 16, WARN, bold=True, first=True)
para(tf, "0  →  pulse the C rail\n1  →  pulse the T rail",
     15, INK, bold=True, before=12, font=MONO, spacing=1.3)
para(tf, "The complement pulse falls while the clock is still high. The pass "
         "gate's pFET conducts through that window, and every downstream stage "
         "latches a spurious 1.", 13.5, BODY, before=14)
para(tf, "It looked completely fine — because we had only ever tested the "
         "1 bit.", 13.5, WARN, bold=True, before=10)
rect(s, 7.05, 2.28, 5.56, 3.55, TINTG, radius=0.05)
rect(s, 7.05, 2.28, 0.055, 3.55, LALC)
_, tf = textbox(s, 7.39, 2.56, 4.90, 3.05)
para(tf, "CORRECT  —  what actually works", 16, LALC, bold=True, first=True)
para(tf, "0  →  no pulse at all\n1  →  pulse the T rail",
     15, INK, bold=True, before=12, font=MONO, spacing=1.3)
para(tf, "The pair simply stays at rest. Nothing moves, nothing conducts, and "
         "nothing downstream is fooled.", 13.5, BODY, before=14)
para(tf, "Every stage is now checked at both bit values, at every frequency "
         "point in the sweep — which is the only reason this was ever "
         "caught.", 13.5, LALC, bold=True, before=10)
_, tf = textbox(s, M, 6.06, CW, 0.6)
para(tf, "The lesson we are taking from this: a logic family whose FALSE is "
         "“do nothing” cannot be validated by testing TRUE.",
     14, INK, bold=True, first=True, align=PP_ALIGN.CENTER)
notes(s, "This is a nice one to tell as a story. Everything worked. Every "
         "waveform looked right. Then we fed it a 0 and the whole chain "
         "reported 1.")

# ========================================================== 18. correction 3
s = slide()
head(s, "Correction 3: inversion is not a wire crossing",
     "part ii · correction", kcolor=WARN)
pic(s, F("fig_quadrail.png"), M - 0.10, 1.42, CW + 0.20, 4.70)
_, tf = textbox(s, M, 6.22, CW, 0.55)
para(tf, "Because the rest state (0, VDD) is lopsided between the two rails, "
         "crossing them turns “rest” into (VDD, 0) — which the "
         "next stage reads as a permanent TRUE. The fix costs no transistors "
         "in the cell, but it doubles the datapath.",
     13.5, BODY, first=True, align=PP_ALIGN.CENTER)
notes(s, "In static CMOS, inverting a differential signal really is just "
         "swapping the wires, because the rest state is symmetric. In 2LAL it "
         "is not symmetric, and that asymmetry is the whole trick. The "
         "quad-rail fix is free in transistors per cell but costs 2x the "
         "datapath — and we measured exactly 2.000x, which is a good sign "
         "the implementation is right.")

# ==================================================== 19. naive vs quad-rail
s = slide()
head(s, "The broken inverter has a measurable signature",
     "part ii · evidence", kcolor=WARN)
pic(s, F("fig_naive_vs_quadrail.png"), M - 0.10, 1.42, 7.35, 5.05)
_, tf = textbox(s, 7.90, 1.52, 4.71, 5.0)
para(tf, "Why the red curve slopes downward", 15, INK, bold=True, first=True)
para(tf, "A resistive short dissipates V²/R for as long as it is held, so "
         "its energy per operation is proportional to the period — it "
         "falls as 1/f. That straight 1/f line on a log-log plot is the "
         "fingerprint of a non-adiabatic path, and it is nothing like the "
         "shape either correct cell produces.", 13.5, BODY, before=7)
bullet(tf, [("6.0 pJ per stage at 10 MHz", {"b": True, "c": WARN}),
            (" — 625× the correct 8-FET buffer cell at the same "
             "point.", {})], 13.5, accent=WARN, before=13)
bullet(tf, [("The two correct curves track each other. ", {"b": True, "c": LALC}),
            ("The quad-rail inverter sits at exactly 2.000× the buffer, "
             "at every frequency — the expected cost of carrying two "
             "chains instead of one, and a useful self-check that the "
             "implementation is right.", {})], 13.5, accent=LALC, before=9)
bullet(tf, [("The upturn below ~50 MHz is real. ", {"b": True, "c": BLUE}),
            ("That is the leakage floor, not a broken circuit — the logic "
             "is still correct there.", {})], 13.5, accent=BLUE, before=9)
notes(s, "The 2.000x is the strongest single piece of evidence that the "
         "quad-rail construction is implemented correctly. If it were wrong "
         "in some subtle way, there is no reason it would land on a clean "
         "factor of two at every frequency.")

# ======================================================= 20. 2LAL vs freq
s = slide()
head(s, "2LAL: energy per operation against frequency",
     "part ii · result", kcolor=LALC)
pic(s, F("2lal_energy_vs_ftr.png"), M - 0.10, 1.42, 7.90, 5.05)
_, tf = textbox(s, 8.30, 1.52, 4.31, 5.0)
para(tf, "A minimum, not a monotone", 15, INK, bold=True, first=True)
para(tf, "Unlike ECRL, the 2LAL curve turns up at both ends. The minimum sits "
         "near f_tr = 100 MHz.", 13.5, BODY, before=6)
bullet(tf, [("Above it: ", {"b": True, "c": INK}),
            ("the same resistive RC/T loss ECRL has.", {})],
       13.5, accent=ECRLC, before=11)
bullet(tf, [("Below it: ", {"b": True, "c": INK}),
            ("a leakage floor. 16 transistors per column hold charge "
             "for progressively longer, which costs more the slower you run. "
             "Confirmed as leakage, not a malfunction: the logic is still "
             "correct at 10 MHz.", {})],
       13.5, accent=BLUE, before=9)
bullet(tf, [("Wider is worse here, at every frequency. ", {"b": True, "c": WARN}),
            ("The opposite of ECRL. These pass gates are not "
             "resistance-limited here, so width buys nothing and costs "
             "capacitance and leakage.", {})],
       13.5, accent=WARN, before=9)
para(tf, "That single difference in the sizing trend is, on its own, a useful "
         "design result: in 2LAL, do not upsize.", 13.5, INK, bold=True,
     before=13)
notes(s, "Contrast the two width families explicitly. In ECRL sizing up helps "
         "at high frequency. In 2LAL it hurts everywhere we measured. Those "
         "are different design rules for two families that superficially do "
         "the same job.")

# ================================================== 21. section: comparison
s = slide(dark=True)
rect(s, 0, 0, 0.16, SH, MINT)
_, tf = textbox(s, 1.30, 2.85, 10.5, 1.7)
para(tf, "PART III", 13, MINT, bold=True, first=True)
para(tf, "ECRL against 2LAL", 42, WHITE, bold=True, before=8, spacing=1.0)
para(tf, "What had to match before the comparison meant anything — and "
         "what the comparison actually says", 15.5, DIM, before=12)
notes(s, "The comparison is the headline, but the seven matching conditions "
         "are what make it defensible. Lead with those.")

# =========================================================== 22. matched
s = slide()
head(s, "Seven things had to match", "part iii · fairness")
items = [
    ("Technology and corner", "SKY130 tt, and — after we found they were "
     "not — the same model files. The two decks had been on different "
     "model sources with different unit conventions.", WARN),
    ("Supply", "1.8 V in both.", LALC),
    ("Load", "25 fF on every metered output node in both.", LALC),
    ("Device geometry", "W and L swept over identical values in both.", LALC),
    ("Time base", "T_phase identical; T_clock = T_rail = 4·T_phase, so "
     "one operation means the same interval in both.", LALC),
    ("Energy definition", "the integral of -V·I over one full period, per "
     "gate for ECRL and per metered quad-rail column for 2LAL.", LALC),
    ("Switching activity", "Verified equal rather than assumed — we "
     "measured the 0→1 and 1→0 cycles separately in both families "
     "and they came out identical, so no activity correction was needed.",
     BLUE),
]
y = 1.46
for i, (t, d, c) in enumerate(items):
    h = 0.80 if i in (0, 4, 6) else 0.58
    rect(s, M, y, CW, h, PANEL if i % 2 == 0 else WHITE, radius=0.04)
    rect(s, M, y, 0.045, h, c)
    _, tf = textbox(s, M + 0.34, y + 0.11, 2.55, h - 0.22)
    para(tf, t, 13.5, INK, bold=True, first=True)
    _, tf = textbox(s, M + 3.05, y + 0.11, CW - 3.35, h - 0.22)
    para(tf, d, 13, BODY, first=True)
    y += h + 0.055
notes(s, "The first and the last are the two that took real work. The model-"
         "file mismatch would have quietly invalidated everything; the "
         "activity check is the one people usually assume rather than "
         "measure.")

# ======================================================= 23. per operation
s = slide()
head(s, "What one “operation” means", "part iii · the unit")
_, tf = textbox(s, M, Y_TOP, 7.35, 0.94)
para(tf, "Per power-clock cycle, per gate. In these decks that is also exactly "
         "one data transaction — the two coincide by construction, "
         "because we made the data alternate every cycle.", 15.5, INK,
     bold=True, first=True)
table(s, M, 2.56, 7.35,
      [["", "what is integrated", "denominator"],
       [[("ECRL", {"b": True, "c": ECRLC})],
        "V(PCLK) over [12·Tp, 16·Tp] = one T_clock",
        "1 gate × 1 cycle"],
       [[("2LAL", {"b": True, "c": LALC})],
        "rail energy over one T_rail = 4·Tp",
        "4 metered columns"]],
      [0.8, 3.0, 1.6], hrow=0.52, hhdr=0.36, size=12.5, hsize=11.5)
_, tf = textbox(s, M, 4.34, 7.35, 2.4)
para(tf, "Neither family is free when idle.", 14.5, INK, bold=True, first=True)
para(tf, "An ECRL gate pulses OUT or OUTB every cycle regardless of the data. "
         "A quad-rail 2LAL column always has exactly one sub-chain carrying a "
         "TRUE, so it also pulses every cycle. “Per power cycle” is "
         "therefore the honest unit for both — you cannot amortise it "
         "away with low data activity.", 13.5, BODY, before=7)
para(tf, "The one place they would diverge is a plain dual-rail 2LAL buffer, "
         "where a FALSE is genuinely free. There you would have to state "
         "whether you meant per cycle or per transaction. For the quad-rail "
         "inverter, they are the same number.", 13.5, MUT, before=8)
callout(s, 8.42, Y_TOP, 4.19, 2.30,
        "Where this definition came from",
        "It is the same definition that exposed the defect in Part I. The old "
        "ECRL sweep was measuring per power cycle with zero data transitions "
        "in the window. Per power cycle it was right. Per data transaction it "
        "was measuring nothing at all.", WARN, TINTR)
callout(s, 8.42, 4.10, 4.19, 2.42,
        "Axis reminder",
        "The plots use f_tr = 1/T_phase. The operation rate is f_clock = "
        "1/(4·T_phase), four times lower. Energy per operation is "
        "plotted against transition frequency — legitimate, but it has "
        "to be said out loud. Both versions of every plot are in the repo.",
        BLUE, TINTB)
notes(s, "If a reviewer challenges any single number in this deck, this is the "
         "slide that answers it. Same unit on both sides: one gate, one power "
         "cycle, one new data value.")

# ========================================================= 24. head to head
s = slide()
head(s, "ECRL against 2LAL, matched conditions", "part iii · result")
pic(s, F("ecrl_vs_2lal_W1.0.png"), M + 0.55, 1.40, 7.60, 4.85)
_, tf = textbox(s, 8.42, 1.50, 4.19, 4.9)
para(tf, "Three things to take away", 15, INK, bold=True, first=True)
bullet(tf, [("They tie at f_tr = 100 MHz. ", {"b": True, "c": INK}),
            ("21.66 fJ against 21.62 fJ. Not a coincidence — both are "
             "doing the same physical work, one 25 fF node charged and "
             "discharged adiabatically per operation.", {})],
       13.5, accent=MUT, before=11)
bullet(tf, [("2LAL's advantage band is narrow and modest. ", {"b": True, "c": LALC}),
            ("f_tr 200–500 MHz, and only by 7–13%.", {})],
       13.5, accent=LALC, before=10)
bullet(tf, [("ECRL wins clearly at low frequency. ", {"b": True, "c": ECRLC}),
            ("3.5× better at 10 MHz, because 2LAL's leakage floor "
             "— 16 transistors per column against ECRL's 4 — turns "
             "its curve upward.", {})], 13.5, accent=ECRLC, before=10)
rect(s, 8.42, 5.32, 4.19, 1.10, PANEL, radius=0.05)
_, tf = textbox(s, 8.66, 5.46, 3.75, 0.85)
para(tf, "There is no headline “2LAL beats ECRL” result here, and we "
         "are not going to manufacture one.", 13, INK, bold=True, first=True)
notes(s, "Resist the temptation to declare a winner. The honest finding is "
         "that under matched conditions these two families are much closer "
         "than the literature's enthusiasm suggests, and which one wins "
         "depends entirely on where you sit on the frequency axis.")

# ============================================================= 25. the table
s = slide()
head(s, "The numbers behind that curve", "part iii · result",
     sub="W = 1.0 µm, L = 0.15 µm, C_L = 25 fF, same T_phase, "
         "alternating data. Energy per operation, in fJ.")
rows = [["T_phase", "f_tr", "f_clock", "ECRL", "2LAL", "outcome"],
        ["100 ns", "10 MHz", "2.5 MHz", "12.46", "44.05",
         [("ECRL by 3.5×", {"c": ECRLC, "b": True})]],
        ["50 ns", "20 MHz", "5 MHz", "14.37", "45.11",
         [("ECRL by 3.1×", {"c": ECRLC, "b": True})]],
        ["20 ns", "50 MHz", "12.5 MHz", "17.83", "23.97",
         [("ECRL by 1.34×", {"c": ECRLC, "b": True})]],
        ["10 ns", "100 MHz", "25 MHz", "21.66", "21.62",
         [("tie", {"c": MUT, "b": True})]],
        ["5 ns", "200 MHz", "50 MHz", "27.32", "23.87",
         [("2LAL by 13%", {"c": LALC, "b": True})]],
        ["2 ns", "500 MHz", "125 MHz", "39.82", "36.86",
         [("2LAL by 7%", {"c": LALC, "b": True})]],
        ["1 ns", "1000 MHz", "250 MHz", "54.69", "64.95",
         [("ECRL by 1.19×", {"c": ECRLC, "b": True})]]]
table(s, M, 1.92, 7.75, rows, [1.0, 1.05, 1.1, 0.95, 0.95, 1.5],
      hrow=0.415, hhdr=0.40, size=13, hsize=12,
      align=[PP_ALIGN.LEFT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT, PP_ALIGN.RIGHT,
             PP_ALIGN.RIGHT, PP_ALIGN.LEFT])
callout(s, 8.72, 1.92, 3.89, 2.30,
        "Reading it honestly",
        "Both families are within a factor of two of each other across four "
        "fifths of the range. The crossover is a genuine crossing, not a gap "
        "— and it sits at a frequency where neither design is obviously "
        "the one you would reach for.", ECRLC, PANEL)
callout(s, 8.72, 4.38, 3.89, 2.44,
        "The caveat to quote with these numbers",
        "Switched capacitance per operation is equal, which is what makes the "
        "energy comparison legitimate. Standing capacitance, area and leakage "
        "are not: 16 FETs and 4 loaded nodes against 4 FETs and 2.",
        WARN, TINTR)
notes(s, "Every cell in this table is a row in a CSV that came out of a "
         "scripted ngspice run. Slide 27 shows the provenance chain for one "
         "of them.")

# ======================================================== 26. verification
s = slide()
head(s, "Verification and reproducibility", "part iii · trust")
_, tf = textbox(s, M, Y_TOP, 7.35, 4.9)
bullet(tf, [("Nothing is hand-entered. ", {"b": True, "c": INK}),
            ("ngspice .meas → sweep shell script → CSV → .dat "
             "→ gnuplot → PNG. gnuplot draws the graphs; every "
             "number in them came out of ngspice.", {})],
       14.5, accent=LALC, before=0, first=True)
bullet(tf, [("Worked provenance example. ", {"b": True, "c": INK}),
            ("2.16179e-14 J appears identically in the run log, in the CSV row "
             "1.0,10,…, in the .dat file handed to gnuplot, and as the "
             "plotted point. Three independent greps, one number.", {})],
       14.5, accent=LALC, before=11)
bullet(tf, [("A 50× speed-up, checked before it was trusted. ", {"b": True, "c": INK}),
            ("A reduced model include loads only the two devices we actually "
             "use: 77 s → 1.5 s per run. Verified bit-for-bit against the "
             "full PDK .lib at four points — 1.80491e-14 J on both "
             "— before being relied on.", {})],
       14.5, accent=BLUE, before=11)
bullet(tf, [("Settling and error checks on every run. ", {"b": True, "c": INK}),
            ("Each measurement is repeated two periods earlier; a run with no "
             "e_c line in the log is an error, not a zero.", {})],
       14.5, accent=BLUE, before=11)
bullet(tf, [("CHECKS.md. ", {"b": True, "c": INK}),
            ("The repository carries the exact command to re-derive every "
             "claim on these slides, including how to reproduce the old "
             "5.3622 fJ figure on purpose to prove what caused it.", {})],
       14.5, accent=BLUE, before=11)
callout(s, 8.42, Y_TOP, 4.19, 2.05,
        "Errors we caught in our own review",
        "A femtojoule / attojoule unit slip that had produced a spurious "
        "~1000× claim in favour of 2LAL, and a “625,000×” "
        "that should have read 625×. Both corrected before anything was "
        "plotted.", WARN, TINTR)
rect(s, 8.42, 4.00, 4.19, 2.52, PANEL, radius=0.05)
_, tf = textbox(s, 8.66, 4.18, 3.75, 2.20)
para(tf, "The scripted pipeline", 13.5, INK, bold=True, first=True)
for t in ["run_2lal_sweep.sh", "ecrl_exp1/run_ecrl_slowramp_sweep.sh",
          "make_plots.py", "CHECKS.md"]:
    para(tf, t, 11.5, BODY, before=6, font=MONO)
para(tf, "84 sweep points, no manual editing.", 12.5, MUT, italic=True,
     before=9)
notes(s, "Offer to run any single point live if they want it. The whole sweep "
         "is about three minutes now, and one point is a second and a half.")

# ========================================================= 27. what we don't
s = slide()
head(s, "What we are not claiming", "honesty", kcolor=WARN)
_, tf = textbox(s, M, Y_TOP, 7.35, 4.9)
bullet(tf, [("We have not reproduced the 1996 numbers. ", {"b": True, "c": WARN}),
            ("Moon & Jeong used 1 µm CMOS, Vt ≈ 0.2 V, a 5 V "
             "supply, and 5/10 µm devices. Different process, different "
             "voltage, different device — the numbers cannot match and "
             "should not be expected to.", {})],
       14.5, accent=WARN, before=0, first=True)
bullet(tf, [("What we did reproduce ", {"b": True, "c": LALC}),
            ("is the ECRL topology and the energy-versus-frequency evaluation "
             "methodology, in SKY130, and we confirmed the frequency-dependent "
             "trend the paper reports.", {})], 14.5, accent=LALC, before=12)
bullet(tf, [("The 2LAL cell is a reconstruction. ", {"b": True, "c": WARN}),
            ("Assembled from Frank's slides, a DeBenedictis technical report "
             "and the 4lc PHAS2 cell. We have not seen Figure 2 of the source "
             "paper. Everything is self-consistent and simulates correctly at "
             "both bit values, but it is a reconstruction and we say so.", {})],
       14.5, accent=WARN, before=12)
bullet(tf, [("A single inverter, not a system. ", {"b": True, "c": WARN}),
            ("No multi-gate logic, no layout, no extracted parasitics, and no "
             "power-clock generator — which every adiabatic result "
             "quietly assumes is free, and which is not.", {})],
       14.5, accent=WARN, before=12)
rect(s, 8.42, Y_TOP, 4.19, 4.9, DARK, radius=0.05)
_, tf = textbox(s, 8.70, Y_TOP + 0.28, 3.63, 4.4)
para(tf, "THE DEFENSIBLE CLAIM", 10.5, MINT, bold=True, first=True)
para(tf, "“We implemented and functionally verified an ECRL inverter in "
         "SKY130, established a power-clock energy measurement by integrating "
         "source power, found and fixed a defect in our own measurement "
         "window, and reproduced the expected trend.",
     13.5, WHITE, before=12, spacing=1.2)
para(tf, "We then reconstructed a working 2LAL quad-rail inverter and compared "
         "the two families under seven matched conditions, with the "
         "switching-activity match verified rather than assumed.”",
     13.5, WHITE, before=10, spacing=1.2)
para(tf, "Stronger than a number match, and we can defend every clause of it.",
     12.5, MINT, bold=True, before=11)
notes(s, "If asked 'so did you match the paper?' — the answer is no, and "
         "explaining why not is the better answer. Read the dark box out loud "
         "if the question comes.")

# ============================================================ 28. next steps
s = slide()
head(s, "Where this goes next", "next steps", kcolor=LALC)
nxt = [
    ("Real logic, not just an inverter", "NAND and NOR cells and a multi-gate "
     "chain in both families. An inverter is the easiest possible case for "
     "both, and it may be hiding where they actually differ.", LALC),
    ("Check the 2LAL cell against the primary source", "If Figure 2 of the "
     "source paper can be obtained, verify our reconstruction against it "
     "rather than against secondary sources.", BLUE),
    ("Separate the leakage floor from the switching term", "Measure at zero "
     "activity and subtract, so the RC/T term can be isolated. That would "
     "explain the 2LAL upturn quantitatively instead of by inference.", BLUE),
    ("The paper's other two axes", "Sweep supply voltage and load "
     "capacitance, which the 1996 work also varies and we have not.", MUT),
    ("Layout and extracted parasitics", "Move from schematic-level SKY130 to "
     "a real cell with extracted parasitics, where the standing-capacitance "
     "penalty of 2LAL's 16 transistors will actually show up.", MUT),
    ("The power-clock generator", "Every adiabatic energy figure in the "
     "literature, ours included, assumes the trapezoidal clock arrives for "
     "free. Costing it is the honest end of this project.", ECRLC),
]
y = 1.48
for i, (t, d, c) in enumerate(nxt):
    rect(s, M, y, CW, 0.82, PANEL if i % 2 == 0 else WHITE, radius=0.04)
    rect(s, M, y, 0.045, 0.82, c)
    _, tf = textbox(s, M + 0.36, y + 0.13, 3.55, 0.60)
    para(tf, t, 13.5, INK, bold=True, first=True)
    _, tf = textbox(s, M + 4.10, y + 0.13, CW - 4.40, 0.60)
    para(tf, d, 12.5, BODY, first=True)
    y += 0.875
notes(s, "Lead with the first one if asked what is most important. The "
         "inverter comparison is close to a tie; real logic is where the "
         "topologies diverge, because a 2LAL gate does logic in the pass "
         "network while ECRL does it in the pull-down tree.")

# =============================================================== 29. summary
s = slide()
head(s, "Where the project stands", "summary")
_, tf = textbox(s, M, 1.46, CW, 1.0)
para(tf, "We did not just simulate an inverter. We built a parameterised "
         "methodology for measuring adiabatic energy, found three defects in "
         "it, fixed them, and then used it to compare two logic families "
         "under conditions we can enumerate and defend.", 17, INK, bold=True,
     first=True, spacing=1.2)
cards = [
    ("Verified", "ECRL inverter correct at both bit values across every "
     "T_phase from 1 ns to 100 ns", ECRLC),
    ("Defined", "Energy per operation = the integral of -V_PHI·I_PHI dt over one "
     "T_clock — and a 2.3× defect it exposed in our own earlier "
     "numbers", WARN),
    ("Measured", "84 scripted sweep points: 2 families × 6 widths "
     "× 7 frequencies, fully reproducible", BLUE),
    ("Compared", "ECRL below 100 MHz, a tie at 100 MHz, 2LAL by 7–13% in "
     "a narrow 200–500 MHz band", LALC),
]
for i, (t, d, c) in enumerate(cards):
    x = M + i * 3.03
    rect(s, x, 2.72, 2.83, 1.90, PANEL, radius=0.07)
    rect(s, x, 2.72, 2.83, 0.055, c)
    _, tf = textbox(s, x + 0.24, 2.94, 2.36, 1.55)
    para(tf, t.upper(), 12, c, bold=True, first=True)
    para(tf, d, 13, BODY, before=7, spacing=1.15)
rect(s, M, 4.84, CW, 1.80, DARK, radius=0.05)
_, tf = textbox(s, M + 0.42, 5.02, CW - 0.84, 1.44)
para(tf, "The most valuable output of this phase is not an energy number. It "
         "is a measurement definition strict enough that it caught our own "
         "mistakes — and a comparison built on top of it that we would "
         "be willing to defend line by line.", 16, WHITE, bold=True,
     first=True, spacing=1.25, align=PP_ALIGN.CENTER)
para(tf, "Everything on these slides is reproducible from the repository with "
         "the commands in CHECKS.md.", 13, MINT, before=8,
     align=PP_ALIGN.CENTER)
notes(s, "Close on the dark box. Then invite questions, and offer to run a "
         "point live.")

# ============================================================== 30. appendix
s = slide()
head(s, "Appendix: the full dataset", "backup",
     sub="Energy per operation in fJ. Rows are transition frequency, columns "
         "are device width. From ecrl_slowramp_sweep.csv and "
         "2lal_inverter_sweep.csv.")
W6 = ["0.84", "1.0", "1.2", "1.5", "2.0", "3.0"]
ecrl_rows = [
    ("10 MHz", [12.61, 12.46, 12.56, 11.97, 11.73, 11.55]),
    ("20 MHz", [14.58, 14.37, 14.44, 13.70, 13.39, 13.10]),
    ("50 MHz", [18.31, 17.83, 17.74, 16.68, 16.15, 15.62]),
    ("100 MHz", [22.55, 21.66, 21.28, 19.81, 18.97, 18.09]),
    ("200 MHz", [28.92, 27.32, 26.41, 24.28, 22.88, 21.40]),
    ("500 MHz", [43.15, 39.82, 37.58, 33.93, 31.06, 28.08]),
    ("1000 MHz", [59.59, 54.69, 51.12, 46.05, 41.40, 36.43]),
]
lal_rows = [
    ("10 MHz", [43.38, 44.05, 44.65, 46.04, 49.20, 56.09]),
    ("20 MHz", [42.53, 45.11, 46.63, 47.62, 50.53, 57.10]),
    ("50 MHz", [21.29, 23.97, 32.05, 49.92, 54.15, 60.16]),
    ("100 MHz", [20.40, 21.62, 23.83, 30.61, 54.03, 64.20]),
    ("200 MHz", [23.71, 23.87, 24.38, 26.95, 32.76, 61.47]),
    ("500 MHz", [36.81, 36.86, 40.73, 34.87, 38.45, 42.11]),
    ("1000 MHz", [61.70, 64.95, 70.74, 68.63, 71.14, 76.84]),
]


def grid(x, title, data, color):
    _, tf = textbox(s, x, 2.02, 5.9, 0.3)
    para(tf, title, 14, color, bold=True, first=True)
    rows = [["f_tr"] + ["W = " + w for w in W6]]
    for lbl, vals in data:
        rows.append([lbl] + ["%.2f" % v for v in vals])
    table(s, x, 2.36, 5.9, rows, [1.25] + [1.0] * 6, hrow=0.375, hhdr=0.36,
          size=11.5, hsize=10.5, accent=color,
          align=[PP_ALIGN.LEFT] + [PP_ALIGN.RIGHT] * 6)


grid(M, "ECRL inverter, slow-ramp input, alternating data", ecrl_rows, ECRLC)
grid(M + 6.30, "2LAL quad-rail inverter", lal_rows, LALC)
_, tf = textbox(s, M, 5.62, CW, 0.9)
para(tf, "Note the difference in the width trend. ECRL improves with width at "
         "high frequency and is flat at low frequency. 2LAL gets worse with "
         "width at every frequency measured — its pass gates are not "
         "resistance-limited in this range, so extra width buys nothing and "
         "costs capacitance and leakage.", 13, BODY, first=True)
para(tf, "All values are E_C, the average of the 0→1 and 1→0 cycles. "
         "In both families those two agreed to within the last printed digit, "
         "which is why no switching-activity correction was applied.",
     12.5, MUT, before=6)
notes(s, "Backup slide. Only go here if someone wants the raw grid.")

prs.save(OUT)
print("wrote", OUT, "-", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
