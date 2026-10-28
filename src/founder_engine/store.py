"""Storage adapters. The rest of the code only uses `Store`.

- SQLiteStore: a single local file, for testing and for running on a laptop.
- FirestoreStore: for Cloud Run (Cloud Run's disk is wiped on restart).
Add a Postgres adapter here if needed; nothing else changes.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from typing import Iterable, TypeVar

from .models import Record

R = TypeVar("R", bound=Record)


class Store:
    def put(self, record: Record) -> None:
        raise NotImplementedError

    def get_raw(self, collection: str, id: str) -> dict | None:
        raise NotImplementedError

    def all_raw(self, collection: str) -> Iterable[dict]:
        raise NotImplementedError

    # typed helpers -------------------------------------------------------
    def get(self, cls: type[R], id: str) -> R | None:
        d = self.get_raw(cls.collection, id)
        return cls.from_dict(d) if d else None

    def find(self, cls: type[R], **filters) -> list[R]:
        out = []
        for d in self.all_raw(cls.collection):
            if all(d.get(k) == v for k, v in filters.items()):
                out.append(cls.from_dict(d))
        return sorted(out, key=lambda r: getattr(r, "created_at", ""))


class SQLiteStore(Store):
    def __init__(self, path: str = ":memory:"):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS records ("
                " collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL,"
                " PRIMARY KEY (collection, id))"
            )
            self._conn.commit()

    def put(self, record: Record) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO records (collection, id, data) VALUES (?, ?, ?)"
                " ON CONFLICT (collection, id) DO UPDATE SET data = excluded.data",
                (record.collection, record.id, json.dumps(record.to_dict())),
            )
            self._conn.commit()

    def get_raw(self, collection: str, id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM records WHERE collection = ? AND id = ?", (collection, id)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def all_raw(self, collection: str) -> Iterable[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT data FROM records WHERE collection = ? ORDER BY rowid", (collection,)
            ).fetchall()
        return [json.loads(r[0]) for r in rows]


class FirestoreStore(Store):
    """Needs `pip install google-cloud-firestore` and a GCP project."""

    def __init__(self, project: str = "", prefix: str = "fe_"):
        from google.cloud import firestore  # imported lazily: optional dependency

        self._db = firestore.Client(project=project or None)
        self._prefix = prefix

    def _col(self, collection: str):
        return self._db.collection(self._prefix + collection)

    def put(self, record: Record) -> None:
        self._col(record.collection).document(record.id).set(record.to_dict())

    def get_raw(self, collection: str, id: str) -> dict | None:
        snap = self._col(collection).document(id).get()
        return snap.to_dict() if snap.exists else None

    def all_raw(self, collection: str) -> Iterable[dict]:
        return [s.to_dict() for s in self._col(collection).stream()]


def make_store(settings) -> Store:
    if settings.storage == "firestore":
        return FirestoreStore(project=settings.gcp_project)
    return SQLiteStore(settings.sqlite_path)
