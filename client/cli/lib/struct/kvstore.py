class KVStore:
    def __init__(self):
        self.store = {}

    def ping(self):
        return "PONG"

    def get(self, key):
        return self.store.get(key, None)

    def set(self, key, value):
        if key in self.store:
            self.store[key] = value
            return "OK"
        else:
            return None

    def strln(self, key):
        value = self.store.get(key, None)
        if value is None:
            return None
        return len(value)

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            return "OK"
        return None

    def append(self, key, value):
        if key in self.store:
            if value is None:
                self.store[key] += ""
            else:
                self.store[key] += value
            return "OK"
        else:
            if value is None:
                self.store[key] = ""
            else:
                self.store[key] = str(value)
            return "OK"