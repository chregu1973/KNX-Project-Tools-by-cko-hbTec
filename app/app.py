from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from pathlib import Path
import os
import re
import secrets
import uuid

from core.knx_project import KNXProjectParser
from core.project_manager import ProjectManager
from core.xml_reader import (
    InvalidKNXProject,
    InvalidProjectPassword,
    ProjectPasswordRequired,
)
from exporters.csv_export import export_devices
from datetime import datetime
from exporters.ptouch_export import export_ptouch
from exporters.ptouch_project import export_ptouch_project, ptouch_download_name
from exporters.label_pdf import export_packaging_labels
from exporters.dymo_export import dymo_download_name, export_dymo_csv, export_dymo_pdf

UPLOAD_FOLDER = "/data/uploads"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



def build_export_name(project, export_type, extension):
    """Erzeugt einen sicheren Downloadnamen aus Projektname und Datum."""

    project_filename = getattr(project, "filename", "") or "KNX-Projekt"
    project_name = Path(project_filename).stem

    project_name = re.sub(
        r"[^\wÄÖÜäöüß-]+",
        "_",
        project_name,
        flags=re.UNICODE
    ).strip("_-")

    if not project_name or project_name.lower() == "current":
        project_name = "KNX-Projekt"

    export_date = datetime.now().strftime("%Y-%m")

    return f"{project_name}_{export_type}_{export_date}.{extension}"



@app.route("/")
def index():

    project = ProjectManager.load()

    manufacturers = {}

    if project:
        for device in project.devices:
            name = device.manufacturer or "Unbekannt"
            manufacturers[name] = manufacturers.get(name, 0) + 1

    return render_template(
        "dashboard.html",
        project=project,
        manufacturers=manufacturers
    )

@app.route("/addresses")
def addresses():

    project = ProjectManager.load()

    return render_template(
        "addresses.html",
        project=project
    )

@app.route("/ptouch")
def ptouch():

    project = ProjectManager.load()

    return render_template(
        "ptouch.html",
        project=project,
        date=datetime.now().strftime("%m-%Y"),
        areas=project.areas if project else [],
        lines=project.lines if project else []
    )

@app.route("/dymo")
def dymo():
    project = ProjectManager.load()
    return render_template("dymo.html", project=project)


@app.route("/label-options")
def label_options():
    return render_template("label_options.html")


@app.route("/labels")
def labels():

    project = ProjectManager.load()

    return render_template(
        "labels.html",
        project=project
    )
@app.route("/export/labels-pdf", methods=["POST"])
def export_labels_pdf():

    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))
    selected_addresses = request.form.getlist("device")

    if not selected_addresses:
        flash("Bitte mindestens ein Gerät für den Etikettenexport auswählen.")
        return redirect(url_for("labels"))

    start_position = request.form.get("start_position", 1)

    logo_data = None
    logo_file = request.files.get("logo")

    if logo_file and logo_file.filename:
        logo_extension = Path(logo_file.filename).suffix.lower()

        if logo_extension not in {".png", ".jpg", ".jpeg"}:
            flash("Bitte für das Logo eine PNG- oder JPG-Datei verwenden.")
            return redirect(url_for("labels"))

        logo_data = logo_file.read((2 * 1024 * 1024) + 1)

        if not logo_data or len(logo_data) > 2 * 1024 * 1024:
            flash("Das Logo darf maximal 2 MB gross sein.")
            return redirect(url_for("labels"))

        try:
            from io import BytesIO
            from reportlab.lib.utils import ImageReader
            ImageReader(BytesIO(logo_data)).getSize()
        except Exception:
            flash("Die ausgewählte Logo-Datei konnte nicht gelesen werden.")
            return redirect(url_for("labels"))

    os.makedirs("/data/exports", exist_ok=True)
    filename = "/data/exports/verpackungsetiketten.pdf"

    export_packaging_labels(
        project,
        filename,

        label_width=request.form.get("width", 70),
        label_height=request.form.get("height", 35),

        cols=request.form.get("cols", 3),
        rows=request.form.get("rows", 8),

        margin_left=request.form.get("margin_left", 0),
        margin_top=request.form.get("margin_top", 8),
        gap_x=request.form.get("gap_x", 0),
        gap_y=request.form.get("gap_y", 0),
        logo_data=logo_data,

        show_address="address" in request.form,
        show_room="room" in request.form,
        show_description="description" in request.form,
        show_location="location" in request.form,
        show_serial="serial" in request.form,
        selected_addresses=selected_addresses,
        start_position=start_position,
    )

    return send_file(
        filename,
        as_attachment=True,
        download_name=build_export_name(project, "Etiketten", "pdf")
    )

@app.route("/export/ptouch", methods=["POST"])
def export_ptouch_csv():
    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))

    selected_addresses = request.form.getlist("device")
    if not selected_addresses:
        flash("Bitte mindestens ein Gerät auswählen.")
        return redirect(url_for("ptouch"))

    prefix = request.form.get("prefix", "Firma XY | IBS").strip()
    date = request.form.get("date", datetime.now().strftime("%m-%Y")).strip()

    os.makedirs("/data/exports", exist_ok=True)
    filename = "/data/exports/brother_ptouch.csv"

    export_ptouch(
        project,
        filename,
        prefix=prefix,
        date=date,
        selected_addresses=selected_addresses,
    )

    return send_file(
        filename,
        as_attachment=True,
        download_name=ptouch_download_name(project, date, "csv"),
    )


@app.route("/export/ptouch-project", methods=["POST"])
def export_ptouch_project_file():
    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))

    selected_addresses = request.form.getlist("device")
    if not selected_addresses:
        flash("Bitte mindestens ein Gerät auswählen.")
        return redirect(url_for("ptouch"))

    prefix = request.form.get("prefix", "Firma XY | IBS").strip()
    date = request.form.get("date", datetime.now().strftime("%m-%Y")).strip()

    os.makedirs("/data/exports", exist_ok=True)
    template_filename = Path(app.root_path) / "assets" / "ptouch_6mm_template.lbxs"
    filename = "/data/exports/brother_ptouch.lbxs"

    try:
        export_ptouch_project(
            project,
            template_filename,
            filename,
            prefix=prefix,
            date=date,
            selected_addresses=selected_addresses,
        )
    except (OSError, ValueError) as error:
        app.logger.exception("P-touch-Projekt konnte nicht erzeugt werden")
        flash(f"P-touch-Projekt konnte nicht erzeugt werden: {error}")
        return redirect(url_for("ptouch"))

    return send_file(
        filename,
        as_attachment=True,
        download_name=ptouch_download_name(project, date, "lbxs"),
    )


@app.route("/export/dymo-pdf", methods=["POST"])
def export_dymo_pdf_file():
    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))

    selected_addresses = request.form.getlist("device")
    if not selected_addresses:
        flash("Bitte mindestens ein Gerät für den DYMO-Export auswählen.")
        return redirect(url_for("dymo"))

    content_fields = {"location", "address", "room", "description"}
    if not any(field in request.form for field in content_fields):
        flash("Bitte mindestens einen Etiketteninhalt auswählen.")
        return redirect(url_for("dymo"))

    logo_data = None
    logo_file = request.files.get("logo")

    if logo_file and logo_file.filename:
        logo_extension = Path(logo_file.filename).suffix.lower()

        if logo_extension not in {".png", ".jpg", ".jpeg"}:
            flash("Bitte für das Logo eine PNG- oder JPG-Datei verwenden.")
            return redirect(url_for("dymo"))

        logo_data = logo_file.read((2 * 1024 * 1024) + 1)

        if not logo_data or len(logo_data) > 2 * 1024 * 1024:
            flash("Das Logo darf maximal 2 MB gross sein.")
            return redirect(url_for("dymo"))

        try:
            from io import BytesIO
            from reportlab.lib.utils import ImageReader
            ImageReader(BytesIO(logo_data)).getSize()
        except Exception:
            flash("Die ausgewählte Logo-Datei konnte nicht gelesen werden.")
            return redirect(url_for("dymo"))

    os.makedirs("/data/exports", exist_ok=True)
    filename = "/data/exports/dymo_11354.pdf"

    try:
        export_dymo_pdf(
            project,
            filename,
            selected_addresses=selected_addresses,
            logo_data=logo_data,
            show_location="location" in request.form,
            show_address="address" in request.form,
            show_room="room" in request.form,
            show_description="description" in request.form,
        )
    except (OSError, ValueError) as error:
        app.logger.exception("DYMO-PDF konnte nicht erzeugt werden")
        flash(f"DYMO-PDF konnte nicht erzeugt werden: {error}")
        return redirect(url_for("dymo"))

    return send_file(
        filename,
        as_attachment=True,
        download_name=dymo_download_name(project, "pdf"),
    )


@app.route("/export/dymo-csv", methods=["POST"])
def export_dymo_csv_file():
    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))

    selected_addresses = request.form.getlist("device")
    if not selected_addresses:
        flash("Bitte mindestens ein Gerät für den DYMO-Export auswählen.")
        return redirect(url_for("dymo"))

    os.makedirs("/data/exports", exist_ok=True)
    filename = "/data/exports/dymo_11354.csv"

    export_dymo_csv(
        project,
        filename,
        selected_addresses=selected_addresses,
    )

    return send_file(
        filename,
        as_attachment=True,
        download_name=dymo_download_name(project, "csv"),
    )


@app.route("/export/csv")
def export_csv():

    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))

    os.makedirs("/data/exports", exist_ok=True)

    filename = "/data/exports/Physikalische_Adressen.csv"

    export_devices(project, filename)

    return send_file(
        filename,
        as_attachment=True,
        download_name=build_export_name(project, "Geraeteliste", "csv")
    )


@app.route("/project/delete", methods=["POST"])
def delete_project():
    """Entfernt das aktuell geladene Projekt und daraus erzeugte Downloads."""

    try:
        ProjectManager.clear()

        data_directories = (
            Path(app.config["UPLOAD_FOLDER"]),
            Path("/data/exports"),
        )

        for directory in data_directories:
            if not directory.exists():
                continue

            for stored_file in directory.iterdir():
                if stored_file.is_file():
                    stored_file.unlink()

    except OSError:
        app.logger.exception("Projekt konnte nicht vollständig gelöscht werden.")
        flash("Projekt konnte nicht vollständig gelöscht werden.")
        return redirect(url_for("index"))

    flash("Projekt wurde gelöscht. Du kannst jetzt ein neues Projekt laden.")
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload():


    file = request.files.get("project")

    if not file:
        flash("Keine Datei ausgewählt.")
        return redirect(url_for("index"))

    if not file.filename.lower().endswith(".knxproj"):
        flash("Bitte eine ETS Projektdatei auswählen.")
        return redirect(url_for("index"))

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    original_filename = Path(file.filename).name
    password = request.form.get("project_password", "")
    pending_path = Path(UPLOAD_FOLDER) / f".upload-{uuid.uuid4().hex}.knxproj"

    try:
        file.save(pending_path)
        parser = KNXProjectParser(pending_path, password=password)
        project = parser.load()
    except ProjectPasswordRequired as error:
        pending_path.unlink(missing_ok=True)
        flash(str(error))
        return redirect(url_for("index"))
    except InvalidProjectPassword as error:
        pending_path.unlink(missing_ok=True)
        flash(str(error))
        return redirect(url_for("index"))
    except InvalidKNXProject as error:
        pending_path.unlink(missing_ok=True)
        flash(str(error))
        return redirect(url_for("index"))
    except Exception:
        pending_path.unlink(missing_ok=True)
        app.logger.exception("ETS-Projekt konnte nicht eingelesen werden.")
        flash("Das ETS-Projekt konnte nicht eingelesen werden.")
        return redirect(url_for("index"))
    finally:
        # Das Klartext-Passwort wird nicht in Session, Cache oder Datei abgelegt.
        password = None

    if not project.devices:
        pending_path.unlink(missing_ok=True)
        flash("Im ETS-Projekt wurden keine adressierten KNX-Geräte gefunden.")
        return redirect(url_for("index"))

    current_path = Path(UPLOAD_FOLDER) / "current.knxproj"

    for old_file in Path(UPLOAD_FOLDER).glob("*.knxproj"):
        if old_file != pending_path:
            old_file.unlink()

    pending_path.replace(current_path)

    # Originalen Dateinamen für spätere Exporte beibehalten
    project.filename = original_filename

    ProjectManager.save(project)

    flash("Projekt erfolgreich geladen.")

    return redirect(url_for("index"))


if __name__ == "__main__":

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
