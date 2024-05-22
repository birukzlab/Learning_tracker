'''

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from google_sheets.google_sheets import ensure_sheets_exist, read_plan_data, write_plan_data, read_timer_data, log_daily_time
from postgresql.database import create_plan_entry, get_plan_summary, create_timer_entry, get_timer_summary
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    # Ensure Google Sheets exist and get data
    ensure_sheets_exist()
    google_plan_data = read_plan_data()
    google_timer_data = read_timer_data()
    
    # Get PostgreSQL data
    postgres_plans = get_plan_summary()
    postgres_timers = get_timer_summary()

    return render_template('index.html', 
                           google_plan_data=google_plan_data, 
                           google_timer_data=google_timer_data,
                           postgres_plans=postgres_plans, 
                           postgres_timers=postgres_timers)

@app.route('/add_plan', methods=['POST'])
def add_plan():
    subject = request.form['subject']
    number_of_days = int(request.form['number_of_days'])
    number_of_hours_per_day = float(request.form['number_of_hours_per_day'])
    
    # Google Sheets
    total_hours_per_month = number_of_days * number_of_hours_per_day
    google_data = [[subject, number_of_days, number_of_hours_per_day, total_hours_per_month]]
    write_plan_data(google_data)
    
    # PostgreSQL
    create_plan_entry(subject, number_of_days, number_of_hours_per_day)
    
    return redirect(url_for('index'))

@app.route('/start_timer', methods=['POST'])
def start_timer():
    subject = request.form['subject']
    start_time = datetime.now()
    session['start_time'] = start_time.isoformat()  # Store start time as ISO format string
    session['subject'] = subject
    return redirect(url_for('index'))

@app.route('/stop_timer', methods=['POST'])
def stop_timer():
    try:
        subject = session.get('subject')
        start_time_str = session.get('start_time')
        if not start_time_str:
            raise Exception("Start time not found in session")
        
        start_time = datetime.fromisoformat(start_time_str)  # Parse ISO format string back to datetime
        end_time = datetime.now()
        number_of_hours_daily = (end_time - start_time).total_seconds() / 3600.0
        
        # Google Sheets
        log_daily_time(subject, number_of_hours_daily)
        
        # PostgreSQL
        planned_daily_hours = next((plan[4] for plan in get_plan_summary() if plan[2] == subject), 0)
        total_hours = sum(timer[5] for timer in get_timer_summary() if timer[4] == subject) + number_of_hours_daily
        create_timer_entry(subject, start_time, end_time, number_of_hours_daily, planned_daily_hours, total_hours)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
'''
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from google_sheets.google_sheets import ensure_sheets_exist, read_plan_data, write_plan_data, read_timer_data, log_daily_time
from postgresql.database import create_plan_entry, get_plan_summary, create_timer_entry, get_timer_summary
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def home():
    return render_template('index.html', title='Home')

@app.route('/planning')
def planning():
    # Ensure Google Sheets exist and get data
    ensure_sheets_exist()
    google_plan_data = read_plan_data()
    
    # Get PostgreSQL data
    postgres_plans = get_plan_summary()

    return render_template('planning.html', 
                           title='Planning', 
                           google_plan_data=google_plan_data, 
                           postgres_plans=postgres_plans)

@app.route('/tracker')
def tracker():
    # Ensure Google Sheets exist and get data
    google_timer_data = read_timer_data()
    
    # Get PostgreSQL data
    postgres_plans = get_plan_summary()
    postgres_timers = get_timer_summary()

    return render_template('tracker.html', 
                           title='Daily Time Tracker', 
                           google_timer_data=google_timer_data, 
                           postgres_plans=postgres_plans, 
                           postgres_timers=postgres_timers)

@app.route('/add_plan', methods=['POST'])
def add_plan():
    subject = request.form['subject']
    number_of_days = int(request.form['number_of_days'])
    number_of_hours_per_day = float(request.form['number_of_hours_per_day'])
    
    # Google Sheets
    total_hours_per_month = number_of_days * number_of_hours_per_day
    google_data = [[subject, number_of_days, number_of_hours_per_day, total_hours_per_month]]
    write_plan_data(google_data)
    
    # PostgreSQL
    create_plan_entry(subject, number_of_days, number_of_hours_per_day)
    
    return redirect(url_for('planning'))

@app.route('/start_timer', methods=['POST'])
def start_timer():
    subject = request.form['subject']
    start_time = datetime.now()
    session['start_time'] = start_time.isoformat()  # Store start time as ISO format string
    session['subject'] = subject
    return redirect(url_for('tracker'))

@app.route('/stop_timer', methods=['POST'])
def stop_timer():
    try:
        subject = session.get('subject')
        start_time_str = session.get('start_time')
        if not start_time_str:
            raise Exception("Start time not found in session")
        
        start_time = datetime.fromisoformat(start_time_str)  # Parse ISO format string back to datetime
        end_time = datetime.now()
        number_of_hours_daily = (end_time - start_time).total_seconds() / 3600.0
        
        # Google Sheets
        log_daily_time(subject, number_of_hours_daily)
        
        # PostgreSQL
        planned_daily_hours = next((plan[4] for plan in get_plan_summary() if plan[2] == subject), 0)
        total_hours = sum(timer[5] for timer in get_timer_summary() if timer[4] == subject) + number_of_hours_daily
        create_timer_entry(subject, start_time, end_time, number_of_hours_daily, planned_daily_hours, total_hours)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return redirect(url_for('tracker'))

if __name__ == '__main__':
    app.run(debug=True)







