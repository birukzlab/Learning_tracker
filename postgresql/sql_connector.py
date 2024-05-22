import psycopg2

__cnx = None

def get_sql_connection():
    global __cnx
    if __cnx is None or __cnx.closed:
        __cnx = psycopg2.connect(
            user='postgres',
            password='Ethio#2014',
            host='localhost',
            port=5432,
            database='LearnT'
        )
    return __cnx



