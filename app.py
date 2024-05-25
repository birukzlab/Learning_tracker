'''
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from google_sheets.google_sheets import ensure_sheets_exist, read_plan_data, write_plan_data, read_timer_data, log_daily_time
from postgresql.database import create_plan_entry, get_plan_summary, create_timer_entry, get_timer_summary, delete_plan_entry
from postgresql.sql_connector import get_sql_connection_string
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = get_sql_connection_string()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function to get current week range
def get_current_week():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    return start_of_week, end_of_week

@app.route('/')
def home():
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('You have successfully registered! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check your email and password.')
            return redirect(url_for('login'))
    
    return render_template('login.html', title='Login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contact')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', title='Privacy Policy')

@app.route('/terms')
def terms():
    return render_template('terms.html', title='Terms of Service')

@app.route('/planning', methods=['GET', 'POST'])
@login_required
def planning():
    ensure_sheets_exist()

    if request.method == 'POST':
        subject = request.form['subject']
        number_of_days = int(request.form['number_of_days'])
        number_of_hours_per_day = float(request.form['number_of_hours_per_day'])
        
        # Google Sheets
        total_hours_per_month = number_of_days * number_of_hours_per_day
        google_data = [[subject, number_of_days, number_of_hours_per_day, total_hours_per_month]]
        write_plan_data(google_data)
        
        # PostgreSQL
        create_plan_entry(subject, number_of_days, number_of_hours_per_day)

    # Get current week range
    start_of_week, end_of_week = get_current_week()

    # Fetch Google Sheets data
    google_plan_data = read_plan_data()
    
    # Fetch PostgreSQL data
    postgres_plans = get_plan_summary()

    return render_template('planning.html', 
                           title='Planning', 
                           google_plan_data=google_plan_data, 
                           postgres_plans=postgres_plans, 
                           start_of_week=start_of_week.strftime('%B %d, %Y'), 
                           end_of_week=end_of_week.strftime('%B %d, %Y'))

@app.route('/delete_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    delete_plan_entry(plan_id)
    return redirect(url_for('planning'))

@app.route('/tracker')
@login_required
def tracker():
    # Ensure Google Sheets exist and get data
    google_timer_data = read_timer_data()
    
    # Get PostgreSQL data
    postgres_plans = get_plan_summary()
    postgres_timers = get_timer_summary()

    # Get current week range
    start_of_week, end_of_week = get_current_week()

    # Calculate remaining time for each subject
    subjects = {}
    for plan in postgres_plans:
        subject = plan[1]
        weekly_plan_hours = plan[4]
        tracked_hours = sum(timer[5] for timer in postgres_timers if timer[4] == subject)
        remaining_hours = weekly_plan_hours - tracked_hours
        subjects[subject] = {
            'weekly_plan_hours': weekly_plan_hours,
            'tracked_hours': tracked_hours,
            'remaining_hours': remaining_hours
        }

    return render_template('tracker.html', 
                           title='Daily Time Tracker', 
                           google_timer_data=google_timer_data, 
                           postgres_plans=postgres_plans, 
                           postgres_timers=postgres_timers,
                           subjects=subjects,
                           start_of_week=start_of_week.strftime('%B %d, %Y'), 
                           end_of_week=end_of_week.strftime('%B %d, %Y'),
                           datetime=datetime)

@app.route('/add_plan', methods=['POST'])
@login_required
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
@login_required
def start_timer():
    subject = request.form['subject']
    start_time = datetime.now()
    session['start_time'] = start_time.isoformat()  # Store start time as ISO format string
    session['subject'] = subject
    return redirect(url_for('tracker'))

@app.route('/stop_timer', methods=['POST'])
@login_required
def stop_timer():
    try:
        subject = session.get('subject')
        start_time_str = session.get('start_time')
        if not start_time_str:
            raise Exception("Start time not found in session")
        
        start_time = datetime.fromisoformat(start_time_str)  # Parse ISO format string back to datetime
        end_time = datetime.now()
        number_of_hours_daily = (end_time - start_time).total_seconds() / 3600.0
        day_of_week = start_time.strftime('%A')
        
        # Google Sheets
        log_daily_time(subject, number_of_hours_daily)
        
        # PostgreSQL
        planned_daily_hours = next((plan[3] for plan in get_plan_summary() if plan[1] == subject), 0)
        total_hours = sum(timer[5] for timer in get_timer_summary() if timer[4] == subject) + number_of_hours_daily
        create_timer_entry(day_of_week, subject, start_time, end_time, number_of_hours_daily, planned_daily_hours, total_hours)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return redirect(url_for('tracker'))

if __name__ == '__main__':
    app.run(debug=True)
'''


from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from google_sheets.google_sheets import ensure_sheets_exist, read_plan_data, write_plan_data, read_timer_data, log_daily_time
from postgresql.database import create_plan_entry, get_plan_summary, create_timer_entry, get_timer_summary, delete_plan_entry
from postgresql.sql_connector import get_sql_connection_string
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = get_sql_connection_string()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function to get current week range
def get_current_week():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    return start_of_week, end_of_week

@app.route('/')
def home():
    return render_template('index.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('You have successfully registered! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check your email and password.')
            return redirect(url_for('login'))
    
    return render_template('login.html', title='Login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contact')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', title='Privacy Policy')

@app.route('/terms')
def terms():
    return render_template('terms.html', title='Terms of Service')

@app.route('/planning', methods=['GET', 'POST'])
@login_required
def planning():
    ensure_sheets_exist()

    if request.method == 'POST':
        subject = request.form['subject']
        number_of_days = int(request.form['number_of_days'])
        number_of_hours_per_day = float(request.form['number_of_hours_per_day'])
        
        # Google Sheets
        total_hours_per_month = number_of_days * number_of_hours_per_day
        google_data = [[subject, number_of_days, number_of_hours_per_day, total_hours_per_month]]
        write_plan_data(google_data)
        
        # PostgreSQL
        create_plan_entry(subject, number_of_days, number_of_hours_per_day)

    # Get current week range
    start_of_week, end_of_week = get_current_week()

    # Fetch Google Sheets data
    google_plan_data = read_plan_data()
    
    # Fetch PostgreSQL data
    postgres_plans = get_plan_summary()

    return render_template('planning.html', 
                           title='Planning', 
                           google_plan_data=google_plan_data, 
                           postgres_plans=postgres_plans, 
                           start_of_week=start_of_week.strftime('%B %d, %Y'), 
                           end_of_week=end_of_week.strftime('%B %d, %Y'))

@app.route('/delete_plan/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    delete_plan_entry(plan_id)
    return redirect(url_for('planning'))

@app.route('/tracker')
@login_required
def tracker():
    # Ensure Google Sheets exist and get data
    google_timer_data = read_timer_data()
    
    # Get PostgreSQL data
    postgres_plans = get_plan_summary()
    postgres_timers = get_timer_summary()

    # Get current week range
    start_of_week, end_of_week = get_current_week()

    # Calculate remaining time for each subject
    subjects = {}
    for plan in postgres_plans:
        subject = plan[1]
        weekly_plan_hours = plan[4]
        tracked_hours = sum(timer[5] for timer in postgres_timers if timer[4] == subject)
        remaining_hours = weekly_plan_hours - tracked_hours
        subjects[subject] = {
            'weekly_plan_hours': weekly_plan_hours,
            'tracked_hours': tracked_hours,
            'remaining_hours': remaining_hours
        }

    return render_template('tracker.html', 
                           title='Daily Time Tracker', 
                           google_timer_data=google_timer_data, 
                           postgres_plans=postgres_plans, 
                           postgres_timers=postgres_timers,
                           subjects=subjects,
                           start_of_week=start_of_week.strftime('%B %d, %Y'), 
                           end_of_week=end_of_week.strftime('%B %d, %Y'),
                           datetime=datetime)

@app.route('/add_plan', methods=['POST'])
@login_required
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
@login_required
def start_timer():
    subject = request.form['subject']
    start_time = datetime.now()
    session['start_time'] = start_time.isoformat()  # Store start time as ISO format string
    session['subject'] = subject
    return redirect(url_for('tracker'))

@app.route('/stop_timer', methods=['POST'])
@login_required
def stop_timer():
    try:
        subject = session.get('subject')
        start_time_str = session.get('start_time')
        if not start_time_str:
            raise Exception("Start time not found in session")
        
        start_time = datetime.fromisoformat(start_time_str)  # Parse ISO format string back to datetime
        end_time = datetime.now()
        number_of_hours_daily = (end_time - start_time).total_seconds() / 3600.0
        day_of_week = start_time.strftime('%A')
        
        # Google Sheets
        log_daily_time(subject, number_of_hours_daily)
        
        # PostgreSQL
        planned_daily_hours = next((plan[3] for plan in get_plan_summary() if plan[1] == subject), 0)
        total_hours = sum(timer[5] for timer in get_timer_summary() if timer[4] == subject) + number_of_hours_daily
        create_timer_entry(day_of_week, subject, start_time, end_time, number_of_hours_daily, planned_daily_hours, total_hours)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return redirect(url_for('tracker'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)

if __name__ == '__main__':
    app.run(debug=True)




















