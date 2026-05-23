from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session,send_file,make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from flask import session
from email.mime.text import MIMEText
from flask_login import UserMixin
from twilio.rest import Client
import datetime
import mysql.connector
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Time
Base = declarative_base()
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import csv
from email.mime.multipart import MIMEMultipart
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email
from sendgrid.helpers.mail import To
from sendgrid.helpers.mail import Content
import os
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from mysql.connector import Error
from flask import jsonify

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(_BASE_DIR, 'templates'),
    static_folder=os.path.join(_BASE_DIR, 'static'),
)

login_manager = LoginManager()
login_manager.init_app(app)

mysql_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'childr_db'),
}

_db_user = mysql_config['user']
_db_password = mysql_config['password']
_db_host = mysql_config['host']
_db_name = mysql_config['database']

# MySQL connection configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqlconnector://{_db_user}:{_db_password}@{_db_host}/{_db_name}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', '7373')

#flask login def
db = SQLAlchemy(app)


class User:
    def __init__(self, id, username, email, number, name=None, admin_id=None, hospital_id=None):
        self.id = id
        self.username = username
        self.email = email
        self.number = number
        self.name = name  
        self.hospital_id = hospital_id 

    def is_authenticated(self):
        return True  

    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False 

    def get_id(self):
        return str(self.id) 

def is_admin_authenticated(username, password):
    return False  

class Admin(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_id(self):
        return self.username

class Admin(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

class Hospital(db.Model):
    __tablename__ = 'hospital'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pending')

    # Define relationship with Child
    children = db.relationship('Child', backref='hospital', lazy=True)

class Parent(db.Model):
    __tablename__ = 'parent'

    id = db.Column(db.Integer, primary_key=True)
    children = db.relationship('Child', back_populates='parent')
    appointments = db.relationship('Appointment', back_populates='parent', lazy='dynamic')

class Child(db.Model):
    __tablename__ = 'child'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    vaccination = db.Column(db.String(100))

    # Define foreign key relationship with Hospital
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)

    # Define relationship with Parent
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))
    parent = db.relationship('Parent', back_populates='children')

class Appointment(db.Model):
    __tablename__ = 'appointment'

    id = db.Column(db.Integer, primary_key=True)
    appointment_date = db.Column(db.String)
    appointment_time = db.Column(db.String)
    status = db.Column(db.String)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'))
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'))  # Foreign key to Child model

    # Define relationship with Child model
    child = db.relationship("Child")

    # Define relationship with Parent model
    parent = db.relationship("Parent")

    def __init__(self, appointment_date, appointment_time, status, hospital_id, parent_id, child_id):
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.status = status
        self.hospital_id = hospital_id
        self.parent_id = parent_id
        self.child_id = child_id

@login_manager.user_loader
def load_user(user_id):
    return Admin(user_id, None)

@login_manager.user_loader
def load_user(user_id):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, number, password FROM parent WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        username, email, number, password = user_data
        if is_admin_authenticated(username, password):  # Authenticate admin user
            return Admin(username, password)  # Pass both username and password to Admin constructor
        else:
            return User(user_id, username, email=email, number=number)
    return None

@staticmethod
def is_admin(username, password):
    return True 

# Routes for regular users
@app.route('/')
def index():
    admin_id = get_admin_id()
    return render_template('index.html', admin_id=admin_id, current_user=current_user)

def get_admin_id():
    admin_id = ...  # Retrieve the admin ID from your database or wherever it's stored
    return admin_id

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        number = request.form['number']
        username = request.form['username']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO parent (username, number, email, password) VALUES (%s, %s, %s, %s)", (username, number, email, password))
            conn.commit()
            flash('Registration successful', 'success')
        except mysql.connector.Error as e:
            flash('Error occurred during registration', 'danger')
            print("MySQL error:", e)
        finally:
            if 'conn' in locals():
                conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM parent WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            conn.close()
            if user_data:
                user_id, stored_password = user_data
                if password == stored_password:
                    flash('Login successful', 'success')
                    user = User(user_id, username, "", "")  # Placeholder for user details
                    login_user(user)
                    return redirect(url_for('parent_dashboard'))
            flash('Invalid username or password', 'danger')
        except mysql.connector.Error as e:
            flash('Error occurred during login: {}'.format(e), 'danger')
            print("MySQL error:", e)

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))
def parent_dashboard():
    if current_user.is_authenticated:
        user_details = {
            'name': current_user.username,
            'email': current_user.email,
            'number': getattr(current_user, 'number', None)  # Handle if 'number' is not available
        }
        return render_template('parent_dashboard.html', user_details=user_details)
    else:
        # Handle case when user is not authenticated
        return "User is not authenticated."
@app.route('/parent_dashboard', methods=['GET', 'POST'])
@login_required
def parent_dashboard():
    user_details = {
        'name': current_user.username,
        'email':current_user.email,  
        'number': current_user.number  
    }
    return render_template('parent_dashboard.html', user_details=user_details)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form['oldPassword']
        new_password = request.form['newPassword']
        confirm_password = request.form['confirmPassword']

        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM parent WHERE id = %s", (current_user.id,))
        user_data = cursor.fetchone()
        if user_data:
            current_password = user_data[0]
            if old_password == current_password:
                if new_password == confirm_password:
                    cursor.execute("UPDATE parent SET password = %s WHERE id = %s", (new_password, current_user.id))
                    conn.commit()
                    flash('Password changed successfully', 'success')
                    return jsonify(redirect=url_for('parent_dashboard'), delay=5)
                else:
                    flash('New password and confirm password do not match', 'danger')
            else:
                flash('Old password is incorrect', 'danger')

        cursor.close()
        conn.close()
        return jsonify(error='Password change failed'), 400

    user_details = {
        'email': ''  # Placeholder for user email
    }
    return render_template('change_password.html', user_details=user_details)


@app.route('/manage_child_data', methods=['GET', 'POST'])
def manage_child_data():
    selected_hospital = None
    if request.method == 'POST':
        try:
            # Retrieve form data
            child_id = request.form.get('child_id')
            name = request.form['name']
            gender = request.form['gender']
            age = request.form.get('age')
            dob = request.form['dob']
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            vaccination = request.form.get('vaccination')
            
            # Assign hospital_id
            hospital_id = int(request.form.get('hospital_id'))  # Get selected hospital ID

            if child_id:
                # Update existing child data
                child = Child.query.get(child_id)
                if child:
                    child.name = name
                    child.gender = gender
                    child.dob = dob
                    child.age = age
                    child.weight = weight
                    child.height = height
                    child.vaccination = vaccination
                    child.hospital_id = hospital_id  # Assigning hospital ID
                    db.session.commit()
                    flash('Child data updated successfully', 'success')
                else:
                    flash('Child not found', 'danger')
            else:
                # Add new child data
                new_child = Child(
                    name=name,
                    gender=gender,
                    dob=dob,
                    age=age,
                    weight=weight,
                    height=height,
                    vaccination=vaccination,
                    hospital_id=hospital_id  # Assigning hospital ID
                )
                # Assign parent ID to the child
                new_child.parent_id = current_user.id  # Assuming current_user holds the logged-in parent's data
                db.session.add(new_child)
                db.session.commit()
                flash('Child data saved successfully', 'success')
        except Exception as e:
            flash('Error occurred while saving child data', 'danger')
            print("Error:", e)

        return redirect(url_for('manage_child_data'))

    children_data = Child.query.filter_by(parent_id=current_user.id).all()
    hospitals = Hospital.query.all()
    return render_template('manage_child_data.html', children_data=children_data, hospitals=hospitals, selected_hospital=selected_hospital)



@app.route('/delete_child', methods=['POST'])
def delete_child():
    if request.method == 'POST':
        child_id = request.form.get('child_id')
        try:
            child = Child.query.get(child_id)
            if child:
                db.session.delete(child)
                db.session.commit()
                flash('Child deleted successfully', 'success')
            else:
                flash('Child not found', 'danger')
        except Exception as e:
            flash('Error occurred while deleting child', 'danger')
            print("Error:", e)

        return redirect(url_for('manage_child_data'))
    
def fetch_child_id(child_name):
    # Assuming you're using SQLAlchemy
    child = Child.query.filter_by(name=child_name).first()
    if child:
        return child.name
    else:
        return None




@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if request.method == 'POST':
        try:
            child_id = int(request.form['child_name'])  # Assuming child_id is passed from the form
            appointment_date = request.form['appointment_date']
            appointment_time = request.form['appointment_time']

            # Fetch the child object from the database
            child = Child.query.filter_by(id=child_id).first()

            if child:
                # Insert appointment data into the database
                appointment = Appointment(
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status="pending",
                    hospital_id=1,
                    parent_id=current_user.id,
                    child_id=child_id
                )

                db.session.add(appointment)
                db.session.commit()

                # Send appointment reminder to the parent
                appointment_message = f"Reminder: Your appointment is scheduled for {appointment_date} at {appointment_time}."
              #  send_sms(current_user.number, appointment_message)  # Correct function call

                flash('Appointment booked successfully. A reminder has been sent to your phone.', 'success')
            else:
                flash('Child not found', 'danger')
        except Exception as e:
            flash(f'Error occurred while booking appointment: {str(e)}', 'danger')
            print("Error:", e)

        return redirect(url_for('book_appointment'))

    # Fetch children data for dropdown
    children_data = Child.query.with_entities(Child.id, Child.name).filter_by(parent_id=current_user.id).all()
    return render_template('book_appointment.html', children_data=children_data)


@app.route('/view_appointments', methods=['GET'])
@login_required
def view_appointments():
    try:
        # Fetch appointment data along with child name, vaccination name, and hospital name
        appointments_data = db.session.query(
            Appointment.id,
            Child.name.label('child_name'),
            Child.vaccination,
            Appointment.appointment_date,
            Appointment.appointment_time,
            Appointment.status,
            Hospital.name.label('hospital_name')  
        ).join(
            Child, Appointment.child_id == Child.id
        ).join(
            Hospital, Appointment.hospital_id == Hospital.id  # Join with Hospital table
        ).filter(
            Appointment.parent_id == current_user.id
        ).all()
    except Exception as e:
        flash('Error occurred while fetching appointment data', 'danger')
        print("Error:", e)
        appointments_data = []

    return render_template('view_appointments.html', appointments_data=appointments_data)


account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '')
client = Client(account_sid, auth_token) if (account_sid and auth_token) else None

# Function to send SMS reminder
def send_sms(receiver_number, message):
    try:
        if client is None:
            raise RuntimeError('Twilio is not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.')
        if not twilio_from_number:
            raise RuntimeError('Twilio from-number not configured. Set TWILIO_FROM_NUMBER.')
        # Send SMS message
        message = client.messages.create(
            body=message,
            from_=twilio_from_number,
            to=receiver_number
        )
        print("SMS sent successfully! SID:", message.sid)
    except Exception as e:
        print("Failed to send SMS:", e)

# Endpoint to trigger SMS appointment reminders
@app.route('/send_appointment_reminders', methods=['POST'])
def send_appointment_reminders():
    try:
        # Connect to MySQL database
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        # Calculate the date for sending reminders (two minutes before appointment)
        reminder_date = datetime.datetime.now() + datetime.timedelta(days=7)
        # Fetch appointments scheduled for the reminder date
        cursor.execute("SELECT parent_id, appointment_date FROM appointment WHERE appointment_date = %s", (reminder_date,))
        appointments_data = cursor.fetchall()

        for appointment in appointments_data:
            parent_id, appointment_date = appointment
            
            # Fetch parent's phone number from database
            cursor.execute("SELECT number FROM parent WHERE id = %s", (parent_id,))
            parent_phone_number = cursor.fetchone()[0]
            
            # Prepare SMS reminder message
            sms_message = f"Reminder: Your child's vaccination appointment is scheduled for {appointment_date}. Please make sure to attend the appointment."
            
            # Send SMS reminder
            send_sms(parent_phone_number, sms_message)
            
    except mysql.connector.Error as e:
        print("MySQL error:", e)
    finally:
        if 'conn' in locals():
            conn.close()

    return 'Appointment reminders sent successfully'

##########################-------------Admin-----------------------################


def is_admin_authenticated(username, password):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM admins WHERE username = %s AND password = %s", (username, password))
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0  # If result[0] > 0, authentication succeeds
    except mysql.connector.Error as e:
        print("MySQL error:", e)
        return False  # Return False in case of any error


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM admins WHERE username = %s", (username,))
            admin_data = cursor.fetchone()
            conn.close()
            if admin_data:
                admin_id, stored_password = admin_data
                if password == stored_password:
                    flash('Login successful', 'success')
                    # Log in the admin
                    admin = Admin(admin_id, username)
                    login_user(admin)
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Incorrect password', 'danger')
            else:
                flash('Username does not exist', 'danger')
        except mysql.connector.Error as e:
            flash('Error occurred during login: {}'.format(e), 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # You can add code here to fetch and display dashboard data
    return render_template('admin_dashboard.html')

# Route to view hospitals
def fetch_hospital_from_database():
    
    hospitals_data = []  # Placeholder for fetched data
    return hospitals_data

def perform_application_action(hospital_id, action):
    pass  # Placeholder for actual implementation

def fetch_hospital_from_database():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM hospital")
        hospitals_data = cursor.fetchall()
        conn.close()
        return hospitals_data
    except mysql.connector.Error as e:
        print("MySQL error:", e)
        return []

# Route for viewing hospitals
@app.route('/view_hospitals')
def view_hospitals():
    hospitals_data = fetch_hospital_from_database()
    return render_template('view_hospitals.html', hospitals_data=hospitals_data)

# Route for approving or rejecting a hospital

@app.route('/approve_reject_hospital', methods=['POST'])
def approve_reject_hospital():
    if request.method == 'POST':
        hospital_id = request.form.get('hospital_id')
        action = request.form.get('action')
        
        # Check if both hospital_id and action are provided
        if not hospital_id or not action:
            flash('Invalid request. Please provide hospital ID and action.', 'danger')
            return redirect(url_for('view_hospitals'))
        
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            if action == 'approve':
                # Update the status to 'approved' for the hospital with given ID
                cursor.execute("UPDATE hospital SET status = 'approved' WHERE id = %s", (hospital_id,))
                flash('Hospital approved successfully', 'success')
            elif action == 'reject':
                # Update the status to 'rejected' for the hospital with given ID
                cursor.execute("UPDATE hospital SET status = 'rejected' WHERE id = %s", (hospital_id,))
                flash('Hospital rejected successfully', 'success')
            elif action == 'delete':
                # Delete the hospital data from the database
                cursor.execute("DELETE FROM hospitals WHERE id = %s", (hospital_id,))
                flash('Hospital deleted successfully', 'success')
                
            # Commit the transaction
            conn.commit()
        except mysql.connector.Error as e:
            flash('Error occurred while processing hospital request', 'danger')
            print("MySQL error:", e)
        finally:
            # Close the connection
            if 'conn' in locals():
                conn.close()
    
    # Redirect to the view_hospitals route after processing the request
    return redirect(url_for('view_hospitals'))


# @app.route('/admin/view_child_data')
# def view_child_data():
#     try:
#         print("Attempting to connect to the database...")
#         conn = mysql.connector.connect(**mysql_config)
#         print("Connected to the database successfully!")

#         cursor = conn.cursor(dictionary=True)
#         cursor.execute("""
#             SELECT 
#                 c.id AS child_id,
#                 c.name AS child_name,
#                 c.age,
#                 c.dob,
#                 c.gender,
#                 c.height,
#                 c.weight,
#                 c.vaccination AS vaccine_name,
#                 a.appointment_date,
#                 a.appointment_time,
#                 a.status,
#                 h.name AS hospital_name  -- Include hospital name
#             FROM 
#                 child c
#             LEFT JOIN 
#                 appointment a ON c.id = a.child_id
#             LEFT JOIN
#                 hospital h ON c.hospital_id = h.id;  -- Join with hospital table
#         """)
#         children_data = cursor.fetchall()
#         conn.close()
        
#         print("Retrieved child data:", children_data)  # Check the retrieved data
        
#         return render_template('view_child_data.html', children=children_data)
#     except mysql.connector.Error as e:
#         # Handle database error
#         print("MySQL error:", e)
#         return "Database error occurred. Please try again later."

@app.route('/admin/view_child_data')
def view_child_data():
    try:
        print("Attempting to connect to the database...")
        conn = mysql.connector.connect(**mysql_config)
        print("Connected to the database successfully!")

        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                c.id AS child_id,
                c.name AS child_name,
                c.age,
                c.dob,
                c.gender,
                c.height,
                c.weight,
                c.vaccination AS vaccine_name,
                h.name AS hospital_name  -- Include hospital name
            FROM 
                child c
            LEFT JOIN 
                hospital h ON c.hospital_id = h.id;
        """)
        children_data = cursor.fetchall()
        conn.close()
        
        print("Retrieved child data:", children_data)  # Check the retrieved data
        
        return render_template('view_child_data.html', children=children_data)
    except mysql.connector.Error as e:
        # Handle database error
        print("MySQL error:", e)
        return "Database error occurred. Please try again later."

def fetch_appointment_data():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                c.name AS child_name,
                c.vaccination AS vaccine_name,
                a.appointment_date AS appointment_date,
                a.appointment_time AS appointment_time,
                a.status AS status
            FROM 
                child c
            LEFT JOIN 
                appointment a ON c.id = a.child_id;
        """)
        appointment_data = cursor.fetchall()
        conn.close()
        return appointment_data
    except mysql.connector.Error as e:
        print("MySQL error:", e)
        return None  # Return None to indicate failure
    
@app.route('/admin/admin_view_appointments')
def admin_view_appointments():
    user_details = {'name': 'Admin'}
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.id AS appointment_id,
                c.name AS child_name,
                c.vaccination AS vaccine_name,
                a.appointment_date,
                a.appointment_time,
                a.status
            FROM 
                appointment a
            LEFT JOIN 
                child c ON a.child_id = c.id;
        """)
        
        appointments_data = cursor.fetchall()
    except mysql.connector.Error as e:
        flash('Error occurred while fetching appointment data', 'danger')
        print("MySQL error:", e)
        appointments_data = []
    finally:
        if 'conn' in locals():
            conn.close()

    return render_template('admin_view_appointments.html', appointments_data=appointments_data, user_details=user_details)

# Route to handle export/save action for appointment data
import io

@app.route('/admin/export_appointment_data', methods=['GET'])
def export_appointment_data():
    try:
        # Fetch appointment data from the database
        appointments_data = fetch_appointment_data()

        # Check if data was fetched successfully
        if appointments_data is None:
            raise Exception("Failed to fetch appointment data from the database")

        # Define the filename for the exported CSV file
        filename = 'appointment_data.csv'

        # Create a StringIO object to hold CSV data
        csv_data = io.StringIO()

        # Write appointment data to the StringIO object as CSV
        writer = csv.DictWriter(csv_data, fieldnames=appointments_data[0].keys())
        writer.writeheader()
        for appointment in appointments_data:
            writer.writerow(appointment)

        # Create a response object containing the CSV data
        response = make_response(csv_data.getvalue())
        
        # Set the appropriate headers for CSV file download
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=' + filename

        return response
    except Exception as e:
        # Handle errors if any
        return str(e), 500  # Return the error

#---------------------------Hospitial------------------------#

# Route for registering a hospital
@app.route('/register_hospital', methods=['GET', 'POST'])
def register_hospital():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        status = "pending"  # Set the initial status to "pending"
        
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO hospital (name, email, password, address, status) VALUES (%s, %s, %s, %s, %s)",
                           (name, email, password, address, status))
            conn.commit()
            flash('Hospital registered successfully', 'success')
            return redirect(url_for('hospital_login'))
        except mysql.connector.Error as e:
            flash('Error occurred while registering hospital', 'danger')
            print("MySQL error:", e)
        finally:
            if 'conn' in locals():
                conn.close()
    return render_template('register_hospital.html')

@app.route('/hospital_login', methods=['GET', 'POST'])
def hospital_login():
    if request.method == 'POST':
        email = request.form['email']  
        password = request.form['password']
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM hospital WHERE email = %s", (email,))
            hospital = cursor.fetchone()
            if hospital:
                if hospital['password'] == password:
                    if hospital['status'] == 'approved':
                        session['hospital_id'] = hospital['id']  # Set hospital_id in the session
                        session['hospital_name'] = hospital['name']
                        flash('Login successful', 'success')
                        return redirect(url_for('hospital_dashboard'))
                    elif hospital['status'] == 'pending':
                        flash('Permission denied. Your account is pending approval.', 'danger')
                    else:
                        flash('Permission denied. Your account has been rejected.', 'danger')
                else:
                    flash('Invalid email or password', 'danger')
            else:
                flash('Invalid email or password', 'danger')
        except mysql.connector.Error as e:
            flash('Error occurred during login', 'danger')
            print("MySQL error:", e)
        finally:
            if 'conn' in locals():
                conn.close()
    return render_template('hospital_login.html')




def fetch_appointments(filter_date=None, hospital_id=None):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        # Construct the SQL query
        query = """
            SELECT 
                a.id AS appointment_id,  
                c.id AS child_id,
                c.name AS child_name,
                c.age,
                c.dob,
                c.gender,
                c.height,
                c.weight,
                c.vaccination AS vaccine_name,
                a.appointment_date,
                a.appointment_time,
                a.status,
                h.name AS hospital_name,
                p.email,  -- Add email field
                p.number  -- Add number field
            FROM 
                child c
            LEFT JOIN 
                appointment a ON c.id = a.child_id
            LEFT JOIN 
                hospital h ON c.hospital_id = h.id
            LEFT JOIN
                parent p ON c.parent_id = p.id  -- Join with parent table to get email and number
            WHERE 1=1
        """
        
        # Add filter conditions
        params = ()
        if filter_date:
            query += " AND a.appointment_date = %s"
            params += (filter_date,)

        if hospital_id:
            query += " AND c.hospital_id = %s"
            params += (hospital_id,)

        # Execute the query with parameters
        cursor.execute(query, params)

        appointments = cursor.fetchall()
        conn.close()

        return appointments
    except mysql.connector.Error as e:
        print("MySQL error:", e)
        return None



# Route for hospital dashboard
@app.route('/hospital_dashboard')
def hospital_dashboard():
    if 'hospital_name' in session:
        # User is authenticated, render the hospital dashboard
        return render_template('hospital_dashboard.html')
    else:
        # User is not authenticated, redirect to the hospital login page
        flash('Please log in to access the hospital dashboard.', 'danger')
        return redirect(url_for('hospital_login'))
# Route for hospital view appointments


@app.route('/hospital_view_appointments', methods=['GET', 'POST'])
def hospital_view_appointments():
    if request.method == 'POST':
        filter_date = request.form.get('filter_date')
        hospital_id = session.get('hospital_id')
        appointments = fetch_appointments(filter_date=filter_date, hospital_id=hospital_id)

        if appointments is None:
            appointments = []

        return render_template('hospital_view_appointments.html', appointments=appointments)

    else:
        hospital_id = session.get('hospital_id')
        appointments = fetch_appointments(hospital_id=hospital_id)

        if appointments is None:
            appointments = []

        return render_template('hospital_view_appointments.html', appointments=appointments)


# Route to update appointment status
@app.route('/update_appointment_status/<int:appointment_id>', methods=['POST'])
def update_appointment_status(appointment_id):
    if request.method == 'POST':
        new_status = request.form['new_status']
        try:
            conn = mysql.connector.connect(**mysql_config)
            cursor = conn.cursor()
            cursor.execute("UPDATE appointment SET status = %s WHERE id = %s", (new_status, appointment_id))
            conn.commit()

            if new_status == 'Approved':
                # Fetch parent's email and phone number from the database based on the appointment
                cursor.execute("SELECT email, number FROM parent WHERE id = (SELECT parent_id FROM appointment WHERE id = %s)", (appointment_id,))
                parent_data = cursor.fetchone()
                parent_email, parent_number = parent_data[0], parent_data[1]

                # Send SMS notification
                sms_message = 'Your child\'s vaccine appointment has been approved.'
                # send_sms_notification(parent_number, sms_message)

                # Send email notification using SendGrid
                email_message = 'Your child\'s vaccine appointment has been approved. Please check your email for more details.'
                #send_email_notification(parent_email, email_message)

            flash('Appointment status updated successfully', 'success')
        except mysql.connector.Error as e:
            flash('Error occurred while updating appointment status', 'danger')
            print("MySQL error:", e)
        finally:
            if 'conn' in locals():
                conn.close()
    return redirect(url_for('hospital_view_appointments'))


@app.route('/hospital_logout')
def hospital_logout():
    # Clear hospital session data
    session.pop('hospital_id', None)
    session.pop('hospital_name', None)
    
    # Redirect to the login page
    return redirect(url_for('hospital_login'))

if __name__ == '__main__':
    app.run(debug=True)