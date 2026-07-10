import csv


def export_devices(project, filename):

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:

        writer = csv.writer(f, delimiter=";")

        writer.writerow([
            "Physikalische Adresse",
            "Gebäude",
            "Etage",
            "Raum",
            "Standort",
            "Beschreibung",
            "Kommentar",
            "Seriennummer"
        ])

        for d in project.devices:

            writer.writerow([
                d.address,
                d.building,
                d.floor,
                d.room,
                d.location,
                d.description,
                d.comment,
                d.serial
            ])
