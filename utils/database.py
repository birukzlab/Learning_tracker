import psycopg2
from psycopg2 import sql

DATABASE_URL = "postgresql://postgres:Ethio#2014@5432/learning_tracker"

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        subject VARCHAR(255) NOT NULL,
        days INTEGER NOT NULL,
        hours_per_day FLOAT NOT NULL,
        total_hours_day FLOAT NOT NULL,
        total_hours_month FLOAT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS timers (
        id SERIAL PRIMARY KEY,
        subject VARCHAR(255) NOT NULL,
        total_hours FLOAT DEFAULT 0,
        daily_hours FLOAT DEFAULT 0,
        rolling_total FLOAT DEFAULT 0
    );
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def add_plan(subject, days, hours_per_day, total_hours_day, total_hours_month):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO plans (subject, days, hours_per_day, total_hours_day, total_hours_month)
    VALUES (%s, %s, %s, %s, %s)
    ''', (subject, days, hours_per_day, total_hours_day, total_hours_month))
    conn.commit()
    cursor.close()
    conn.close()

def get_plans():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM plans')
    plans = cursor.fetchall()
    cursor.close()
    conn.close()
    return plans

def add_timer(subject):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO timers (subject)
    VALUES (%s)
    ON CONFLICT (subject) DO NOTHING
    ''', (subject,))
    conn.commit()
    cursor.close()
    conn.close()

def get_timers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM timers')
    timers = cursor.fetchall()
    cursor.close()
    conn.close()
    return timers

def update_timer(subject, daily_elapsed):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE timers
    SET daily_hours = daily_hours + %s, rolling_total = rolling_total + %s
    WHERE subject = %s
    ''', (daily_elapsed, daily_elapsed, subject))
    conn.commit()
    cursor.close()
    conn.close()

