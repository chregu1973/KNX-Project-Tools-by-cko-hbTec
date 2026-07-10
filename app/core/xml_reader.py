import zipfile
import xml.etree.ElementTree as ET


class XMLReader:

    def __init__(self, filename):
        self.filename = filename
        self.archive = zipfile.ZipFile(filename, "r")

    def list_files(self):
        return self.archive.namelist()

    def read_xml(self, filename):
        return ET.fromstring(self.archive.read(filename))

    def find(self, suffix):
        for name in self.archive.namelist():
            if name.endswith(suffix):
                return self.read_xml(name)
        return None

    def find_all(self, suffix):
        result = []

        for name in self.archive.namelist():
            if name.endswith(suffix):
                result.append((name, self.read_xml(name)))

        return result

    def close(self):
        self.archive.close()
