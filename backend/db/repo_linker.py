from db.connection import get_connection

def assign_trainings_to_matches(links_dict: dict):
    conn = get_connection()
    cursor = conn.cursor()
    data_to_update = [(m_id, t_id) for t_id, m_id in links_dict.items()]

    cursor.executemany("""
        UPDATE treningi 
        SET mecz_id = ? 
        WHERE aktywnosc_id = ?
    """, data_to_update)
    
    conn.commit()
    conn.close()


