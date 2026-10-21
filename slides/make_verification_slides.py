#!/usr/bin/env python3
"""
Build a short, plain-language deck on how the energy numbers were verified.

    python3 make_verification_slides.py          -> Verification_Explained.pptx
    python3 make_verification_slides.py --preview -> also preview/slide-N.png

Every slide is described once, as a list of boxes; the same description is
written to the .pptx (python-pptx) and drawn to a PNG preview (Pillow, with
Liberation Sans, which has the same metrics as Arial).  The preview also
reports any text that would not fit its box.

Every number on the slides comes from the repository:
  ../verification/{waveform,mutation,calibration,lc_scaling}_report.txt,
  ../2lal/2lal_inverter_sweep.csv, ../ecrl/ecrl_slowramp_sweep.csv,
  ../2lal/superseded/2lal_inverter_sweep_openchain.csv, ../CHECKS.md.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Verification_Explained.pptx")
REPO = os.path.dirname(HERE)
SW, SH = 13.333, 7.5                      # 16:9, inches

# ---------------------------------------------------------------- palette
INK   = "17212B"      # dark background / headings
BODY  = "3D4752"      # body text
MUTED = "6B7682"      # captions
GOOD  = "1A7F5A"      # pass / verified
GOODT = "E8F3EE"      # light tint of GOOD
BAD   = "B23A2E"      # bug
BADT  = "F8E9E7"
CARD  = "F2F4F6"
WHITE = "FFFFFF"
FONT  = "Arial"
M     = 0.6           # side margin, inches

# ---------------------------------------------------------------- slide model
def T(x, y, w, h, runs, size=16, color=BODY, bold=False, align="l",
      anchor="t", font=FONT, spacing=1.0):
    """text box; runs = str or list of paragraphs, each a str or list of
    (text, {bold, color, size}) runs"""
    return dict(kind="text", x=x, y=y, w=w, h=h, runs=runs, size=size,
                color=color, bold=bold, align=align, anchor=anchor,
                font=font, spacing=spacing)

def R(x, y, w, h, fill, rounded=True, name=""):
    return dict(kind="rect", x=x, y=y, w=w, h=h, fill=fill, rounded=rounded, name=name)

def C(x, y, d, fill):
    return dict(kind="circle", x=x, y=y, w=d, h=d, fill=fill)

def I(path, x, y, w=None, h=None):
    return dict(kind="image", path=os.path.join(REPO, path), x=x, y=y, w=w, h=h)

def badge(n, x=M, y=0.55, fill=GOOD):
    """the deck's motif: a numbered circle beside each check's title"""
    return [C(x, y, 0.62, fill), T(x, y, 0.62, 0.62, str(n), size=22, bold=True,
            color=WHITE, align="c", anchor="m")]

def title(text, with_badge=True):
    x = M + 0.85 if with_badge else M
    return T(x, 0.5, SW - x - M, 0.75, text, size=30, bold=True, color=INK, anchor="m")

slides = []   # (background, [elements], notes)

# 1 ---------------------------------------------------------------- title
slides.append((INK, [
    T(M, 2.2, 11.5, 1.1, "Can we trust the energy numbers?", size=44, bold=True,
      color=WHITE),
    T(M, 3.35, 11.5, 0.6, "How the ECRL and 2LAL inverter results were checked",
      size=22, color="C9D3DC"),
    T(M, 5.9, 11.5, 0.4, "SKY130 tt  ·  ngspice  ·  1.8 V  ·  25 fF load  ·  Adiabatic_sweep repository",
      size=14, color="8C99A6"),
], "We simulate two adiabatic logic families and report energy per operation. "
   "This deck explains, in plain terms, why we believe those energy numbers."))

# 2 ---------------------------------------------------------------- overview
qs = [("1", "Is the logic right?", "Every point is checked before its energy is kept"),
      ("2", "Is the energy meter right?", "It gives the textbook answer on circuits we can solve by hand"),
      ("3", "Does it follow the physics?", "Energy changes with speed and load the way theory says"),
      ("4", "Does it match published work?", "Same operating point, close to the published number")]
els = [T(M, 0.5, SW - 2 * M, 0.75, "Four questions, four checks", size=30, bold=True,
         color=INK, anchor="m")]
cw, gap, cy, ch = 2.83, 0.24, 1.75, 3.6
for i, (n, q, a) in enumerate(qs):
    x = M + i * (cw + gap)
    els += [R(x, cy, cw, ch, CARD),
            C(x + 0.3, cy + 0.35, 0.62, GOOD),
            T(x + 0.3, cy + 0.35, 0.62, 0.62, n, size=22, bold=True, color=WHITE,
              align="c", anchor="m"),
            T(x + 0.3, cy + 1.25, cw - 0.6, 1.0, q, size=20, bold=True, color=INK),
            T(x + 0.3, cy + 2.5, cw - 0.6, 1.0, a, size=16, color=BODY)]
els.append(T(M, 5.75, SW - 2 * M, 0.5,
             "All four pass. One script reruns everything in about four minutes.",
             size=16, color=MUTED))
slides.append((WHITE, els,
    "If any one of these fails, the energy numbers mean nothing. We check all four, "
    "and the checks run automatically every time."))

# 3 ---------------------------------------------------------------- logic
els = badge(1) + [title("Is the logic right?"),
    I("verification/figures/2lal_inverter_stage_T10.png", M, 1.55, w=7.0),
    T(M, 5.35, 7.0, 0.7, "One 2LAL stage at 10 ns: the output (bottom) is the input "
      "(middle) inverted, one phase later. Red digits are read from the waveform.",
      size=12, color=MUTED)]
pts = [("Checked at every point", "An ECRL point is kept only if both outputs reach the rails. "
        "A 2LAL point needs all 96 of its checks to pass."),
       ("Checked a second way", "A separate program reads the raw waveforms and agrees: "
        "every stage inverts, 154 of 154 times."),
       ("The checks can fail", "We broke the circuit on purpose in 6 ways. "
        "Every break was caught.")]
y = 1.6
for h, b in pts:
    els += [T(8.1, y, 4.6, 0.4, h, size=18, bold=True, color=INK),
            T(8.1, y + 0.42, 4.6, 1.0, b, size=15, color=BODY)]
    y += 1.6
slides.append((WHITE, els,
    "Energy from a circuit that computes the wrong answer is worthless, so logic is "
    "checked first. One broken circuit, a stage that does not invert, uses exactly the "
    "same energy as the correct one (6.29 fJ). Only the logic checks can catch that."))

# 4 ---------------------------------------------------------------- meter
stats = [("+0.3 %", "Static CMOS",
          "Energy per fF of load must be VDD² = 3.240 fJ/fF. We measure 3.250."),
         ("0.01 %", "Resistor + capacitor",
          "A case with an exact answer, driven by our clock ramp. We match it."),
         ("0.06 %", "Smaller time steps",
          "4× finer steps and tighter tolerance move no result by more than this.")]
els = badge(2) + [title("Is the energy meter right?")]
cw, gap, cy = 3.85, 0.27, 1.75
for i, (big, h, b) in enumerate(stats):
    x = M + i * (cw + gap)
    els += [R(x, cy, cw, 3.9, CARD),
            T(x + 0.35, cy + 0.35, cw - 0.7, 1.1, big, size=48, bold=True, color=GOOD),
            T(x + 0.35, cy + 1.55, cw - 0.7, 0.45, h, size=20, bold=True, color=INK),
            T(x + 0.35, cy + 2.1, cw - 0.7, 1.6, b, size=16, color=BODY)]
els.append(T(M, 6.0, SW - 2 * M, 0.8,
    "The numbers are the error of the meter against the known answer. "
    "All three are far smaller than any difference we report.", size=15, color=MUTED))
slides.append((WHITE, els,
    "Before trusting the meter on adiabatic circuits, we point it at circuits whose "
    "answer we already know. Static CMOS must give VDD squared per femtofarad, whatever "
    "its parasitics. A resistor and capacitor on our clock ramp has an exact formula."))

# 5 ---------------------------------------------------------------- physics
els = badge(3) + [title("Does it follow the physics?"),
    I("plots/2lal_energy_vs_cap.png", M, 1.5, w=6.5),
    T(M, 6.05, 6.5, 0.5, "2LAL energy vs load. Dashed: C and C² slopes.",
      size=12, color=MUTED)]
pts = [("Slower clock, less energy", "2LAL energy falls almost as 1/T. Its fixed "
        "leftover loss is 0.11 fJ: essentially zero, as a fully adiabatic circuit should be."),
       ("ECRL stops improving", "It levels off near 15 fJ, the threshold-voltage loss "
        "the theory predicts for ECRL."),
       ("Bigger load, steeper rise", "2LAL energy grows as C². The resistance this implies, "
        "4.54 kΩ, matches the transmission gate measured on its own, 4.92 kΩ.")]
y = 1.55
for h, b in pts:
    els += [T(7.55, y, 5.2, 0.4, h, size=18, bold=True, color=INK),
            T(7.55, y + 0.42, 5.2, 1.1, b, size=15, color=BODY)]
    y += 1.6
slides.append((WHITE, els,
    "Adiabatic theory makes specific predictions: energy proportional to 1 over T for "
    "2LAL, a fixed floor for ECRL, and C squared growth with load. All three show up, "
    "with numbers that agree with separate measurements of the transistors."))

# 6 ---------------------------------------------------------------- published
els = badge(4) + [title("Does it match published work?")]
for i, (big, h, b, fill, col) in enumerate([
        ("6.9 aJ", "Published", "Frank et al., ICRC 2020\nSandia 180 nm process", CARD, INK),
        ("8.1 aJ", "Our circuit", "Same operating point\nSKY130 process", GOODT, GOOD)]):
    x = M + i * 4.2
    els += [R(x, 1.75, 3.9, 3.3, fill),
            T(x + 0.4, 2.0, 3.1, 0.45, h, size=18, bold=True, color=MUTED),
            T(x + 0.4, 2.5, 3.1, 1.2, big, size=54, bold=True, color=col),
            T(x + 0.4, 3.8, 3.1, 1.0, b, size=15, color=BODY)]
els += [T(9.15, 1.9, 3.6, 0.9, "1.17×", size=54, bold=True, color=GOOD),
        T(9.15, 2.9, 3.6, 2.2, "Energy per transistor per clock cycle, for a 2LAL shift "
          "register at 1 MHz with a 10 fF load. Different process, same order and close.",
          size=15, color=BODY),
        T(M, 5.5, SW - 2 * M, 0.9,
          "Our ring at their settings (W = 0.48 µm, L = 0.18 µm) also passes all 96 logic "
          "checks. We found no published ECRL or 2LAL result in SKY130 to compare against directly.",
          size=15, color=MUTED)]
slides.append((WHITE, els,
    "This is the only published 2LAL energy we found at a stated operating point. "
    "Matching it to within 17 percent, in a different process, is strong evidence our "
    "2LAL circuit and meter behave like the real thing."))

# 7 ---------------------------------------------------------------- bugs
els = [T(M, 0.5, SW - 2 * M, 0.75, "What the checks caught", size=30, bold=True,
         color=INK, anchor="m")]
bugs = [("The 2LAL chain had a loose end",
         "The last stage had nothing after it to reset it. It disturbed the stages we "
         "were measuring.",
         "44.05 fJ", "0.93 fJ", "at 100 ns: 47× too high",
         "Fix: close the chain into an 8-stage ring."),
        ("ECRL measured the wrong cycle",
         "The measured clock cycle had no data change in it, so it missed the loss "
         "that happens when the data flips.",
         "5.36 fJ", "12.46 fJ", "at 100 ns: 2.3× too low",
         "Fix: change the data every cycle, measure that cycle.")]
cw = 5.9
for i, (h, b, before, after, ratio, fix) in enumerate(bugs):
    x = M + i * (cw + 0.33)
    els += [R(x, 1.6, cw, 4.45, CARD),
            T(x + 0.35, 1.85, cw - 0.7, 0.5, h, size=20, bold=True, color=INK),
            T(x + 0.35, 2.4, cw - 0.7, 1.0, b, size=15, color=BODY),
            T(x + 0.35, 3.5, 1.4, 0.3, "Before", size=12, bold=True, color=BAD),
            T(x + 0.35, 3.8, 2.4, 0.7, before, size=32, bold=True, color=BAD),
            T(x + 2.9, 3.5, 1.4, 0.3, "After", size=12, bold=True, color=GOOD),
            T(x + 2.9, 3.8, 2.6, 0.7, after, size=32, bold=True, color=GOOD),
            T(x + 0.35, 4.55, cw - 0.7, 0.4, ratio, size=15, color=MUTED),
            T(x + 0.35, 5.25, cw - 0.7, 0.9, fix, size=16, bold=True, color=INK)]
slides.append((WHITE, els,
    "Both bugs changed our conclusions. The 2LAL one made the two families look tied; "
    "the ECRL one made ECRL look better than it is. Each was found by a check, and each "
    "check now runs on every result."))

# 8 ---------------------------------------------------------------- close
res = [("Logic checks", "pass at every point"),
       ("Broken-circuit test", "6 of 6 caught"),
       ("Meter and physics", "28 of 28 pass"),
       ("Length and load sweeps", "11 of 11 pass")]
els = [T(M, 0.9, 11.5, 0.9, "Rerun it yourself", size=40, bold=True, color=WHITE),
       R(M, 2.05, 7.2, 0.75, "26323F"),
       T(M + 0.3, 2.05, 6.8, 0.75, "verification/verify_all.sh      (about 4 minutes)",
         size=18, color="E6EDF3", font="Courier New", anchor="m")]
for i, (h, b) in enumerate(res):
    x = M + i * 3.03
    els += [T(x, 3.35, 2.85, 0.45, h, size=16, color="9FB0BF"),
            T(x, 3.8, 2.85, 0.6, b, size=22, bold=True, color="7FD1AE")]
els.append(T(M, 5.4, 11.8, 1.0, "Limits: simulation only, one process corner (tt, 27 °C), "
             "inverters only, ideal clock source. The checks show the numbers are right "
             "for this setup, not that a chip would behave the same.", size=15, color="B8C4CF"))
slides.append((INK, els,
    "Anyone can repeat every check with one command. The last line is the honest scope: "
    "this verifies the simulation, not silicon."))


# ================================================================ pptx writer
def rgb(h): return RGBColor.from_string(h)

def add_text(slide, e):
    tb = slide.shapes.add_textbox(Inches(e["x"]), Inches(e["y"]), Inches(e["w"]), Inches(e["h"]))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE}[e["anchor"]]
    paras = e["runs"] if isinstance(e["runs"], list) else e["runs"].split("\n")
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER}[e["align"]]
        p.line_spacing = e["spacing"]
        runs = para if isinstance(para, list) else [(para, {})]
        for text, o in runs:
            r = p.add_run(); r.text = text
            f = r.font; f.name = e["font"]; f.size = Pt(o.get("size", e["size"]))
            f.bold = o.get("bold", e["bold"]); f.color.rgb = rgb(o.get("color", e["color"]))

def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
    blank = prs.slide_layouts[6]
    for bg, els, notes in slides:
        s = prs.slides.add_slide(blank)
        s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(bg)
        for e in els:
            k = e["kind"]
            if k in ("rect", "circle"):
                shape = {"rect": MSO_SHAPE.ROUNDED_RECTANGLE if e.get("rounded") else MSO_SHAPE.RECTANGLE,
                         "circle": MSO_SHAPE.OVAL}[k]
                sh = s.shapes.add_shape(shape, Inches(e["x"]), Inches(e["y"]), Inches(e["w"]), Inches(e["h"]))
                sh.fill.solid(); sh.fill.fore_color.rgb = rgb(e["fill"]); sh.line.fill.background()
                sh.shadow.inherit = False
                if k == "rect" and e.get("rounded"):
                    sh.adjustments[0] = 0.06
            elif k == "image":
                w, h = image_size(e)
                s.shapes.add_picture(e["path"], Inches(e["x"]), Inches(e["y"]), Inches(w), Inches(h))
            else:
                add_text(s, e)
        s.notes_slide.notes_text_frame.text = notes
    prs.core_properties.title = "Can we trust the energy numbers?"
    prs.save(OUT)
    print("wrote", OUT, "-", len(slides), "slides")

def image_size(e):
    iw, ih = Image.open(e["path"]).size
    if e["w"] and not e["h"]: return e["w"], e["w"] * ih / iw
    if e["h"] and not e["w"]: return e["h"] * iw / ih, e["h"]
    return e["w"], e["h"]


# ================================================================ preview
DPI = 96
FONTS = {(False, "Arial"): "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         (True, "Arial"): "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
         (False, "Courier New"): "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
         (True, "Courier New"): "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"}

def font(bold, face, pt):
    return ImageFont.truetype(FONTS[(bool(bold), face)], max(1, round(pt * DPI / 72)))

def wrap(draw, text, f, width):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if draw.textlength(t, font=f) <= width or not cur:
                if draw.textlength(word, font=f) > width:
                    lines.append(("OVERFLOW-WORD", word))
                cur = t
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines

def preview(outdir):
    os.makedirs(outdir, exist_ok=True)
    problems = []
    for n, (bg, els, _) in enumerate(slides, 1):
        im = Image.new("RGB", (int(SW * DPI), int(SH * DPI)), "#" + bg)
        d = ImageDraw.Draw(im)
        px = lambda v: int(round(v * DPI))
        for e in els:
            k = e["kind"]
            if k != "image":
                box = [px(e["x"]), px(e["y"]), px(e["x"] + e["w"]), px(e["y"] + e["h"])]
            if k == "rect":
                d.rounded_rectangle(box, radius=px(0.06 * min(e["w"], e["h"])), fill="#" + e["fill"])
            elif k == "circle":
                d.ellipse(box, fill="#" + e["fill"])
            elif k == "image":
                w, h = image_size(e)
                pic = Image.open(e["path"]).convert("RGB").resize((px(w), px(h)))
                im.paste(pic, (px(e["x"]), px(e["y"])))
                if e["x"] + w > SW - 0.3 or e["y"] + h > SH - 0.3:
                    problems.append(f"slide {n}: image {os.path.basename(e['path'])} reaches the edge")
            else:
                paras = e["runs"] if isinstance(e["runs"], str) else "\n".join(
                    p if isinstance(p, str) else "".join(t for t, _ in p) for p in e["runs"])
                f = font(e["bold"], e["font"], e["size"])
                lines = wrap(d, paras, f, px(e["w"]))
                if any(isinstance(l, tuple) for l in lines):
                    problems.append(f"slide {n}: a single word is wider than its box: {paras[:40]!r}")
                    lines = [l if isinstance(l, str) else l[1] for l in lines]
                lh = e["size"] * 1.2 * e["spacing"] * DPI / 72
                th = lh * len(lines)
                if th > px(e["h"]) + 1:
                    problems.append(f"slide {n}: text overflows its box by "
                                    f"{(th - px(e['h'])) / DPI:.2f} in: {paras[:50]!r}")
                y0 = box[1] if e["anchor"] == "t" else box[1] + (px(e["h"]) - th) / 2
                for i, line in enumerate(lines):
                    x0 = box[0] if e["align"] == "l" else box[0] + (px(e["w"]) - d.textlength(line, font=f)) / 2
                    d.text((x0, y0 + i * lh), line, font=f, fill="#" + e["color"])
                if e["x"] < 0.45 or e["x"] + e["w"] > SW - 0.45:
                    problems.append(f"slide {n}: text box closer than 0.45 in to the edge: {paras[:40]!r}")
        im.save(os.path.join(outdir, f"slide-{n}.png"))
    print("preview in", outdir)
    for p in problems: print("  PROBLEM:", p)
    if not problems: print("  no overflow or edge problems found")


if __name__ == "__main__":
    build()
    if "--preview" in sys.argv:
        preview(os.path.join(HERE, "preview"))
