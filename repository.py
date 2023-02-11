import json
import os


class KeyValRepository:
    def __init__(self, key):
        self.key = key
        self.data = dict()

        self.load()

    def load(self):
        file_path = os.path.join("data", f"{self.key}.json")
        try:
            with open(file_path, "r") as f:
                self.data = json.load(f)
        except Exception as e:
            print(e)

    def save(self):
        file_path = os.path.join("data", f"{self.key}.json")
        with open(file_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def get_and_set(self, key, value):
        old_value = self.get(key)
        self.set(key, value)
        return old_value

    def compute_if_absent(self, key, func):
        if key not in self.data:
            self.data[key] = func()
        return self.data[key]

    def delete(self, key):
        del self.data[key]
