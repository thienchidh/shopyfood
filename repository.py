class KeyValRepository:
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = dict()

        self.load()

    def load(self):
        pass

    def save(self):
        pass

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
