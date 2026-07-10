from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def fit_text(c, text, max_width, font="Helvetica", size=8):
    text = str(text or "")
    c.setFont(font, size)

    if c.stringWidth(text, font, size) <= max_width:
        return text

    while text and c.stringWidth(text + "...", font, size) > max_width:
        text = text[:-1]

    return text + "..."


def export_packaging_labels(
    project,
    filename,
    label_width=70,
    label_height=35,
    cols=3,
    rows=8,
    margin_left=0,
    margin_top=8,
    gap_x=0,
    gap_y=0,
    show_address=True,
    show_room=True,
    show_description=True,
    show_location=True,
    show_serial=False,
    selected_addresses=None,
    start_position=1,
):
    c = canvas.Canvas(filename, pagesize=A4)
    page_w, page_h = A4

    label_w = float(label_width) * mm
    label_h = float(label_height) * mm
    margin_x = float(margin_left) * mm
    margin_y = float(margin_top) * mm
    gap_x = float(gap_x) * mm
    gap_y = float(gap_y) * mm

    cols = int(cols)
    rows = int(rows)
    per_page = cols * rows
    devices = project.devices

    if selected_addresses is not None:
        selected = set(selected_addresses)
        devices = [
            device
            for device in project.devices
            if device.address in selected
        ]

    start_position = max(1, min(int(start_position), per_page))
    start_offset = start_position - 1

    for index, d in enumerate(devices):

        slot_index = start_offset + index

        if slot_index > 0 and slot_index % per_page == 0:
            c.showPage()

        page_index = slot_index % per_page
        col = page_index % cols
        row = page_index // cols
        x = margin_x + col * (label_w + gap_x)
        y = page_h - margin_y - (row + 1) * label_h - row * gap_y

        c.setLineWidth(0.2)
        c.rect(x, y, label_w, label_h)

        pad = 4 * mm
        text_x = x + pad
        max_text_w = label_w - (2 * pad)

        cursor_y = y + label_h - 6 * mm

        if show_location and d.location:
            txt = fit_text(c, d.location, max_text_w, "Helvetica-Bold", 6)
            c.drawString(text_x, cursor_y, txt)
            cursor_y -= 7 * mm

        if show_address:
            txt = fit_text(c, d.address, max_text_w, "Helvetica-Bold", 16)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(text_x, cursor_y, txt)
            cursor_y -= 7 * mm

        if show_room and d.room:
            txt = fit_text(c, d.room, max_text_w, "Helvetica-Bold", 9)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(text_x, cursor_y, txt)
            cursor_y -= 5 * mm

        if show_description and d.description:
            txt = fit_text(c, d.description, max_text_w, "Helvetica", 8)
            c.setFont("Helvetica", 8)
            c.drawString(text_x, cursor_y, txt)

    c.save()
