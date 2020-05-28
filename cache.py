import pickle
import threading
import time
from dataclasses import dataclass
from typing import List


@dataclass
class Record:
    value: List[str]
    time: int
    ttl: int


class Cache:
    def __init__(self, file: str):
        try:
            self._cache = pickle.load(open(file, 'rb'))
        except:
            self._cache = dict()
        self.update()
        self.file = file

        threading.Thread(target=self._run_gc).start()

    def put(self, key, value: List[str], ttl=10):
        self._cache[key] = Record(value, int(time.time()), ttl)

    def get(self, key) -> Record:
        return self._cache[key]

    def update(self):
        items = list(self._cache.items())
        for key, record in items:
            if time.time() - record.time > record.ttl:
                self._cache.pop(key)

    def contains(self, key):
        return key in self._cache.keys()

    def save(self):
        with open(self.file, 'wb') as file:
            pickle.dump(self._cache, file)

    def _run_gc(self):
        while True:
            time.sleep(10)
            self.update()
            self.save()

    def __del__(self):
        self.save()
