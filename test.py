from postgresql.sql_connector import get_sql_connection_string
import psycopg2

def test_connection():
    conn = psycopg2.connect(get_sql_connection_string())
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

if __name__ == "__main__":
    result = test_connection()
    print(f"Test result: {result}")
