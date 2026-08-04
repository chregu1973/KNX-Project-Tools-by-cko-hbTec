import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from exporters.ptouch_export import build_ptouch_csv_bytes


def ptouch_download_name(project, date, extension):
    source = getattr(project, "name", "") or Path(getattr(project, "filename", "KNX_Projekt")).stem
    stem = re.sub(r"[^A-Za-z0-9ÄÖÜäöüß_-]+", "_", str(source)).strip("_-") or "KNX_Projekt"
    safe_date = re.sub(r"[^0-9A-Za-z_-]+", "-", str(date)).strip("-")
    date_part = f"_{safe_date}" if safe_date else ""
    return f"{stem}_PTouch{date_part}.{extension}"


def export_ptouch_project(
    project,
    template_filename,
    output_filename,
    prefix="Firma XY | IBS",
    date="",
    selected_addresses=None,
):
    csv_bytes = build_ptouch_csv_bytes(
        project,
        prefix=prefix,
        date=date,
        selected_addresses=selected_addresses,
    )

    with ZipFile(template_filename, "r") as source:
        try:
            config = json.loads(source.read("config.json").decode("utf-8-sig"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Die P-touch-Vorlage enthält keine gültige config.json.") from error

        csv_name = config.get("CurrentCsv", "")
        lbx_name = config.get("CurrentLbx", "")

        if not csv_name or csv_name not in source.namelist():
            raise ValueError("Die P-touch-Vorlage enthält keine eingebettete CSV-Datenbank.")
        if not lbx_name or lbx_name not in source.namelist():
            raise ValueError("Die P-touch-Vorlage enthält kein gültiges Layout.")

        with ZipFile(output_filename, "w", compression=ZIP_DEFLATED) as target:
            for entry in source.infolist():
                data = csv_bytes if entry.filename == csv_name else source.read(entry.filename)
                target.writestr(entry, data)
