import os
import shutil


class TempManager:

    @staticmethod
    def create():
        path = os.path.join(os.getcwd(), "temp")
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def cleanup():
        path = os.path.join(os.getcwd(), "temp")
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
