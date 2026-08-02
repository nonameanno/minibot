import sqlite3
conn = sqlite3.connect('storage/minibot.db')
conn.execute("DELETE FROM metrics WHERE session_id='frontend_test_1'")
conn.commit()
print('deleted', conn.total_changes, 'rows')
conn.close()
