import os
import pickle
import re
import shutil
import time
from pathlib import Path


DATA_ROOT = Path(os.environ.get("DATA_ROOT", "/data"))
SESSIONS_ROOT = DATA_ROOT / "sessions"
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")


class InvalidSessionId(ValueError):
    """Die Sitzungskennung ist nicht für einen Dateipfad geeignet."""


class ProjectManager:
    """Speichert Projekt- und Exportdaten strikt getrennt je Browser-Sitzung."""

    @staticmethod
    def is_valid_session_id(session_id):
        return bool(
            isinstance(session_id, str)
            and SESSION_ID_PATTERN.fullmatch(session_id)
        )

    @classmethod
    def session_dir(cls, session_id, create=True):
        if not cls.is_valid_session_id(session_id):
            raise InvalidSessionId("Ungültige Sitzungskennung.")

        directory = SESSIONS_ROOT / session_id
        if create:
            directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def upload_dir(cls, session_id, create=True):
        directory = cls.session_dir(session_id, create=create) / "uploads"
        if create:
            directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def export_dir(cls, session_id, create=True):
        directory = cls.session_dir(session_id, create=create) / "exports"
        if create:
            directory.mkdir(parents=True, exist_ok=True)
        return directory

    @classmethod
    def export_path(cls, session_id, filename):
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename:
            raise ValueError("Ungültiger Exportdateiname.")
        return cls.export_dir(session_id) / safe_name

    @classmethod
    def cache_file(cls, session_id):
        return cls.session_dir(session_id) / "current_project.pkl"

    @classmethod
    def activity_file(cls, session_id):
        return cls.session_dir(session_id) / ".last_activity"

    @classmethod
    def touch(cls, session_id):
        """Aktualisiert die Inaktivitätsfrist ohne Projekt- oder Passwortdaten."""
        marker = cls.activity_file(session_id)
        marker.touch(exist_ok=True)

    @classmethod
    def save(cls, session_id, project):
        cache_file = cls.cache_file(session_id)
        temporary_file = cache_file.with_suffix(".tmp")

        with temporary_file.open("wb") as file_handle:
            pickle.dump(project, file_handle)

        os.replace(temporary_file, cache_file)
        cls.touch(session_id)

    @classmethod
    def load(cls, session_id):
        cache_file = cls.cache_file(session_id)

        if not cache_file.exists():
            return None

        with cache_file.open("rb") as file_handle:
            project = pickle.load(file_handle)

        cls.touch(session_id)
        return project

    @classmethod
    def clear_exports(cls, session_id):
        export_directory = cls.export_dir(session_id, create=False)
        if export_directory.exists():
            shutil.rmtree(export_directory)

    @classmethod
    def clear(cls, session_id):
        """Löscht ausschließlich die Daten der angegebenen Sitzung."""
        directory = cls.session_dir(session_id, create=False)
        if directory.exists():
            shutil.rmtree(directory)

    @classmethod
    def cleanup_expired(cls, max_age_seconds, now=None):
        """Entfernt Sitzungen, die länger als die konfigurierte Frist inaktiv sind."""
        if max_age_seconds <= 0:
            raise ValueError("Die Aufbewahrungsfrist muss größer als 0 sein.")

        current_time = time.time() if now is None else float(now)
        removed = []

        if not SESSIONS_ROOT.exists():
            return removed

        for directory in SESSIONS_ROOT.iterdir():
            if directory.is_symlink() or not directory.is_dir():
                continue
            if not cls.is_valid_session_id(directory.name):
                continue

            marker = directory / ".last_activity"
            try:
                last_activity = (
                    marker.stat().st_mtime
                    if marker.exists()
                    else directory.stat().st_mtime
                )
            except FileNotFoundError:
                continue

            if current_time - last_activity < max_age_seconds:
                continue

            try:
                shutil.rmtree(directory)
                removed.append(directory.name)
            except FileNotFoundError:
                continue

        return removed
