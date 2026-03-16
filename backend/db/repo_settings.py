from .connection import get_connection

def save_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        REPLACE INTO settings (key, value) 
        VALUES (?, ?)
    ''', (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        try:
            return row['value']
        except TypeError:
            return row[0]
            
    return None