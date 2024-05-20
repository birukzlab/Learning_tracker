from flask import Flask, render_template, request, redirect, url_for, jsonify
from utils.google_sheets import ensure_sheets_exist, read_plan_data, write_plan_data, read_timer_data, log_daily_time
import logging

app = Flask(__name__)

@app.route('/')
def index():
    ensure_sheets_exist()  # Ensure both sheets exist
    plan_data = read_plan_data()
    timer_data = read_timer_data()
    return render_template('index.html', plan_data=plan_data, timer_data=timer_data)

@app.route('/add', methods=['POST'])
def add_subject():
    subjects = request.form.getlist('subject')
    days = request.form.getlist('days')
    hours_per_day = request.form.getlist('hours_per_day')
    new_data = []
    for subject, day, hour_per_day in zip(subjects, days, hours_per_day):
        day = int(day)
        hour_per_day = float(hour_per_day)
        total_hours_day = hour_per_day * day
        total_hours_month = hour_per_day * 30  # assuming a month has 30 days
        new_data.append([subject, day, hour_per_day, total_hours_day, total_hours_month])
    write_plan_data(new_data)

    # Copy subjects to the timer sheet if they do not already exist
    timer_data = read_timer_data()
    timer_subjects = [row[0] for row in timer_data]
    new_timer_data = []
    for subject in subjects:
        if subject not in timer_subjects:
            new_timer_data.append([subject, '', '0', '0'])
    write_plan_data(new_timer_data)
    
    return redirect(url_for('index'))

@app.route('/log_time', methods=['POST'])
def log_time_route():
    data = request.get_json()
    subject = data.get('subject')
    daily_elapsed = data.get('dailyElapsed')
    success = log_daily_time(subject, daily_elapsed)
    if not success:
        logging.error(f"Failed to log time for subject {subject} with elapsed time {daily_elapsed}")
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(debug=True)





