import base64
import hashlib
import io
import json
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET

import pyzipper


class ProjectPasswordRequired(ValueError):
    """Das ETS-Projekt ist geschützt, aber es wurde kein Passwort übergeben."""


class InvalidProjectPassword(ValueError):
    """Das angegebene ETS-Projektpasswort ist nicht korrekt."""


class InvalidKNXProject(ValueError):
    """Die Datei ist kein lesbares ETS-Projekt."""


class XMLReader:

    def __init__(self, filename, password=None):
        self.filename = filename
        self.archive = None
        self.project_archive = None
        self.project_archive_file = None
        self.project_prefix = ""

        try:
            self.archive = zipfile.ZipFile(filename, "r")
            self._open_protected_project(password)
        except (ProjectPasswordRequired, InvalidProjectPassword, InvalidKNXProject):
            self.close()
            raise
        except (OSError, zipfile.BadZipFile) as error:
            self.close()
            raise InvalidKNXProject(
                "Die Datei ist kein gültiges ETS-Projekt oder ist beschädigt."
            ) from error

    def _open_protected_project(self, password):
        info_name = next(
            (
                name
                for name in self.archive.namelist()
                if name.startswith("P-") and name.endswith(".info")
            ),
            None,
        )

        if not info_name:
            return

        try:
            project_info = json.loads(self.archive.read(info_name))
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as error:
            raise InvalidKNXProject(
                "Die Projektinformationen konnten nicht gelesen werden."
            ) from error

        if not project_info.get("IsPasswordProtected", False):
            return

        if not password:
            raise ProjectPasswordRequired(
                "Dieses ETS-Projekt ist passwortgeschützt. Bitte das Projektpasswort eingeben."
            )

        self.project_prefix = info_name[:-len(".info")]
        nested_name = f"{self.project_prefix}.zip"

        if nested_name not in self.archive.namelist():
            raise InvalidKNXProject(
                "Der geschützte Projektteil fehlt im ETS-Projekt."
            )

        # Der verschlüsselte innere Projektteil bleibt verschlüsselt, falls er
        # bei großen Projekten vorübergehend auf die Festplatte ausgelagert wird.
        self.project_archive_file = tempfile.SpooledTemporaryFile(
            max_size=16 * 1024 * 1024
        )

        with self.archive.open(nested_name) as source:
            shutil.copyfileobj(source, self.project_archive_file)

        self.project_archive_file.seek(0)

        try:
            self.project_archive = pyzipper.AESZipFile(
                self.project_archive_file,
                "r",
            )

            # ETS5 verwendet das eingegebene Projektpasswort direkt für das
            # innere ZipCrypto-Archiv. ETS6 verschlüsselt das innere Archiv
            # hingegen mit AES und leitet dafür ein separates ZIP-Passwort ab.
            encrypted_entry = next(
                (
                    entry
                    for entry in self.project_archive.infolist()
                    if not entry.is_dir()
                ),
                None,
            )
            uses_ets6_aes = bool(
                encrypted_entry
                and getattr(encrypted_entry, "wz_aes_version", None)
            )

            if uses_ets6_aes:
                zip_password = self._derive_ets6_zip_password(password)
            else:
                zip_password = password.encode("utf-8")

            self.project_archive.setpassword(zip_password)

            test_name = next(
                (
                    name
                    for name in self.project_archive.namelist()
                    if name.endswith("0.xml") or name.endswith("project.xml")
                ),
                None,
            )

            if not test_name:
                raise InvalidKNXProject(
                    "Im geschützten Projektteil wurden keine ETS-Projektdaten gefunden."
                )

            # Ein kleiner Lesezugriff validiert das Passwort, bevor der Parser
            # das Projekt verarbeitet. Das Passwort wird nirgends gespeichert.
            with self.project_archive.open(test_name) as test_file:
                test_file.read(1)

        except InvalidKNXProject:
            raise
        except (RuntimeError, NotImplementedError, ValueError) as error:
            raise InvalidProjectPassword(
                "Das Projektpasswort ist nicht korrekt."
            ) from error

    @staticmethod
    def _derive_ets6_zip_password(password):
        """Das von ETS6 aus dem Projektpasswort abgeleitete ZIP-Passwort."""
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-16-le"),
            b"21.project.ets.knx.org",
            65536,
            dklen=32,
        )
        return base64.b64encode(derived_key)

    def _entries(self):
        for name in self.archive.namelist():
            yield name, self.archive, name

        if self.project_archive is not None:
            for name in self.project_archive.namelist():
                public_name = f"{self.project_prefix}/{name}"
                yield public_name, self.project_archive, name

    def list_files(self):
        return [public_name for public_name, _, _ in self._entries()]

    def read_xml(self, filename):
        for public_name, archive, archive_name in self._entries():
            if public_name == filename:
                return ET.fromstring(archive.read(archive_name))

        raise KeyError(filename)

    def find(self, suffix):
        for public_name, archive, archive_name in self._entries():
            if public_name.endswith(suffix):
                return ET.fromstring(archive.read(archive_name))
        return None

    def find_all(self, suffix):
        result = []

        for public_name, archive, archive_name in self._entries():
            if public_name.endswith(suffix):
                result.append(
                    (public_name, ET.fromstring(archive.read(archive_name)))
                )

        return result

    def close(self):
        if self.project_archive is not None:
            self.project_archive.close()
            self.project_archive = None

        if self.project_archive_file is not None:
            self.project_archive_file.close()
            self.project_archive_file = None

        if self.archive is not None:
            self.archive.close()
            self.archive = None
