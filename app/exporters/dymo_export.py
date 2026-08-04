import csv
import re
from io import BytesIO, StringIO
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


DYMO_WIDTH = 57 * mm
DYMO_HEIGHT = 32 * mm
DYMO_FIELDS = [
    "Standort",
    "Adresse",
    "Raum",
    "Beschreibung",
    "Seriennummer",
]


def selected_dymo_devices(project, selected_addresses=None):
    if selected_addresses is None:
        return list(project.devices)

    wanted = {str(address) for address in selected_addresses}
    return [device for device in project.devices if device.address in wanted]


def dymo_download_name(project, extension):
    source = (
        getattr(project, "name", "")
        or Path(getattr(project, "filename", "KNX_Projekt")).stem
    )
    stem = re.sub(
        r"[^A-Za-z0-9ÄÖÜäöüß_-]+",
        "_",
        str(source),
    ).strip("_-") or "KNX_Projekt"
    return f"{stem}_DYMO_11354.{extension}"


def export_dymo_csv(project, filename, selected_addresses=None):
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(DYMO_FIELDS)

    for device in selected_dymo_devices(project, selected_addresses):
        writer.writerow([
            device.location,
            device.address,
            device.room,
            device.description,
            device.serial,
        ])

    Path(filename).write_bytes(output.getvalue().encode("utf-8-sig"))


def _fit_text(value, maximum_width, font_name, font_size):
    text = " ".join(str(value or "").split())

    if not text:
        return ""

    if stringWidth(text, font_name, font_size) <= maximum_width:
        return text

    suffix = "…"
    low = 0
    high = len(text)

    while low < high:
        middle = (low + high + 1) // 2
        candidate = text[:middle].rstrip() + suffix

        if stringWidth(candidate, font_name, font_size) <= maximum_width:
            low = middle
        else:
            high = middle - 1

    return text[:low].rstrip() + suffix if low else ""


def _light_logo_needs_background(logo_data):
    if not logo_data:
        return False

    try:
        from PIL import Image

        with Image.open(BytesIO(logo_data)) as source_image:
            sample = source_image.convert("RGBA")
            sample.thumbnail((128, 128))
            visible_pixels = [pixel for pixel in sample.getdata() if pixel[3] >= 32]

            if not visible_pixels:
                return False

            light_pixels = 0

            for red, green, blue, alpha in visible_pixels:
                luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                if luminance >= 205:
                    light_pixels += 1

            return (light_pixels / len(visible_pixels)) >= 0.72
    except Exception:
        return False


def export_dymo_pdf(
    project,
    filename,
    selected_addresses=None,
    logo_data=None,
    show_location=True,
    show_address=True,
    show_room=True,
    show_description=True,
):
    devices = selected_dymo_devices(project, selected_addresses)

    if not devices:
        raise ValueError("Es wurden keine DYMO-Etiketten ausgewählt.")

    pdf = canvas.Canvas(
        str(filename),
        pagesize=(DYMO_WIDTH, DYMO_HEIGHT),
        pageCompression=1,
    )
    pdf.setTitle("KNX DYMO 11354 Etiketten")

    logo = ImageReader(BytesIO(logo_data)) if logo_data else None
    logo_source_width = 0
    logo_source_height = 0

    if logo:
        logo_source_width, logo_source_height = logo.getSize()

    logo_needs_dark_background = _light_logo_needs_background(logo_data)

    pad = 3 * mm
    maximum_width = DYMO_WIDTH - (2 * pad)
    middle_width = maximum_width

    logo_box_width = 15 * mm
    logo_box_height = 10 * mm
    logo_box_x = DYMO_WIDTH - pad - logo_box_width
    logo_box_y = (DYMO_HEIGHT - logo_box_height) / 2

    if logo:
        middle_width = max(1 * mm, maximum_width - logo_box_width - (2 * mm))

    for device in devices:
        pdf.setFillColorRGB(1, 1, 1)
        pdf.rect(0, 0, DYMO_WIDTH, DYMO_HEIGHT, stroke=0, fill=1)
        pdf.setFillColorRGB(0.04, 0.06, 0.09)

        if logo:
            logo_inner_pad = 1.1 * mm if logo_needs_dark_background else 0
            available_width = max(1 * mm, logo_box_width - (2 * logo_inner_pad))
            available_height = max(1 * mm, logo_box_height - (2 * logo_inner_pad))
            logo_scale = min(
                available_width / logo_source_width,
                available_height / logo_source_height,
            )
            logo_width = logo_source_width * logo_scale
            logo_height = logo_source_height * logo_scale
            logo_x = logo_box_x + (logo_box_width - logo_width) / 2
            logo_y = logo_box_y + (logo_box_height - logo_height) / 2

            if logo_needs_dark_background:
                pdf.saveState()
                pdf.setFillColorRGB(0.055, 0.09, 0.15)
                pdf.roundRect(
                    logo_box_x,
                    logo_box_y,
                    logo_box_width,
                    logo_box_height,
                    1.2 * mm,
                    stroke=0,
                    fill=1,
                )
                pdf.restoreState()

            pdf.drawImage(
                logo,
                logo_x,
                logo_y,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto",
            )

        if show_location and device.location:
            pdf.setFont("Helvetica-Bold", 6.2)
            pdf.drawString(
                pad,
                26.4 * mm,
                _fit_text(device.location, maximum_width, "Helvetica-Bold", 6.2),
            )

        if show_address:
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(
                pad,
                18.2 * mm,
                _fit_text(device.address, middle_width, "Helvetica-Bold", 16),
            )

        if show_room and device.room:
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawString(
                pad,
                12.2 * mm,
                _fit_text(device.room, middle_width, "Helvetica-Bold", 8),
            )

        if show_description and device.description:
            pdf.setFont("Helvetica", 7)
            pdf.drawString(
                pad,
                3.4 * mm,
                _fit_text(device.description, maximum_width, "Helvetica", 7),
            )

        pdf.showPage()

    pdf.save()
