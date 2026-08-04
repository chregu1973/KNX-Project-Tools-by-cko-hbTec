from pathlib import Path
import xml.etree.ElementTree as ET

from .models import Project, Device
from .xml_reader import XMLReader


class KNXProjectParser:

    def __init__(self, filename, password=None):

        self.filename = filename
        self.password = password

        self.project = Project()

        self.project.filename = Path(filename).name

        self.manufacturers = {}


    def load(self):

        reader = XMLReader(self.filename, password=self.password)

        try:
            self._read_project_information(reader)

            self._read_manufacturers(reader)

            for filename, root in reader.find_all(".xml"):

                if not filename.startswith("P-"):
                    continue

                if filename.endswith("project.xml"):
                    continue

                try:
                    self._parse_installation(root)

                except Exception as ex:
                    print(f"Parserfehler in {filename}: {ex}")
        finally:
            reader.close()

        self.project.devices.sort(
            key=lambda d: tuple(int(x) for x in d.address.split("."))
        )

        return self.project


    def _read_project_information(self, reader):

        root = reader.find("project.xml")

        if root is None:
            return

        self.project.tool_version = root.attrib.get("ToolVersion", "")

        if self.project.tool_version.startswith("6"):
            self.project.ets_version = "ETS6"

        elif self.project.tool_version.startswith("5"):
            self.project.ets_version = "ETS5"

        else:
            self.project.ets_version = self.project.tool_version

        info = root.find(".//{*}ProjectInformation")

        if info is not None:
            self.project.name = info.attrib.get("Name", "")


    def _parse_installation(self, root):

        devices = {}

        for area in root.findall(".//{*}Topology/{*}Area"):

            area_address = area.attrib.get("Address", "")
            area_name = area.attrib.get("Name", "")
            if area_address == "0":
                self.project.backbone = True

            if area_address != "0":
                if area_address not in self.project.areas:
                    self.project.areas.append(area_address)

            for line in area.findall("./{*}Line"):

                line_address = line.attrib.get("Address", "")
                line_name = line.attrib.get("Name", "")

                line_id = f"{area_address}.{line_address}"

                if not (area_address == "0" and line_address == "0"):
                    if line_id not in self.project.lines:
                        self.project.lines.append(line_id)

                for di in line.findall(".//{*}DeviceInstance"):

                    dev_address = di.attrib.get("Address", "")
                    dev_id = di.attrib.get("Id", "")

                    if not dev_address or not dev_id:
                        continue

                    device = Device()

                    device.address = (
                        f"{int(area_address)}."
                        f"{int(line_address)}."
                        f"{int(dev_address)}"
                    )

                    device.name = di.attrib.get("Name", "")
                    device.description = di.attrib.get("Description", "")
                    device.comment = di.attrib.get("Comment", "")

                    device.serial = di.attrib.get("SerialNumber", "")

                    device.product = di.attrib.get("ProductRefId", "")
                    device.hardware = di.attrib.get("Hardware2ProgramRefId", "")
                    device.manufacturer = self._manufacturer_from_ref(device.product)

                    device.area = area_name
                    device.line = line_name

                    devices[dev_id] = device

        self._read_locations(root, devices)

        known = {d.address for d in self.project.devices}

        for device in devices.values():

            if device.address not in known:
                self.project.devices.append(device)
    def _read_locations(self, root, devices):

        locations = root.find(".//{*}Locations")

        if locations is None:
            return

        def walk(space, path, info):

            name = space.attrib.get("Name", "")
            typ = space.attrib.get("Type", "")

            new_path = list(path)

            if name:
                new_path.append(name)

            current = dict(info)

            if typ == "Building":
                current["building"] = name

            elif typ == "Floor":
                current["floor"] = name

            elif typ in ("Room", "DistributionBoard", "Cabinet"):
                current["room"] = name

            for ref in space.findall("./{*}DeviceInstanceRef"):

                refid = ref.attrib.get("RefId", "")

                if refid not in devices:
                    continue

                dev = devices[refid]

                dev.building = current.get("building", "")
                dev.floor = current.get("floor", "")
                dev.room = current.get("room", "")
                dev.location = " / ".join(new_path)

            for child in space.findall("./{*}Space"):
                walk(child, new_path, current)

        for space in locations.findall("./{*}Space"):
            walk(space, [], {})


    def get_device(self, address):

        for device in self.project.devices:

            if device.address == address:
                return device

        return None


    def get_devices_by_room(self, room):

        result = []

        for device in self.project.devices:

            if device.room == room:
                result.append(device)

        return result


    def get_devices_by_line(self, line):

        result = []

        for device in self.project.devices:

            if device.line == line:
                result.append(device)

        return result


    def get_devices_by_building(self, building):

        result = []

        for device in self.project.devices:

            if device.building == building:
                result.append(device)

        return result


    def get_unique_buildings(self):

        return sorted({
            d.building
            for d in self.project.devices
            if d.building
        })


    def get_unique_floors(self):

        return sorted({
            d.floor
            for d in self.project.devices
            if d.floor
        })


    def get_unique_rooms(self):

        return sorted({
            d.room
            for d in self.project.devices
            if d.room
        })


    def get_unique_lines(self):

        return sorted({
            d.line
            for d in self.project.devices
            if d.line
        })


    def get_unique_areas(self):

        return sorted({
            d.area
            for d in self.project.devices
            if d.area
        })
    def summary(self):

        manufacturers = {}

        for device in self.project.devices:

            if device.manufacturer:

                manufacturers.setdefault(device.manufacturer, 0)

                manufacturers[device.manufacturer] += 1

        return {

            "project": self.project.name,

            "ets": self.project.ets_version,

            "tool_version": self.project.tool_version,

            "devices": len(self.project.devices),

            "areas": len(self.project.areas),

            "lines": len(self.project.lines),

            "manufacturers": manufacturers

        }


    def get_devices(self):

        return self.project.devices


    def search(self, text):

        text = text.lower()

        result = []

        for device in self.project.devices:

            if (
                text in device.address.lower()
                or text in device.name.lower()
                or text in device.description.lower()
                or text in device.comment.lower()
                or text in device.room.lower()
                or text in device.location.lower()
            ):

                result.append(device)

        return result
    def _read_manufacturers(self, reader):

        root = reader.find("knx_master.xml")

        if root is None:
            return

        for manufacturer in root.findall(".//{*}Manufacturer"):

            mid = manufacturer.attrib.get("Id", "")
            name = manufacturer.attrib.get("Name", "")

            if mid and name:
                self.manufacturers[mid] = name


    def _manufacturer_from_ref(self, ref):

        if not ref:
            return ""

        manufacturer_id = ref.split("_")[0]

        return self.manufacturers.get(manufacturer_id, manufacturer_id)


    def manufacturer_statistics(self):

        result = {}

        for device in self.project.devices:

            if not device.manufacturer:
                continue

            result.setdefault(device.manufacturer, 0)
            result[device.manufacturer] += 1

        return dict(sorted(result.items()))


    def sort_by_address(self):

        self.project.devices.sort(
            key=lambda d: tuple(int(x) for x in d.address.split("."))
        )


    def sort_by_room(self):

        self.project.devices.sort(
            key=lambda d: (
                d.building,
                d.floor,
                d.room,
                d.address
            )
        )


    def sort_by_name(self):

        self.project.devices.sort(
            key=lambda d: (
                d.name,
                d.address
            )
        )


    def sort_by_description(self):

        self.project.devices.sort(
            key=lambda d: (
                d.description,
                d.address
            )
        )
