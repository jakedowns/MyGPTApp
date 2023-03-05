import sqlite3

class MessageStore:
    def __init__(self, db_file='messages.db'):
        # Connect to the database (creates a new database if it doesn't exist)
        self.conn = sqlite3.connect(db_file)
        # Create a table to store messages
        self.conn.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     role TEXT NOT NULL,
                     content TEXT NOT NULL);''')
    
    def insert_message(self, role, content):
        # Insert a new message into the table
        self.conn.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
        self.conn.commit()
    
    def get_all_messages(self):
        # Retrieve all messages from the table
        cursor = self.conn.execute("SELECT * FROM messages")
        return cursor.fetchall()
    
    def get_messages_for_prompt(self, n):
        # Retrieve the most recent n messages from the table
        cursor = self.conn.execute(f"SELECT * FROM messages ORDER BY id DESC LIMIT {n}")
        return cursor.fetchall()[::-1] # Reverse the order of the messages to return them in chronological order
