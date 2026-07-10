from dataclasses import dataclass, field
from typing import List


@dataclass
class Device:
    address: str = ""

    name: str = ""
    description: str = ""
    comment: str = ""

    serial: str = ""

    manufacturer: str = ""
    product_name: str = ""
    product: str = ""
    hardware: str = ""

    building: str = ""
    floor: str = ""
    room: str = ""

    location: str = ""

    area: str = ""
    line: str = ""


@dataclass
class Project:
    filename: str = ""

    name: str = ""

    ets_version: str = ""
    tool_version: str = ""

    areas: List[str] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)
    backbone: bool = False

    devices: List[Device] = field(default_factory=list)

    @property
    def device_count(self):
        return len(self.devices)

    @property
    def area_count(self):
        return len(self.areas)

    @property
    def line_count(self):
        return len(self.lines)

    @property
    def room_count(self):
        return len({
            d.room
            for d in self.devices
            if d.room
        })

    @property
    def building_count(self):
        return len({
            d.building
            for d in self.devices
            if d.building
        })
