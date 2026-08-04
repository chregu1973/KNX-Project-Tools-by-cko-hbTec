import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_ROOT))

TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="knx-label-sessions-"))
os.environ["DATA_ROOT"] = str(TEST_DATA_ROOT)
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["SESSION_CLEANUP_ENABLED"] = "false"
os.environ["SESSION_COOKIE_SECURE"] = "false"

from app import app  # noqa: E402
from core.models import Device, Project  # noqa: E402
from core.project_manager import ProjectManager  # noqa: E402


def example_project(name, address):
    return Project(
        filename=f"{name}.knxproj",
        name=name,
        ets_version="ETS6",
        devices=[Device(address=address, name=f"Gerät {name}")],
    )


class SessionIsolationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)
        TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
        app.config.update(TESTING=True)

    @staticmethod
    def session_id(client):
        with client.session_transaction() as browser_session:
            return browser_session["session_id"]

    def test_two_browsers_keep_projects_separate(self):
        browser_a = app.test_client()
        browser_b = app.test_client()

        browser_a.get("/")
        browser_b.get("/")
        session_a = self.session_id(browser_a)
        session_b = self.session_id(browser_b)

        self.assertNotEqual(session_a, session_b)

        ProjectManager.save(session_a, example_project("Projekt A", "1.1.10"))
        ProjectManager.save(session_b, example_project("Projekt B", "2.2.20"))

        page_a = browser_a.get("/").get_data(as_text=True)
        page_b = browser_b.get("/").get_data(as_text=True)

        self.assertIn("Projekt A", page_a)
        self.assertNotIn("Projekt B", page_a)
        self.assertIn("Projekt B", page_b)
        self.assertNotIn("Projekt A", page_b)

    def test_manual_delete_only_removes_own_session(self):
        browser_a = app.test_client()
        browser_b = app.test_client()

        browser_a.get("/")
        browser_b.get("/")
        session_a = self.session_id(browser_a)
        session_b = self.session_id(browser_b)

        ProjectManager.save(session_a, example_project("Projekt A", "1.1.10"))
        ProjectManager.save(session_b, example_project("Projekt B", "2.2.20"))

        response = browser_a.post("/project/delete", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(ProjectManager.load(session_a))
        self.assertEqual(ProjectManager.load(session_b).name, "Projekt B")

    def test_cleanup_removes_only_expired_sessions(self):
        expired_id = "a" * 43
        active_id = "b" * 43

        ProjectManager.save(expired_id, example_project("Alt", "1.1.1"))
        ProjectManager.save(active_id, example_project("Aktiv", "1.1.2"))

        now = time.time()
        expired_marker = ProjectManager.activity_file(expired_id)
        os.utime(expired_marker, (now - 7200, now - 7200))

        removed = ProjectManager.cleanup_expired(3600, now=now)

        self.assertEqual(removed, [expired_id])
        self.assertFalse(ProjectManager.session_dir(expired_id, create=False).exists())
        self.assertTrue(ProjectManager.session_dir(active_id, create=False).exists())

    def test_export_paths_are_session_local(self):
        session_a = "c" * 43
        session_b = "d" * 43

        export_a = ProjectManager.export_path(session_a, "export.csv")
        export_b = ProjectManager.export_path(session_b, "export.csv")

        self.assertNotEqual(export_a, export_b)
        self.assertEqual(export_a.parent.name, "exports")
        self.assertEqual(export_b.parent.name, "exports")

    def test_existing_export_routes_use_current_browser_session(self):
        browser = app.test_client()
        other_browser = app.test_client()
        browser.get("/")
        other_browser.get("/")
        session_id = self.session_id(browser)

        project = example_project("Exporttest", "1.1.10")
        project.devices[0].room = "Technik"
        project.devices[0].location = "Gebäude / UG / Technik"
        project.devices[0].description = "KNX Gerät"
        ProjectManager.save(session_id, project)

        csv_response = browser.get("/export/csv")
        ptouch_response = browser.post(
            "/export/ptouch",
            data={"device": "1.1.10", "prefix": "Test", "date": "08-2026"},
        )
        dymo_response = browser.post(
            "/export/dymo-pdf",
            data={"device": "1.1.10", "address": "on", "room": "on"},
        )
        a4_response = browser.post(
            "/export/labels-pdf",
            data={
                "device": "1.1.10",
                "address": "on",
                "room": "on",
                "width": "70",
                "height": "36",
                "cols": "3",
                "rows": "8",
                "margin_left": "0",
                "margin_top": "4.5",
                "gap_x": "0",
                "gap_y": "0",
                "start_position": "1",
            },
        )

        self.assertEqual(csv_response.status_code, 200)
        self.assertIn(b"1.1.10", csv_response.data)
        self.assertEqual(ptouch_response.status_code, 200)
        self.assertIn(b"1.1.10", ptouch_response.data)
        self.assertEqual(dymo_response.status_code, 200)
        self.assertTrue(dymo_response.data.startswith(b"%PDF"))
        self.assertEqual(a4_response.status_code, 200)
        self.assertTrue(a4_response.data.startswith(b"%PDF"))

        csv_response.close()
        ptouch_response.close()
        dymo_response.close()
        a4_response.close()

        other_response = other_browser.get("/export/csv")
        self.assertEqual(other_response.status_code, 302)
        self.assertTrue(other_response.location.endswith("/"))
        other_response.close()


if __name__ == "__main__":
    unittest.main()
