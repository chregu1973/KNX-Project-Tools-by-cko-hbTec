import csv
from io import StringIO


PTOUCH_FIELDS = [
    "Zeile1",
    "Zeile2",
    "Adresse",
    "Raum",
    "Beschreibung",
    "Seriennummer",
]


def selected_ptouch_devices(project, selected_addresses=None):
    if selected_addresses is None:
        return list(project.devices)

    wanted = {str(address) for address in selected_addresses}
    return [device for device in project.devices if device.address in wanted]


def build_ptouch_csv_bytes(
    project,
    prefix="Firma XY | IBS",
    date="",
    selected_addresses=None,
):
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter=",")
    writer.writerow(PTOUCH_FIELDS)

    for device in selected_ptouch_devices(project, selected_addresses):
        writer.writerow([
            f"{prefix} {date}".strip(),
            device.address,
            device.address,
            device.room,
            device.description,
            device.serial,
        ])

    return output.getvalue().encode("utf-8-sig")


def export_ptouch(
    project,
    filename,
    prefix="Firma XY | IBS",
    date="",
    area="",
    line="",
    selected_addresses=None,
):
    # area und line bleiben für ältere Aufrufe kompatibel. Die neue Oberfläche
    # übergibt eine eindeutige Liste ausgewählter physikalischer Adressen.
    if selected_addresses is None and (area or line):
        selected_addresses = [
            device.address
            for device in project.devices
            if (not area or device.address.startswith(f"{area}."))
            and (not line or device.address.startswith(f"{line}."))
        ]

    data = build_ptouch_csv_bytes(
        project,
        prefix=prefix,
        date=date,
        selected_addresses=selected_addresses,
    )

    with open(filename, "wb") as output:
        output.write(data)
