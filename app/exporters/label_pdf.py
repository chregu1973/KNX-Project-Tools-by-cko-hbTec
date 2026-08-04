from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
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
    logo_data=None,
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

    logo = ImageReader(BytesIO(logo_data)) if logo_data else None
    logo_source_width = 0
    logo_source_height = 0

    if logo:
        logo_source_width, logo_source_height = logo.getSize()

    # Helle Logos auf transparentem Grund würden auf weissen Etiketten
    # verschwinden. Die tatsächlichen Bildpixel werden deshalb unabhängig
    # vom Dateinamen geprüft. Transparente Pixel zählen nicht mit.
    logo_needs_dark_background = False

    if logo_data:
        try:
            from PIL import Image

            with Image.open(BytesIO(logo_data)) as source_image:
                sample = source_image.convert("RGBA")
                sample.thumbnail((128, 128))

                visible_pixels = [
                    pixel for pixel in sample.getdata()
                    if pixel[3] >= 32
                ]

                if visible_pixels:
                    light_pixels = 0

                    for red, green, blue, alpha in visible_pixels:
                        luminance = (
                            0.2126 * red
                            + 0.7152 * green
                            + 0.0722 * blue
                        )

                        if luminance >= 205:
                            light_pixels += 1

                    light_share = light_pixels / len(visible_pixels)
                    logo_needs_dark_background = light_share >= 0.72
        except Exception:
            # ReportLab kann das Bild bereits lesen. Falls die optionale
            # Pixelanalyse scheitert, bleibt der bisherige transparente
            # Ausdruck erhalten.
            logo_needs_dark_background = False

    logo = ImageReader(BytesIO(logo_data)) if logo_data else None
    logo_source_width = 0
    logo_source_height = 0

    if logo:
        logo_source_width, logo_source_height = logo.getSize()

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
        middle_line_max_w = max_text_w

        if logo:
            logo_box_w = min(18 * mm, max_text_w)
            logo_box_h = min(8 * mm, max(1 * mm, label_h - (2 * pad)))
            logo_box_x = x + label_w - pad - logo_box_w
            logo_box_y = y + (label_h - logo_box_h) / 2

            # Ein heller Bildinhalt erhält automatisch eine dunkle Fläche.
            # Dunkle und farbige Logos werden weiterhin transparent gedruckt.
            logo_inner_pad = 1.1 * mm if logo_needs_dark_background else 0
            available_logo_w = max(1 * mm, logo_box_w - (2 * logo_inner_pad))
            available_logo_h = max(1 * mm, logo_box_h - (2 * logo_inner_pad))

            logo_scale = min(
                available_logo_w / logo_source_width,
                available_logo_h / logo_source_height,
            )
            logo_draw_w = logo_source_width * logo_scale
            logo_draw_h = logo_source_height * logo_scale
            logo_x = logo_box_x + (logo_box_w - logo_draw_w) / 2
            logo_y = logo_box_y + (logo_box_h - logo_draw_h) / 2

            if logo_needs_dark_background:
                c.saveState()
                c.setFillColorRGB(0.055, 0.09, 0.15)
                c.roundRect(
                    logo_box_x,
                    logo_box_y,
                    logo_box_w,
                    logo_box_h,
                    1.2 * mm,
                    stroke=0,
                    fill=1,
                )
                c.restoreState()

            c.drawImage(
                logo,
                logo_x,
                logo_y,
                width=logo_draw_w,
                height=logo_draw_h,
                preserveAspectRatio=True,
                mask="auto",
            )

            middle_line_max_w = max(1 * mm, max_text_w - logo_box_w - (2 * mm))

        cursor_y = y + label_h - 6 * mm

        if show_location and d.location:
            txt = fit_text(c, d.location, max_text_w, "Helvetica-Bold", 6)
            c.drawString(text_x, cursor_y, txt)
            cursor_y -= 7 * mm

        if show_address:
            txt = fit_text(c, d.address, middle_line_max_w, "Helvetica-Bold", 16)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(text_x, cursor_y, txt)
            cursor_y -= 7 * mm

        if show_room and d.room:
            txt = fit_text(c, d.room, middle_line_max_w, "Helvetica-Bold", 9)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(text_x, cursor_y, txt)
            cursor_y -= 5 * mm

        if show_description and d.description:
            txt = fit_text(c, d.description, max_text_w, "Helvetica", 8)
            c.setFont("Helvetica", 8)
            c.drawString(text_x, cursor_y, txt)

    c.save()
