"""Build the typediff progress-update deck.

Run:  python build_deck.py [output.pptx]
To add slides: write another `slide_xxx(prs)` helper and append it to SLIDES.
"""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from lxml import etree

# ---- theme ----------------------------------------------------------------
NAVY = RGBColor(0x1B, 0x26, 0x3B)
ACCENT = RGBColor(0x1F, 0x6F, 0xB5)
GREY = RGBColor(0x6B, 0x72, 0x80)
LIGHT = RGBColor(0xE9, 0xEC, 0xF1)
MID = RGBColor(0xC9, 0xCF, 0xD8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"
SW, SH = 13.333, 7.5
MARGIN = 0.7
DEFAULT_OUT = Path(__file__).with_name("typediff_update.pptx")


# ---- helpers --------------------------------------------------------------
def new_prs():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
    return prs


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def text(slide, x, y, w, h, paras, size=18, color=NAVY, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=0, inset=0.05):
    """paras: str or list of str / (str, dict(size,color,bold)) items."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    fill_tf(tb.text_frame, paras, size, color, bold, align, anchor, space, inset)
    return tb


def fill_tf(tf, paras, size=18, color=NAVY, bold=False, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, space=0, inset=0.05):
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(inset)
    tf.margin_top = tf.margin_bottom = Inches(inset)
    if isinstance(paras, str):
        paras = [paras]
    for i, p in enumerate(paras):
        t, o = (p, {}) if isinstance(p, str) else p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        if space and i:
            para.space_before = Pt(space)
        r = para.add_run()
        r.text = t
        f = r.font
        f.name, f.size = FONT, Pt(o.get("size", size))
        f.bold = o.get("bold", bold)
        f.color.rgb = o.get("color", color)
        if o.get("link"):
            r.hyperlink.address = o["link"]


def rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, lw=1.0):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    return s


def title(slide, t, n):
    text(slide, MARGIN, 0.4, SW - 2 * MARGIN, 0.75, t, size=34, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    rect(slide, MARGIN + 0.05, 1.15, 0.9, 0.06, fill=ACCENT)
    footer(slide, n)


def footer(slide, n):
    rect(slide, MARGIN + 0.05, 7.0, SW - 2 * MARGIN - 0.05, 0.01, fill=MID)
    text(slide, MARGIN, 7.03, 4, 0.35, "typediff", size=12, color=GREY)
    text(slide, SW - MARGIN - 1, 7.03, 1, 0.35, str(n), size=12, color=GREY,
         align=PP_ALIGN.RIGHT)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def bullets(slide, x, y, w, h, items, size=18, space=8):
    """Accent-square bullets drawn as separate small shapes + text, one per item."""
    tb = text(slide, x + 0.3, y, w - 0.3, h, items, size=size, space=space)
    return tb


# ---- slides ---------------------------------------------------------------
def slide_title(prs):
    s = blank(prs)
    rect(s, 0, 0, 0.35, SH, fill=ACCENT)
    text(s, 1.2, 1.7, 10.5, 1.5, "typediff", size=80, bold=True, anchor=MSO_ANCHOR.BOTTOM)
    rect(s, 1.25, 3.3, 1.4, 0.07, fill=ACCENT)
    text(s, 1.2, 3.55, 11, 1.1,
         "Differential fuzzing of Python type checkers (ty vs mypy vs pyright)",
         size=28, color=NAVY)
    text(s, 1.2, 4.6, 8, 0.5, "Project progress update", size=20, color=ACCENT, bold=True)
    names = ["Anay Gupta", "Ajay Meena", "Aarsh Verma"]
    for i, n in enumerate(names):
        x = 1.25 + i * 3.4
        rect(s, x, 5.75, 0.04, 0.6, fill=MID)
        text(s, x + 0.15, 5.75, 3.1, 0.6, n, size=22, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "Hi everyone, we are Anay, Ajay and Aarsh. This is a progress update on typediff, "
             "our project on differential fuzzing of Python type checkers. "
             "We compare ty, mypy and pyright on the same programs and look for disagreements. "
             "Over the next few minutes we will cover the problem, why we picked it, our pipeline, "
             "and what we expect to deliver.")


def slide_problem(prs):
    s = blank(prs)
    title(s, "Problem statement", 2)
    text(s, MARGIN, 1.5, SW - 2 * MARGIN, 1.2,
         "Python type checkers should follow one typing specification, but they often "
         "disagree on the same program. We find which disagreements are real bugs.",
         size=24, color=NAVY)
    rows = [
        ("Problem", "mypy, pyright and the new Rust-based ty disagree on many programs, "
                    "and the spec itself is incomplete in places."),
        ("Why it is hard", "Most disagreements are intended design choices, known limits or "
                           "already-reported issues. Sorting them by hand does not scale."),
        ("Our approach", "Run the same programs through several checkers and real CPython, "
                         "auto-filter known differences, surface the few genuine bugs "
                         "(mainly ty, also mypy)."),
    ]
    y = 3.1
    for label, body in rows:
        rect(s, MARGIN + 0.05, y, 0.06, 1.0, fill=ACCENT)
        text(s, MARGIN + 0.3, y, 2.6, 1.0, label, size=22, bold=True, color=ACCENT,
             anchor=MSO_ANCHOR.MIDDLE)
        text(s, MARGIN + 3.0, y, SW - 2 * MARGIN - 3.0, 1.0, body, size=18,
             anchor=MSO_ANCHOR.MIDDLE)
        y += 1.2
    notes(s, "Python has a typing specification, and mypy, pyright and ty all claim to follow it. "
             "In practice they disagree on many programs, and the spec is vague in some places. "
             "Some of those disagreements are real bugs, but most are deliberate choices or known issues. "
             "Checking them by hand does not scale, so we built a pipeline that runs several checkers plus CPython, "
             "filters the known differences automatically, and leaves only the few that are worth reporting.")


def slide_motivation(prs):
    s = blank(prs)
    title(s, "Motivation: why type checkers, why ty", 3)
    cards = [
        ("Why type checkers matter", [
            "They run in editors, CI and AI-assisted coding",
            "A wrong answer silently misleads many developers",
            "Users expect them to follow the spec"]),
        ("Why ty", [
            "New Rust checker from Astral, now part of OpenAI [2]",
            "Reported 10x-60x faster than mypy and Pyright [1]",
            "Still beta, behind on spec coverage [3]",
            "pydantic-ai: 337 of 417 diagnostics were false positives [4]"]),
        ("Why differential testing", [
            "No hand-written oracle needed",
            "Other checkers and CPython act as oracles",
            "Young tool: bugs found now are cheap to fix and high impact"]),
    ]
    cw, gap = 3.75, 0.3
    x0 = (SW - (3 * cw + 2 * gap)) / 2
    for i, (head, items) in enumerate(cards):
        x = x0 + i * (cw + gap)
        rect(s, x, 1.45, cw, 4.85, fill=LIGHT)
        rect(s, x, 1.45, cw, 0.08, fill=ACCENT)
        text(s, x + 0.2, 1.65, cw - 0.4, 0.5, head, size=22, bold=True, color=ACCENT)
        text(s, x + 0.2, 2.65, cw - 0.4, 3.5,
             [("\u2022  " + t) for t in items], size=18, space=9)
    srcs = [
        ("[1] astral.sh/blog/ty", "https://astral.sh/blog/ty"),
        ("[2] pydevtools.com ty guide",
         "https://pydevtools.com/handbook/explanation/ty-complete-guide/"),
        ("[3] jlevy/simple-modern-uv type-checker comparison",
         "https://github.com/jlevy/simple-modern-uv/blob/main/docs/project/research/research-python-type-checkers.md"),
        ("[4] pydantic-ai issue #3970", "https://github.com/pydantic/pydantic-ai/issues/3970"),
    ]
    tb = s.shapes.add_textbox(Inches(MARGIN), Inches(6.45), Inches(SW - 2 * MARGIN), Inches(0.5))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0.05)
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = "Sources:  "
    r.font.name, r.font.size, r.font.color.rgb, r.font.bold = FONT, Pt(11), GREY, True
    for j, (label, url) in enumerate(srcs):
        r = p.add_run(); r.text = label + ("    " if j < len(srcs) - 1 else "")
        r.font.name, r.font.size, r.font.color.rgb = FONT, Pt(11), GREY
        r.hyperlink.address = url
    notes(s, "Type checkers sit in editors, in CI and increasingly in AI coding loops, so a wrong answer quietly affects a lot of people. "
             "ty is a new Rust checker from Astral, the Ruff and uv team, who are now part of OpenAI according to one 2026 guide. "
             "Astral reports it is roughly 10 to 60 times faster than mypy and Pyright, so adoption is growing fast. "
             "But it is still in beta, and a third-party comparison says it lags on spec coverage. "
             "One project, pydantic-ai, saw 337 of 417 diagnostics were false positives. "
             "Differential testing fits well because the other checkers and CPython act as oracles, so we need no hand-written expected answers.")


# -- architecture flowchart --
def fnode(slide, x, y, w, h, lines, kind):
    """kind: det (accent fill), llm (dashed outline), human (grey), pill."""
    shape = MSO_SHAPE.DIAMOND if kind == "dia" else MSO_SHAPE.ROUNDED_RECTANGLE
    fill, line, col = {
        "det": (ACCENT, None, WHITE),
        "llm": (WHITE, ACCENT, NAVY),
        "human": (LIGHT, GREY, NAVY),
        "dia": (LIGHT, GREY, NAVY),
        "pill": (WHITE, MID, GREY),
    }[kind]
    sh = rect(slide, x, y, w, h, fill=fill, line=line, shape=shape, lw=2.0)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = 0.12
    if kind == "llm":
        ln = sh.line._get_or_add_ln()
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "dash")
    paras = [(lines[0], {"bold": True, "size": 14})] + [(t, {"size": 14}) for t in lines[1:]]
    fill_tf(sh.text_frame, paras, size=14, color=col, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE, inset=0.04)
    return sh


def conn(slide, a, ai, b, bi, kind=MSO_CONNECTOR.STRAIGHT, color=NAVY, dash=False):
    c = slide.shapes.add_connector(kind, 0, 0, 0, 0)
    c.begin_connect(a, ai)
    c.end_connect(b, bi)
    c.line.color.rgb = color
    c.line.width = Pt(2)
    ln = c.line._get_or_add_ln()
    if dash:
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "dash")
    t = etree.SubElement(ln, qn("a:tailEnd")); t.set("type", "triangle")
    return c


def slide_arch(prs):
    s = blank(prs)
    title(s, "Pipeline: from programs to filed bugs", 4)
    W, GAP, X0 = 2.2, 0.45, 0.42
    cx = [X0 + i * (W + GAP) for i in range(5)]
    # row A
    A_Y, A_H = 1.45, 1.55
    inp = fnode(s, cx[0], A_Y, W, A_H, ["INPUT PROGRAMS", "27 hand-written seeds",
                "4,849 harvested", "LLM-generated"], "det")
    run = fnode(s, cx[1], A_Y, W, A_H, ["RUN", "mypy 2.4.0, ty 0.0.84, pyright",
                "CPython = ground truth"], "det")
    nor = fnode(s, cx[2], A_Y, W, A_H, ["NORMALISE & COMPARE", "parse diagnostics and reveal_type",
                "align by statement"], "det")
    flt = fnode(s, cx[3], A_Y, W, A_H, ["AUTO-FILTER", "KB: intended, known, cascades, invalid", "dismissed ones leave"], "det")
    rev = fnode(s, cx[4], A_Y, W, A_H, ["REVIEW QUEUE", "grouped into patterns (triage)"], "human")
    # row B
    B_Y, B_H = 3.4, 1.25
    kb = fnode(s, cx[3], B_Y + 0.1, W, 1.05, ["Add KB / harness rule"], "human")
    dia = fnode(s, cx[4], B_Y, W, B_H, ["Real candidate?"], "dia")
    # row C
    C_Y, C_H = 4.95, 0.75
    hits = fnode(s, cx[4], C_Y, W, C_H, ["Hits"], "pill")
    ver = fnode(s, cx[3], C_Y - 0.2, W, 1.3, ["VERIFY", "spec, CPython, tracker search, minimal repro"], "human")
    iss = fnode(s, cx[2], C_Y, W, C_H, ["FILE ISSUE", "upstream"], "human")
    # row D
    D_Y = 6.0
    llm = fnode(s, cx[4], D_Y, W, 0.8, ["LLM MUTATION", "LLM generates only, never judges"], "llm")
    # dismissed
    # connectors (sites: 0 top, 1 left, 2 bottom, 3 right)
    conn(s, inp, 3, run, 1)
    conn(s, run, 3, nor, 1)
    conn(s, nor, 3, flt, 1)
    conn(s, flt, 3, rev, 1)
    conn(s, rev, 2, dia, 0)
    conn(s, dia, 1, kb, 3)
    conn(s, kb, 0, flt, 2)
    conn(s, dia, 2, hits, 0)
    conn(s, hits, 1, ver, 3)
    conn(s, ver, 1, iss, 3)
    conn(s, hits, 2, llm, 0)
    conn(s, llm, 1, inp, 2, kind=MSO_CONNECTOR.ELBOW, dash=True, color=ACCENT)
    # labels
    text(s, cx[3] + W - 0.05, B_Y + 0.2, 0.5, 0.35, "No", size=14, bold=True, color=GREY)
    text(s, cx[4] + W / 2 + 0.05, B_Y + B_H + 0.0, 0.6, 0.35, "Yes", size=14, bold=True, color=GREY)
    # legend
    lx, ly = 2.2, 3.5
    items = [(ACCENT, None, "Deterministic"), (WHITE, ACCENT, "LLM (dashed)"), (LIGHT, GREY, "Human")]
    for i, (f, l, lab) in enumerate(items):
        x = lx; ly_i = ly + i * 0.45
        b = rect(s, x, ly_i + 0.05, 0.35, 0.25, fill=f, line=l, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=1.5)
        if f == WHITE:
            d = etree.SubElement(b.line._get_or_add_ln(), qn("a:prstDash")); d.set("val", "dash")
        text(s, x + 0.42, ly_i, 1.9, 0.35, lab, size=14, color=NAVY)
    text(s, lx, ly + 1.35, 3.2, 0.6, "Dashed arrow: fuzzing loop back to inputs", size=14, color=GREY)
    notes(s, "Here is the full pipeline. Inputs are 27 hand-written seeds, about 4,849 harvested programs, and LLM-generated variants. "
             "We run mypy, ty and pyright with pinned versions plus real CPython as ground truth, then normalise and compare the outputs. "
             "An auto-filter with a knowledge base drops known or intended differences. "
             "What remains goes to a review queue grouped by pattern. If it is not a real candidate, we add a knowledge base or harness rule. "
             "If it is, the LLM only generates new variants that feed back into the inputs, and we verify against the spec, CPython and the trackers before filing upstream.")


def slide_plan(prs):
    s = blank(prs)
    title(s, "Plan: six stages", 5)
    stages = [
        ("Setup", "Pinned tools: ty 0.0.84, mypy 2.4.0, pyright. Docs corpus, knowledge-base self-test.", "Done"),
        ("Seed run and triage", "Hand-written seeds + 4,849 harvested programs. Group findings into patterns, teach the KB what is noise.", "In progress"),
        ("LLM mutation", "Variants of promising hits (feature crossovers), judged deterministically.", "Upcoming"),
        ("LLM generation + crash hunting", "New programs in under-covered areas: ParamSpec, TypedDict, overloads, recursive aliases.", "Upcoming"),
        ("Judging and filing", "Spec rule, CPython oracle, duplicate search, minimal repro. One issue per root cause.", "Upcoming"),
        ("Write-up", "Results tables, discrepancy dataset, filed issues.", "Upcoming"),
    ]
    n, gap = 6, 0.12
    x0 = 0.45
    w = (SW - 2 * x0 - (n - 1) * gap) / n
    for i, (head, body, st) in enumerate(stages):
        x = x0 + i * (w + gap)
        ch = rect(s, x, 1.6, w, 1.0, fill=ACCENT if st == "Done" else (WHITE if st == "In progress" else LIGHT),
                  line=ACCENT if st != "Upcoming" else None,
                  shape=MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON, lw=2.0)
        ch.adjustments[0] = 0.18
        col = WHITE if st == "Done" else NAVY
        fill_tf(ch.text_frame, [(f"{i + 1}", {"size": 24, "bold": True})], color=col,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, inset=0.02)
        text(s, x, 2.75, w, 0.85, head, size=16, bold=True, color=NAVY, anchor=MSO_ANCHOR.TOP)
        text(s, x, 3.6, w, 1.9, body, size=14, color=NAVY)
        chip = rect(s, x + 0.05, 5.5, w - 0.3, 0.42,
                    fill=ACCENT if st == "Done" else (WHITE if st == "In progress" else LIGHT),
                    line=ACCENT if st == "In progress" else None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=2.0)
        chip.adjustments[0] = 0.5
        fill_tf(chip.text_frame, st, size=14, bold=True,
                color=WHITE if st == "Done" else (ACCENT if st == "In progress" else GREY),
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, inset=0.02)
    rect(s, 0.5, 6.15, SW - 1.0, 0.7, fill=LIGHT)
    rect(s, 0.5, 6.15, 0.08, 0.7, fill=ACCENT)
    pr = ["Free LLMs generate, never judge", "Judge patterns, not individual findings", "Search trackers before filing"]
    pw = (SW - 1.0 - 0.3) / 3
    for i, t in enumerate(pr):
        text(s, 0.7 + i * pw, 6.15, pw - 0.1, 0.7, t, size=16, bold=True, color=ACCENT,
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    notes(s, "This is our plan as six stages. Setup is done: tools are pinned, the docs corpus is in and the knowledge base passes its self-test. "
             "We are now in stage two, running the hand-written and harvested seeds and triaging the findings into patterns. "
             "Next the LLM mutates promising hits, then generates new programs for under-covered areas and hunts crashes, and every result is judged deterministically. "
             "Then we judge and file: spec rule, CPython as oracle, duplicate search and a minimal repro, one issue per root cause. "
             "The last stage is the write-up. Three principles run through it: free LLMs generate but never judge, we judge patterns rather than single findings, and we search trackers before filing. "
             "The LLM budget is about 20 dollars in total.")


def slide_updates(prs):
    s = blank(prs)
    title(s, "Updates: what is done so far", 6)
    items = [
        ("Pipeline built end to end: ", "runs mypy, ty, pyright and CPython, normalises output, detects disagreements, auto-dismisses known ones with a knowledge base, groups the rest into patterns."),
        ("First probe: ", "a hand-written Self seed led to our first report (ty#4656). Closed as intended; a related display bug is ty#4673. Lesson: argue the accused tool's side before filing."),
        ("Corpus: ", "27 hand-written seeds plus 4,849 harvested programs (typing conformance suite, ty mdtests, mypy tests)."),
        ("First full run: ", "7,480 findings in 618 patterns, all deterministic, no LLM."),
        ("Triage of top 5 patterns: ", "all harness noise or design differences, no new bug yet. It showed our 'strong bug evidence' flag was misleading."),
        ("Pipeline fixes: ", "NameError no longer blames the silent tool, stub-function None ignored, runtime-miss anchored on full statement, 4 scoped KB entries, harvest provenance, 1,423 other-version mdtest snippets skipped. 81 tests pass."),
        ("In progress: ", "re-run on the fixed pipeline."),
    ]
    tb = s.shapes.add_textbox(Inches(MARGIN), Inches(1.45), Inches(8.2), Inches(5.4))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (lead, body) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if i:
            p.space_before = Pt(9)
        for t, b, c in (("\u25AA  ", True, ACCENT), (lead, True, NAVY), (body, False, NAVY)):
            r = p.add_run(); r.text = t
            r.font.name, r.font.size, r.font.bold = FONT, Pt(17), b
            r.font.color.rgb = c
    # funnel
    fx, fw = 9.3, 3.35
    stages = [("7,480", "findings", 1.0), ("618", "patterns", 0.8), ("5", "top patterns triaged", 0.62), ("0", "confirmed bugs yet", 0.46)]
    y = 1.75
    for i, (num, lab, f) in enumerate(stages):
        w = fw * f
        b = rect(s, fx + (fw - w) / 2, y, w, 1.0, fill=ACCENT if i < 3 else NAVY)
        fill_tf(b.text_frame, [(num, {"size": 24, "bold": True}), (lab, {"size": 14})], color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, inset=0.03)
        y += 1.2
    notes(s, "Here is what is done so far. The pipeline works end to end: it runs mypy, ty, pyright and CPython, compares them, filters known differences with a knowledge base and groups the rest into patterns. "
             "Our first probe, a hand-written Self seed, became ty issue 4656. The maintainers closed it as intended behaviour, and a related display bug is ty 4673, so we learned to argue the other tool's side before filing. "
             "The corpus is 27 hand-written seeds plus 4,849 harvested programs. The first full run gave 7,480 findings in 618 patterns, with no LLM involved. "
             "We triaged the top five patterns and all were harness noise or design differences, so no confirmed bug yet. That exposed a misleading evidence flag, and we fixed it along with several other pipeline issues, and 81 tests pass. "
             "A re-run on the fixed pipeline is in progress, so we have no results from it to show today.")


def slide_outcomes(prs):
    s = blank(prs)
    title(s, "Expected outcomes", 7)
    pts = [
        ("New, confirmed bugs", "Reportable bugs in ty (and mypy): minimal repros filed upstream "
                                "with spec references, checked against the trackers for duplicates."),
        ("A discrepancy dataset", "Disagreements classified as real bug, intended, known or harness "
                                  "noise, with evidence, reusable by others."),
        ("A reusable pipeline", "Knowledge base and triage discard known differences cheaply, so humans "
                                "review only real candidates. Funnel numbers: programs, disagreements, "
                                "candidates, confirmed, filed."),
    ]
    y = 1.6
    for i, (h, b) in enumerate(pts, 1):
        o = rect(s, MARGIN + 0.05, y + 0.15, 0.7, 0.7, fill=ACCENT, shape=MSO_SHAPE.OVAL)
        fill_tf(o.text_frame, str(i), size=26, color=WHITE, bold=True, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE, inset=0)
        text(s, MARGIN + 1.1, y, 3.3, 1.0, h, size=24, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        text(s, MARGIN + 4.5, y, SW - 2 * MARGIN - 4.5, 1.0, b, size=18, anchor=MSO_ANCHOR.MIDDLE)
        y += 1.3
    notes(s, "We expect three things. First, new confirmed bugs in ty and possibly mypy, each with a minimal repro and a spec reference, checked against the trackers so we do not file duplicates. "
             "Second, a documented dataset of disagreements, labelled as real bug, intended, known or noise, with evidence. "
             "Third, a reusable pipeline that cheaply discards known differences so humans only look at real candidates, with measured funnel numbers. "
             "We are not promising a specific number of bugs. The status of all this is on the updates slide.")


SLIDES = [slide_title, slide_problem, slide_motivation, slide_arch, slide_plan, slide_updates, slide_outcomes]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    prs = new_prs()
    for fn in SLIDES:
        fn(prs)
    prs.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
