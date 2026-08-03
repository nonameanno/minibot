import sqlite3
conn = sqlite3.connect('storage/minibot.db')
conn.execute("DELETE FROM messages WHERE session_id='debug_001'")
conn.commit()
print('deleted', conn.total_changes, 'rows')
conn.close()
