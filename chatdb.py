import sqlite3
import datetime
from sqlite3 import Error
from ConnectionPool import ConnectionPool


class MessageStore:
    def __init__(self, db_file='messages.db', max_connections=5):
        self.pool = ConnectionPool(db_file, max_connections)

        with self.pool.get_connection() as conn:
            # Create a table to store messages
            conn.execute('''CREATE TABLE IF NOT EXISTS messages
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         role TEXT NOT NULL,
                         content TEXT NOT NULL);''')

            # Check if the created_at column is already present in the table
            cursor = conn.execute('''SELECT count(*) FROM sqlite_master WHERE type='table' AND name='messages' AND sql LIKE '%created_at%';''')
            result = cursor.fetchone()
            created_at_column_exists = (result[0] > 0)
            
            if not created_at_column_exists:
                # Add a new column to store created_at timestamps
                conn.execute('''ALTER TABLE messages ADD COLUMN created_at TIMESTAMP;''')

                # Set the value of the created_at column for existing rows to the current timestamp
                conn.execute('''UPDATE messages SET created_at = CURRENT_TIMESTAMP;''')



    def insert_message(self, role, content):
        with self.pool.get_connection() as conn:
            # Insert a new message into the table
            # get current timestamp in sqlite datetime format
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)", (role, content, created_at))
            conn.commit()

    def get_all_messages(self):
        with self.pool.get_connection() as conn:
            # Retrieve all messages from the table
            cursor = conn.execute("SELECT * FROM messages")
            return cursor.fetchall()

    def get_messages_for_prompt(self, n):
        with self.pool.get_connection() as conn:
            # Retrieve the most recent n messages from the table
            cursor = conn.execute(f"SELECT * FROM messages ORDER BY id DESC LIMIT {n}")
            return cursor.fetchall()[::-1] # Reverse the order of the messages to return them in chronological order
