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
