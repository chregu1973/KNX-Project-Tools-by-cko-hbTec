from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from pathlib import Path
import os
import uuid

from core.knx_project import KNXProjectParser
from core.project_manager import ProjectManager
from exporters.csv_export import export_devices
from datetime import datetime
from exporters.ptouch_export import export_ptouch
from exporters.label_pdf import export_packaging_labels

UPLOAD_FOLDER = "/data/uploads"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
app.secret_key = "knx-project-tools"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



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
    start_position = request.form.get("start_position", 1)

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
        download_name="verpackungsetiketten.pdf"
    )

@app.route("/export/ptouch")
def export_ptouch_csv():

    project = ProjectManager.load()

    if project is None:
        flash("Kein Projekt geladen.")
        return redirect(url_for("index"))

    prefix = request.args.get("prefix", "hbTec | IBS")
    date = request.args.get("date", datetime.now().strftime("%m-%Y"))
    area = request.args.get("area", "")
    line = request.args.get("line", "")

    os.makedirs("/data/exports", exist_ok=True)

    filename = "/data/exports/brother_ptouch.csv"

    export_ptouch(
        project,
        filename,
        prefix=prefix,
        date=date,
        area=area,
        line=line
   )

    
    return send_file(
        filename,
        as_attachment=True,
        download_name="brother_ptouch.csv"
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
        download_name="Physikalische_Adressen.csv"
    )


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

    for old_file in Path(UPLOAD_FOLDER).glob("*.knxproj"):
        old_file.unlink()

    filename = "current.knxproj"

    path = Path(UPLOAD_FOLDER) / filename

    file.save(path)

    parser = KNXProjectParser(path)

    project = parser.load()

    project.filename = original_filename

    project = parser.load()

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
