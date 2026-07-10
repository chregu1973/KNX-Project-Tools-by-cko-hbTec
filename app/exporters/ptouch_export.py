import csv

def export_ptouch(
    project,
    filename,
    prefix="hbTec | IBS",
    date="",
    area="",
    line=""
):

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:

        writer = csv.writer(f, delimiter=",")

        writer.writerow([
            "Zeile1",
            "Zeile2",
            "Adresse",
            "Raum",
            "Beschreibung",
            "Seriennummer"
        ])

        for d in project.devices:

            if area and not d.address.startswith(f"{area}."):
                continue

            if line and not d.address.startswith(f"{line}."):
                continue

            writer.writerow([
                f"{prefix} {date}".strip(),
                d.address,
                d.address,
                d.room,
                d.description,
                d.serial
            ])
