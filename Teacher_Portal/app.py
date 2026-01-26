from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
import math  # ✅ ADDED for distance calculation

app = Flask(__name__)
app.secret_key = "supersecretkey123"

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

DB = "attendance.db"

# ---------------- DB HELPER ----------------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    if not os.path.exists(DB_PATH):
        print("Creating database...")
        conn = get_db_connection()
       
        conn.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT)''')
       
        conn.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            year TEXT,
            branch TEXT,
            email TEXT,
            phone TEXT,
            password TEXT NOT NULL DEFAULT 'student123')''')
       
        conn.execute('''CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            subject_code TEXT,
            year TEXT,
            branch TEXT,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id))''')
       
        conn.execute('''CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            UNIQUE(student_id, subject_id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id))''')
       
        conn.execute('''CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_by INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (marked_by) REFERENCES teachers(id))''')
       
        # ✅ ADDED - Temporary table to store student locations
        conn.execute('''CREATE TABLE IF NOT EXISTS student_temp_locations (
            student_id INTEGER PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id))''')
       
        # ✅ ADDED - Active attendance sessions
        conn.execute('''CREATE TABLE IF NOT EXISTS active_attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            teacher_latitude REAL NOT NULL,
            teacher_longitude REAL NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id))''')
                # Update student location first

       
        try:
            conn.execute('''INSERT INTO teachers (name, email, password, phone)
                VALUES ('Dr. Sharma', 'teacher@college.com', 'teacher123', '9876543210')''')
            conn.execute('''INSERT INTO students (name, roll_no, year, branch, email, password)
                VALUES ('Rahul Kumar', '2021001', '3rd Year', 'CSE', 'rahul@student.com', 'student123')''')
            conn.execute('''INSERT INTO students (name, roll_no, year, branch, email, password)
                VALUES ('Priya Sharma', '2021002', '3rd Year', 'CSE', 'priya@student.com', 'student123')''')
            conn.execute('''INSERT INTO subjects (teacher_id, subject_name, subject_code, year, branch)
                VALUES (1, 'Data Structures', 'CS301', '3rd Year', 'CSE')''')
            conn.execute('INSERT INTO enrollments (student_id, subject_id) VALUES (1, 1)')
            conn.execute('INSERT INTO enrollments (student_id, subject_id) VALUES (2, 1)')
            conn.execute('''INSERT INTO attendance (student_id, subject_id, date, status, marked_by)
                VALUES (1, 1, '2024-01-15', 'Present', 1)''')
            conn.execute('''INSERT INTO attendance (student_id, subject_id, date, status, marked_by)
                VALUES (1, 1, '2024-01-16', 'Present', 1)''')
            conn.execute('''INSERT INTO attendance (student_id, subject_id, date, status, marked_by)
                VALUES (1, 1, '2024-01-17', 'Absent', 1)''')
            conn.commit()
            print("✓ Database initialized!")
           
        except sqlite3.IntegrityError:
            print("Sample data exists.")
        conn.close()


# ========== HOME ==========
@app.route('/')
def home_page():
    return render_template("index.html")



# ========== TEACHER LOGIN ========== ✅ LOCATION ADDED
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        latitude = request.form.get('latitude')    # ✅ ADDED
        longitude = request.form.get('longitude')  # ✅ ADDED
       
        if not email or not password:
            error = "Please enter both email and password"
        else:
            try:
                conn = get_db_connection()
                teacher = conn.execute("SELECT * FROM teachers WHERE email=? AND password=?",
                    (email, password)).fetchone()
                conn.close()
               
                if teacher:
                    session['teacher_id'] = teacher['id']
                    session['teacher_name'] = teacher['name']
                   
                    # ✅ ADDED - Store location in session
                    if latitude and longitude:
                        session['teacher_latitude'] = float(latitude)
                        session['teacher_longitude'] = float(longitude)
                        print(f"📍 Teacher Location: {latitude}, {longitude}")
                   
                    flash(f"Welcome back, {teacher['name']}!", "success")
                    return redirect(url_for('teacher_dashboard'))
                else:
                    error = "Invalid email or password."
            except Exception as e:
                error = f"Database error: {str(e)}"
    return render_template("teacher_login.html", error=error)

# ✅ LOCATION ADDED - Pass location to template
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    try:
        conn = get_db_connection()
        teacher = conn.execute("SELECT * FROM teachers WHERE id=?", (session['teacher_id'],)).fetchone()
        subjects = conn.execute("SELECT * FROM subjects WHERE teacher_id=?", (session['teacher_id'],)).fetchall()
        conn.close()
       
        # ✅ ADDED - Create location object for template
        teacher_location = {
            'latitude': session.get('teacher_latitude', 0),
            'longitude': session.get('teacher_longitude', 0)
        }
       
        return render_template("teacher.html", teacher=teacher, subjects=subjects, teacher_location=teacher_location)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_login'))

# ========== ADD SUBJECT ==========
@app.route('/add_subject_form')
def add_subject_form():
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    try:
        conn = get_db_connection()
        teacher = conn.execute("SELECT * FROM teachers WHERE id=?", (session['teacher_id'],)).fetchone()
        conn.close()
        return render_template("add_subject.html", teacher=teacher)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_dashboard'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    subject_name = request.form.get('subject_name', '').strip()
    subject_code = request.form.get('subject_code', '').strip()
    year = request.form.get('year', '').strip()
    branch = request.form.get('branch', '').strip()
   
    if not subject_name or not year or not branch:
        flash("Please fill all required fields", "error")
        return redirect(url_for('add_subject_form'))
   
    try:
        conn = get_db_connection()
        conn.execute('''INSERT INTO subjects (teacher_id, subject_name, subject_code, year, branch)
            VALUES (?, ?, ?, ?, ?)''', (session['teacher_id'], subject_name, subject_code, year, branch))
        conn.commit()
        conn.close()
        flash(f"Subject '{subject_name}' added successfully!", "success")
        return redirect(url_for('teacher_dashboard'))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('add_subject_form'))

# ========== ADD STUDENT ==========
@app.route('/add_student_form')
def add_student_form():
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    try:
        conn = get_db_connection()
        subjects = conn.execute("SELECT * FROM subjects WHERE teacher_id=?", (session['teacher_id'],)).fetchall()
        conn.close()
        return render_template("add_student.html", subjects=subjects)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_dashboard'))

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    if request.method == 'GET':
        try:
            conn = get_db_connection()
            subjects = conn.execute("SELECT * FROM subjects WHERE teacher_id=?", (session['teacher_id'],)).fetchall()
            conn.close()
            return render_template("add_student.html", subjects=subjects)
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('teacher_dashboard'))
   
    # POST - Add student
    name = request.form.get('name', '').strip()
    roll_no = request.form.get('roll_no', '').strip()
    year = request.form.get('year', '').strip()
    branch = request.form.get('branch', '').strip()
    subject_id = request.form.get('subject_id', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    password = 'student123'
   
    print(f"✅ ADD STUDENT: Name={name}, Roll={roll_no}, Year={year}, Branch={branch}, Subject={subject_id}")
   
    if not name or not roll_no or not year or not branch or not subject_id:
        flash("Please fill all required fields and select a subject", "error")
        return redirect(url_for('add_student'))
   
    try:
        conn = get_db_connection()
       
        # Check if student exists
        existing = conn.execute("SELECT id FROM students WHERE roll_no=?", (roll_no,)).fetchone()
       
        if existing:
            student_id = existing['id']
            print(f"⚠️ Student exists: ID={student_id}")
        else:
            cursor = conn.execute('''INSERT INTO students (name, roll_no, year, branch, email, phone, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (name, roll_no, year, branch, email, phone, password))
            student_id = cursor.lastrowid
            print(f"✅ New student added: ID={student_id}")
       
        # Enroll in subject
        try:
            conn.execute('INSERT INTO enrollments (student_id, subject_id) VALUES (?, ?)',
                (student_id, subject_id))
            flash(f"Student '{name}' added and enrolled successfully!", "success")
            print(f"✅ Enrolled: Student {student_id} in Subject {subject_id}")
        except sqlite3.IntegrityError:
            flash(f"Student '{name}' already enrolled in this subject", "info")
            print(f"⚠️ Already enrolled")
       
        conn.commit()
        conn.close()
       
        return redirect(url_for('class_details', subject_id=subject_id))
       
    except sqlite3.IntegrityError:
        flash(f"Student with roll number '{roll_no}' already exists", "error")
        return redirect(url_for('add_student'))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        print(f"❌ Error: {str(e)}")
        return redirect(url_for('add_student'))

# ========== CLASS DETAILS ==========
@app.route('/class_details/<int:subject_id>')
def class_details(subject_id):
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    try:
        conn = get_db_connection()
        subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
            (subject_id, session['teacher_id'])).fetchone()
       
        if not subject:
            flash("Subject not found", "error")
            return redirect(url_for('teacher_dashboard'))
       
        students = conn.execute("""SELECT s.* FROM students s
            JOIN enrollments e ON s.id = e.student_id
            WHERE e.subject_id = ?""", (subject_id,)).fetchall()
       
        conn.close()
        return render_template('classDetails.html', subject=subject, students=students)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_dashboard'))


@app.before_request
def update_teacher_location():
    if 'teacher_id' in session:
        # Example: get current location from GPS or frontend (dummy values for now)
        current_lat = session.get('teacher_latitude', 19.0)  # replace with real GPS
        current_lon = session.get('teacher_longitude', 73.0) # replace with real GPS

        conn = get_db_connection()
        conn.execute("""
            INSERT OR REPLACE INTO teacher_temp_locations
            (teacher_id, latitude, longitude)
            VALUES (?, ?, ?)
        """, (session['teacher_id'], current_lat, current_lon))
        conn.commit()
        conn.close()


# ========== ATTENDANCE ========== ✅ COMPLETELY UPDATED WITH LOCATION

from math import radians, cos, sin, asin, sqrt
from datetime import datetime

# ---------- Distance function ----------
def distance_m(lat1, lon1, lat2, lon2):
    """
    Returns distance in meters between two lat/lon points using Haversine formula
    """
    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of Earth in meters
    return c * r

# ---------- Take Attendance ----------
@app.route('/take_attendance/<int:subject_id>')
def take_attendance(subject_id):
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))

    conn = get_db_connection()
   
    # Fetch subject info
    subject = conn.execute("""
        SELECT * FROM subjects WHERE id=? AND teacher_id=?
    """, (subject_id, session['teacher_id'])).fetchone()
   
    if not subject:
        flash("Subject not found", "error")
        return redirect(url_for('teacher_dashboard'))
   
    # Fetch teacher's current location from temp table
    teacher_loc = conn.execute("""
        SELECT latitude, longitude FROM teacher_temp_locations
        WHERE teacher_id=?
    """, (session['teacher_id'],)).fetchone()
   
    if not teacher_loc:
        flash("Teacher location missing. Please update location.", "error")
        return redirect(url_for('teacher_dashboard'))

    today = datetime.now().strftime('%Y-%m-%d')

    # Fetch students + their mark requests for this subject
    students = conn.execute("""
        SELECT s.id, s.roll_no, s.name,
               smr.latitude AS stu_lat, smr.longitude AS stu_lon
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        LEFT JOIN student_mark_requests smr
               ON s.id = smr.student_id AND smr.subject_id = ?
        WHERE e.subject_id = ?
    """, (subject_id, subject_id)).fetchall()

    attendance_results = []

    for stu in students:
        if stu['stu_lat'] is None or stu['stu_lon'] is None:
            status = 'Absent'
        else:
            d = distance_m(
                teacher_loc['latitude'], teacher_loc['longitude'],
                stu['stu_lat'], stu['stu_lon']
            )
            status = 'Present' if d <= 50 else 'Absent'

        # Save attendance (replace if already exists)
        conn.execute("""
            INSERT OR REPLACE INTO attendance
            (student_id, subject_id, date, status, marked_by)
            VALUES (?, ?, ?, ?, ?)
        """, (stu['id'], subject_id, today, status, session['teacher_id']))

        attendance_results.append({
            'roll_no': stu['roll_no'],
            'name': stu['name'],
            'status': status
        })

    conn.commit()
    conn.close()

    return render_template(
        'take_attendance.html',
        students=attendance_results,
        subject=subject,  # ← pass the subject object
        date=today
    )


#---- GET => PREVIEW LIVE STATUS ------------------
    preview_list = []
    for stu in students:
        stu_lat = stu["latitude"]
        stu_lon = stu["longitude"]

        if stu_lat == 0 or stu_lon == 0:
            live_status = "No Location"
        else:
            d = distance_m(
                float(teacher_lat), float(teacher_lon),
                float(stu_lat), float(stu_lon)
            )
            live_status = "Present" if d <= 50 else "Absent"

        preview_list.append({
            "id": stu["id"],
            "roll_no": stu["roll_no"],
            "name": stu["name"],
            "status": live_status
        })

    conn.close()

    return render_template("take_attendance.html",
                           students=preview_list,
                           subject=subject)

# ✅ ADDED - Start attendance session
@app.route('/start_attendance', methods=['POST'])
def start_attendance():
    if 'teacher_id' not in session:
        return {'error': 'Not logged in'}, 401
   
    data = request.get_json()
    subject_id = data.get('subject_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
   
    if not subject_id or not latitude or not longitude:
        return {'error': 'Missing data'}, 400
   
    try:
        conn = get_db_connection()
        # Check if subject belongs to teacher
        subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
            (subject_id, session['teacher_id'])).fetchone()
        if not subject:
            conn.close()
            return {'error': 'Subject not found'}, 404
       
        # Insert active session (ends in 5 minutes)
        from datetime import datetime, timedelta
        end_time = datetime.now() + timedelta(minutes=5)
        conn.execute('''INSERT INTO active_attendance_sessions
            (subject_id, teacher_latitude, teacher_longitude, end_time)
            VALUES (?, ?, ?, ?)''',
            (subject_id, latitude, longitude, end_time))
        conn.commit()
        conn.close()
       
        return {'success': True}
    except Exception as e:
        return {'error': str(e)}, 500


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'student_id' not in session:
        return {'error': 'Not logged in'}, 401

    data = request.get_json()
    subject_id = data.get('subject_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not subject_id or latitude is None or longitude is None:
        return {'error': 'Missing data'}, 400

    try:
        conn = get_db_connection()

        # Save student location globally
        conn.execute("""
            INSERT OR REPLACE INTO student_temp_locations
            (student_id, latitude, longitude)
            VALUES (?, ?, ?)
        """, (session['student_id'], latitude, longitude))

        # Save student mark request for this subject
        conn.execute("""
            INSERT OR REPLACE INTO student_mark_requests
            (student_id, subject_id, latitude, longitude)
            VALUES (?, ?, ?, ?)
        """, (session['student_id'], subject_id, latitude, longitude))

        conn.commit()
        conn.close()

        return {'status': 'Location saved, waiting for teacher to take attendance'}

    except Exception as e:
        return {'error': str(e)}, 500
@app.route('/view_attendance/<int:subject_id>')
def view_attendance(subject_id):
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    try:
        conn = get_db_connection()
        subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
            (subject_id, session['teacher_id'])).fetchone()
       
        if not subject:
            flash("Subject not found", "error")
            return redirect(url_for('teacher_dashboard'))
       
        attendance_records = conn.execute("""SELECT s.roll_no, s.name, a.date, a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.subject_id = ?
            ORDER BY a.date DESC, s.roll_no""", (subject_id,)).fetchall()
       
        conn.close()
        return render_template('view_attendance.html', subject=subject, attendance_records=attendance_records)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_dashboard'))

@app.route('/generate_report/<int:subject_id>')
def generate_report(subject_id):
    if 'teacher_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('teacher_login'))
   
    try:
        conn = get_db_connection()
        subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
            (subject_id, session['teacher_id'])).fetchone()
       
        if not subject:
            flash("Subject not found", "error")
            return redirect(url_for('teacher_dashboard'))
       
        students_summary = conn.execute("""SELECT
                s.roll_no, s.name,
                COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_count,
                COUNT(DISTINCT a.date) as total_classes
            FROM students s
            JOIN enrollments e ON s.id = e.student_id
            LEFT JOIN attendance a ON s.id = a.student_id AND a.subject_id = e.subject_id
            WHERE e.subject_id = ?
            GROUP BY s.id
            ORDER BY s.roll_no""", (subject_id,)).fetchall()
       
        conn.close()
        return render_template('generate_report.html', subject=subject, students_summary=students_summary)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('teacher_dashboard'))

# ========== STUDENT LOGIN ========== ✅ LOCATION ADDED
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    error = None
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        password = request.form.get('password', '').strip()
        latitude = request.form.get('latitude')    # ✅ ADDED
        longitude = request.form.get('longitude')  # ✅ ADDED
       
        if not roll_no or not password:
            error = "Please enter both roll number and password"
        else:
            try:
                conn = get_db_connection()
                student = conn.execute("SELECT * FROM students WHERE roll_no=? AND password=?",
                    (roll_no, password)).fetchone()
               
                if student:
                    session['student_id'] = student['id']
                    session['student_name'] = student['name']
                    session['student_roll'] = student['roll_no']
                   
                    # ✅ ADDED - Store location in temp table
                    if latitude and longitude:
                        conn.execute("""INSERT OR REPLACE INTO student_temp_locations
                            (student_id, latitude, longitude) VALUES (?, ?, ?)""",
                            (student['id'], float(latitude), float(longitude)))
                        conn.commit()
                        print(f"📍 Student Location: {latitude}, {longitude}")
                   
                    conn.close()
                    flash(f"Welcome back, {student['name']}!", "success")
                    return redirect(url_for('student_dashboard'))
                else:
                    error = "Invalid Roll Number or Password."
                    conn.close()
            except Exception as e:
                error = f"Database error: {str(e)}"
    return render_template("student_login.html", error=error)

# ✅ UPDATED - Student dashboard with location
@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('student_login'))
   
    try:
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE id=?", (session['student_id'],)).fetchone()
       
        subjects = conn.execute("""SELECT s.id, s.subject_name, s.subject_code, t.name AS teacher_name
            FROM subjects s
            JOIN enrollments e ON s.id = e.subject_id
            JOIN teachers t ON s.teacher_id = t.id
            WHERE e.student_id=?""", (session['student_id'],)).fetchall()
       
        attendance_summary = []
        for subject in subjects:
            subject_id = subject['id']
            total_classes = conn.execute("SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?",
                (subject_id,)).fetchone()[0]
            present_count = conn.execute("""SELECT COUNT(*) FROM attendance
                WHERE subject_id=? AND student_id=? AND status='Present'""",
                (subject_id, session['student_id'])).fetchone()[0]
           
            attendance_percentage = round((present_count / total_classes * 100), 2) if total_classes > 0 else 0
           
            attendance_summary.append({
                'subject_id': subject['id'],
                'subject_name': subject['subject_name'],
                'subject_code': subject['subject_code'],
                'teacher_name': subject['teacher_name'],
                'total_classes': total_classes,
                'present_count': present_count,
                'attendance_percentage': attendance_percentage
            })
       
        # ✅ ADDED - Get student location from temp table
        student_loc = conn.execute("""SELECT latitude, longitude
            FROM student_temp_locations WHERE student_id=?""",
            (session['student_id'],)).fetchone()
       
        student_location = {
            'latitude': student_loc['latitude'] if student_loc else 0,
            'longitude': student_loc['longitude'] if student_loc else 0
        }
       
        conn.close()
       
        # ✅ UPDATED - Pass student_location to template
        return render_template('student_dashboard.html',
                             student=student,
                             attendance_summary=attendance_summary,
                             student_location=student_location)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('student_login'))

@app.route('/student_attendance')
def student_attendance():
    if 'student_id' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('student_login'))
   
    try:
        conn = get_db_connection()
        student = conn.execute("SELECT * FROM students WHERE id=?", (session['student_id'],)).fetchone()
       
        attendance_records = conn.execute("""SELECT s.subject_name, s.subject_code, a.date, a.status
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.id
            WHERE a.student_id=?
            ORDER BY a.date DESC""", (session['student_id'],)).fetchall()
       
        conn.close()
        return render_template('student_attendance.html', student=student, attendance_records=attendance_records)
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('student_dashboard'))

# ========== LOGOUT ==========
@app.route('/logout')
def logout():
    if 'teacher_id' in session:
        session.pop('teacher_id', None)
        session.pop('teacher_name', None)
        session.pop('teacher_latitude', None)  # ✅ ADDED
        session.pop('teacher_longitude', None)  # ✅ ADDED
        flash("Teacher logged out!", "info")
    elif 'student_id' in session:
        session.pop('student_id', None)
        session.pop('student_name', None)
        session.pop('student_roll', None)
        flash("Student logged out!", "info")
    return redirect(url_for('home_page'))

if __name__ == "__main__":
    init_database()
   
    print("\n" + "="*60)
    print("🎓 ATTENDANCE MANAGEMENT SYSTEM WITH LOCATION")
    print("="*60)
    print("\n👨‍🏫 TEACHER: teacher@college.com / teacher123")
    print("👨‍🎓 STUDENT: 2021001 / student123")
    print("\n🌐 http://localhost:5000")
    print("📍 Location tracking enabled!")
    print("📏 Auto-marking within 50 meters")
    print("="*60 + "\n")
   
    app.run(debug=True, host='0.0.0.0', port=5000)

# # ---------- LOGOUT ----------
# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect("/")

# # ---------- RUN ----------
# if __name__ == "__main__":
#     app.run(debug=True)
