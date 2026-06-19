#!/usr/bin/env python3
"""Generate editable PowerPoint presentation for FAIRweaver workflow slides."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# Constants
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
DIAGRAM_DIR = os.path.join(os.path.dirname(__file__), "diagrams")

# Colors
BLUE = RGBColor(0x15, 0x65, 0xC0)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
DARK_BLUE = RGBColor(0x0D, 0x47, 0xA1)
GRAY = RGBColor(0x61, 0x61, 0x61)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)


def set_font(run, size=18, bold=False, color=BLACK, name="Calibri"):
    """Set font properties on a run."""
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name


def add_title(slide, text, left=Inches(0.5), top=Inches(0.3), width=Inches(12), size=28, color=BLUE):
    """Add a title text box to a slide."""
    txBox = slide.shapes.add_textbox(left, top, width, Inches(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    set_font(run, size=size, bold=True, color=color)
    return txBox


def add_text_box(slide, text, left, top, width, height, size=18, bold=False, color=BLACK, align=PP_ALIGN.LEFT):
    """Add a text box with formatted text."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_font(run, size=size, bold=bold, color=color)
    return txBox


def add_bullet_list(slide, items, left, top, width, height, size=16, color=BLACK):
    """Add a bulleted list to a slide."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.level = 0
        run = p.add_run()
        run.text = item
        set_font(run, size=size, color=color)
    return txBox


def add_image(slide, img_path, left, top, width=None, height=None):
    """Add an image to a slide."""
    if os.path.exists(img_path):
        if width and height:
            slide.shapes.add_picture(img_path, left, top, width, height)
        elif width:
            slide.shapes.add_picture(img_path, left, top, width=width)
        elif height:
            slide.shapes.add_picture(img_path, left, top, height=height)
        else:
            slide.shapes.add_picture(img_path, left, top)


def add_table(slide, data, left, top, width, height, header_color=BLUE):
    """Add a table to a slide."""
    rows = len(data)
    cols = len(data[0])
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    # Set column widths evenly
    col_width = int(width / cols)
    for i in range(cols):
        table.columns[i].width = col_width

    # Populate table
    for i, row in enumerate(data):
        for j, cell_text in enumerate(row):
            cell = table.cell(i, j)
            cell.text = cell_text
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    set_font(run, size=14, bold=(i == 0), color=WHITE if i == 0 else BLACK)
            if i == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_color

    return table_shape


def create_presentation():
    """Create the full presentation."""
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # Use blank layout
    blank_layout = prs.slide_layouts[6]  # Blank layout

    # =========================================================================
    # TITLE SLIDE
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "FAIRweaver: Schema.org → ARC → FAIRagro Workflow",
              top=Inches(2.5), size=36, color=BLUE)
    add_text_box(slide, "TA3/4 Retreat 2026",
                 left=Inches(0.5), top=Inches(4), width=Inches(12), height=Inches(0.8), size=20, color=GRAY)

    # =========================================================================
    # SLIDE 1 — Pipeline Diagram
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 1 — FAIRagro Metadata Transformation Pipeline")
    add_image(slide, os.path.join(DIAGRAM_DIR, "slide1-pipeline.png"),
              left=Inches(0.5), top=Inches(1.5), width=Inches(12))

    # =========================================================================
    # SLIDE 1 — Key Points
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 1 — Key Points")
    bullets = [
        "Sequential dependency: Output B (FAIRagro JSON) is derived from Output A (ARC RO-Crate) — not a parallel output",
        "Two harvest paths converge on the same FAIRagro JSON schema:",
        "  • Path 1 (solid): Direct harvest from GitLab DataHub where ARCs are stored",
        "  • Path 2 (dashed): Via FAIRagro Middleware API (federated service)",
        "Both paths produce identical FAIRagro schema.json ingested into SearchHub"
    ]
    add_bullet_list(slide, bullets, Inches(0.5), Inches(1.5), Inches(12), Inches(5))

    # =========================================================================
    # SLIDE 2 — Three File Scenarios
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 2 — Three File Scenarios: Input → ARC → FAIRagro Output")

    table_data = [
        ["Case", "Input File", "ARC Output", "FAIRagro Output"],
        ["Synthetic", "schema-org-wheat-full.json", "arc-ro-crate-wheat-full ✓ compliant", "Full extraction ✓"],
        ["Real — Small", "arc-ro-crate-dronflyover.json (<10 MB)", "Manual, partial ⚠", "Partial — mappable fields only"],
        ["Real — Large", "arc-ro-crate-muenchenberg-lte.json (>100 MB)", "Manual, partial ⚠", "Basic harvest only"]
    ]
    add_table(slide, table_data, Inches(0.5), Inches(1.5), Inches(12), Inches(2.5))

    add_text_box(slide, "💡 If an ARC follows the FAIRagro specification → full metadata extraction. If not → only basic information is harvested.",
                 left=Inches(0.5), top=Inches(5), width=Inches(12), height=Inches(0.8), size=18, bold=True, color=GREEN)

    # =========================================================================
    # SLIDE 3 — Drone Flyover Structure
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 3 — Examining ARC Structure: Domain Objects at Different Depths")

    bullets = [
        "Goal:",
        "• Understand how Agrischemas concepts map into ARC RO-Crate",
        "• Show that equivalent domain concepts require very different traversal depths"
    ]
    add_bullet_list(slide, bullets, Inches(0.5), Inches(1.3), Inches(12), Inches(1.5))

    add_image(slide, os.path.join(DIAGRAM_DIR, "slide3-drone.png"),
              left=Inches(1.5), top=Inches(2.8), width=Inches(10))

    add_text_box(slide, "Example ARC RO-Crate: UC13 drone-flyover",
                 left=Inches(0.5), top=Inches(6.8), width=Inches(12), height=Inches(0.5), size=14, color=GRAY)

    # =========================================================================
    # SLIDE 4 — Müncheberg Structure
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 4 — Müncheberg ARC: A Different Structural Pattern")

    bullets = [
        "Goal:",
        "• Show another real ARC with a different structural pattern",
        "• Reinforce that parser must handle multiple modeling conventions"
    ]
    add_bullet_list(slide, bullets, Inches(0.5), Inches(1.3), Inches(12), Inches(1.5))

    add_image(slide, os.path.join(DIAGRAM_DIR, "slide4-muenchenberg.png"),
              left=Inches(1.5), top=Inches(2.8), width=Inches(10))

    add_text_box(slide, "Example ARC RO-Crate: Müncheberg LTE",
                 left=Inches(0.5), top=Inches(6.8), width=Inches(12), height=Inches(0.5), size=14, color=GRAY)

    # =========================================================================
    # SLIDE 4 — Comparison Table
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 4 — Comparison: Drone Flyover vs Müncheberg")

    table_data = [
        ["Aspect", "Drone Flyover", "Müncheberg LTE"],
        ["Study entity", "Explicit, in hasPart chain", "Present but disconnected (not in hasPart)"],
        ["Crop species path (short)", "Study → LabProcess → Sample → PropertyValue (4 hops)", "Source → additionalProperty → CharacteristicValue (2 hops)"],
        ["Crop species path (long)", "Same as short (only path)", "ALSO via LabProcess → object → Source → additionalProperty"],
        ["Sensor metadata", "Present (DefinedTerm)", "Absent"],
        ["Assay count", "1", "27+"]
    ]
    add_table(slide, table_data, Inches(0.5), Inches(1.5), Inches(12), Inches(3.5))

    # =========================================================================
    # SLIDE 5 — Required Pattern
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 5 — Required Modeling Pattern & Standardization Gap")

    bullets = [
        "Goal:",
        "• Define the required path for unambiguous extraction",
        "• Identify what still needs standardization"
    ]
    add_bullet_list(slide, bullets, Inches(0.5), Inches(1.3), Inches(12), Inches(1.5))

    add_image(slide, os.path.join(DIAGRAM_DIR, "slide5-required.png"),
              left=Inches(1.5), top=Inches(2.8), width=Inches(10))

    add_text_box(slide, "In bold: required objects/properties to represent Crop",
                 left=Inches(0.5), top=Inches(6.5), width=Inches(12), height=Inches(0.5), size=14, color=GREEN)

    add_text_box(slide, "Example ARC RO-Crate: UC13 drone-flyover",
                 left=Inches(0.5), top=Inches(6.8), width=Inches(12), height=Inches(0.5), size=14, color=GRAY)

    # =========================================================================
    # SLIDE 5 — Open Questions
    # =========================================================================
    slide = prs.slides.add_slide(blank_layout)
    add_title(slide, "Slide 5 — Open Questions")

    table_data = [
        ["Question", "Details"],
        ["Structure: ?", "How to formally specify the required traversal path?"],
        ["propertyID: SSSOM mapping", "How to standardize ontology term mappings?"]
    ]
    add_table(slide, table_data, Inches(0.5), Inches(1.5), Inches(12), Inches(2))

    # =========================================================================
    # SAVE
    # =========================================================================
    output_path = os.path.join(os.path.dirname(__file__), "fairst-workflow-slides-editable.pptx")
    prs.save(output_path)
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    create_presentation()
