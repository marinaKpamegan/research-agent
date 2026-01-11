import json
from pathlib import Path
from app.core.config import settings


class SimpleMemory:
    def __init__(self, path: str = None):
        self.path = Path(path or settings.MEMORY_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self):
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, item: dict):
        data = self._read()
        data.append(item)
        self._write(data)

    def all(self):
        return self._read()

    def query(self, predicate):
        return [i for i in self._read() if predicate(i)]
