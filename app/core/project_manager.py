import os
import pickle

CACHE_FILE = "/data/current_project.pkl"


class ProjectManager:

    @staticmethod
    def save(project):

        os.makedirs("/data", exist_ok=True)

        with open(CACHE_FILE, "wb") as f:
            pickle.dump(project, f)

    @staticmethod
    def load():

        if not os.path.exists(CACHE_FILE):
            return None

        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)

    @staticmethod
    def clear():

        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
