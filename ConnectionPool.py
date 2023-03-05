import sqlite3
from queue import Queue
from threading import Lock

class ConnectionPool:
    def __init__(self, db_file, max_connections=5):
        self.db_file = db_file
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = Lock()

    def _create_connection(self):
        return sqlite3.connect(self.db_file)

    def get_connection(self):
        with self.lock:
            if self.connections.empty():
                connection = self._create_connection()
            else:
                connection = self.connections.get()

        return connection

    def return_connection(self, connection):
        with self.lock:
            if self.connections.full():
                connection.close()
            else:
                self.connections.put(connection)

    def close_all_connections(self):
        with self.lock:
            while not self.connections.empty():
                connection = self.connections.get()
                connection.close()