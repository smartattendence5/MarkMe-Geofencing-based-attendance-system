from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime, timedelta
import math
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
app.secret_key = "supersecretkey123"

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def distance(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# ========== HOME ==========
@app.route('/')
def home_page():
    return render_template("index.html")

# ========== TEACHER LOGIN ==========
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
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
                    if latitude and longitude:
                        session['teacher_latitude'] = float(latitude)
                        session['teacher_longitude'] = float(longitude)
                    flash(f"Welcome back, {teacher['name']}!", "success")
                    return redirect(url_for('teacher_dashboard'))
                else:
                    error = "Invalid email or password."
            except Exception as e:
                error = f"Database error: {str(e)}"
    return render_template("teacher_login.html", error=error)

# ========== TEACHER DASHBOARD ==========
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
        return redirect(url_for('teacher_login'))
    return render_template("add_subject.html")

@app.route('/add_subject', methods=['POST'])
def add_subject():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    subject_name = request.form.get('subject_name', '').strip()
    subject_code = request.form.get('subject_code', '').strip()
    year = request.form.get('year', '').strip()
    branch = request.form.get('branch', '').strip()
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
        return redirect(url_for('teacher_login'))
    conn = get_db_connection()
    subjects = conn.execute("SELECT * FROM subjects WHERE teacher_id=?", (session['teacher_id'],)).fetchall()
    conn.close()
    return render_template("add_student.html", subjects=subjects)

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    name = request.form.get('name', '').strip()
    roll_no = request.form.get('roll_no', '').strip()
    year = request.form.get('year', '').strip()
    branch = request.form.get('branch', '').strip()
    subject_id = request.form.get('subject_id', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    try:
        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM students WHERE roll_no=?", (roll_no,)).fetchone()
        if existing:
            student_id = existing['id']
        else:
            cursor = conn.execute('''INSERT INTO students (name, roll_no, year, branch, email, phone, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (name, roll_no, year, branch, email, phone, 'student123'))
            student_id = cursor.lastrowid
        try:
            conn.execute('INSERT INTO enrollments (student_id, subject_id) VALUES (?, ?)',
                (student_id, subject_id))
            flash(f"Student '{name}' added successfully!", "success")
        except sqlite3.IntegrityError:
            flash(f"Student already enrolled", "info")
        conn.commit()
        conn.close()
        return redirect(url_for('class_details', subject_id=subject_id))
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('add_student_form'))

# ========== CLASS DETAILS ==========
@app.route('/class_details/<int:subject_id>')
def class_details(subject_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
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

# ========== TAKE ATTENDANCE ==========
@app.route('/take_attendance/<int:subject_id>')
def take_attendance(subject_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
        (subject_id, session['teacher_id'])).fetchone()
    if not subject:
        flash("Subject not found", "error")
        return redirect(url_for('teacher_dashboard'))
    teacher_lat = session.get('teacher_latitude', 0)
    teacher_lon = session.get('teacher_longitude', 0)
    conn.execute("""
        INSERT OR REPLACE INTO teacher_temp_locations (teacher_id, latitude, longitude)
        VALUES (?, ?, ?)
    """, (session['teacher_id'], teacher_lat, teacher_lon))
    conn.commit()
    active_session = conn.execute("""
        SELECT * FROM active_attendance_sessions
        WHERE subject_id=? AND teacher_id=? AND date=? AND end_time > datetime('now')
    """, (subject_id, session['teacher_id'], today)).fetchone()
    if not active_session:
        conn.execute("""
            INSERT INTO active_attendance_sessions
            (subject_id, teacher_id, teacher_latitude, teacher_longitude, date, end_time)
            VALUES (?, ?, ?, ?, ?, datetime('now', '+1 hour'))
        """, (subject_id, session['teacher_id'], teacher_lat, teacher_lon, today))
        enrolled_students = conn.execute(
            "SELECT student_id FROM enrollments WHERE subject_id=?", (subject_id,)).fetchall()
        for student in enrolled_students:
            exists = conn.execute("""
                SELECT 1 FROM attendance WHERE student_id=? AND subject_id=? AND date=?
            """, (student['student_id'], subject_id, today)).fetchone()
            if not exists:
                conn.execute("""
                    INSERT INTO attendance (student_id, subject_id, date, status, marked_by)
                    VALUES (?, ?, ?, 'Absent', ?)
                """, (student['student_id'], subject_id, today, session['teacher_id']))
        conn.commit()
    students = conn.execute("""
        SELECT s.id, s.roll_no, s.name,
        COALESCE(a.status, 'Absent') AS status
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = ? AND a.date = ?
        WHERE e.subject_id = ?
        ORDER BY s.roll_no
    """, (subject_id, today, subject_id)).fetchall()
    conn.close()
    final_list = [{"roll_no": s["roll_no"], "name": s["name"], "status": s["status"]} for s in students]
    return render_template("take_attendance.html", students=final_list, subject=subject, date=today)

# ========== MARK ATTENDANCE (Student) ==========
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'student_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    subject_id = data.get('subject_id')
    student_lat = data.get('latitude')
    student_lon = data.get('longitude')
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    session_row = conn.execute("""
        SELECT * FROM active_attendance_sessions
        WHERE subject_id=? AND date=? AND end_time > datetime('now')
    """, (subject_id, today)).fetchone()
    if not session_row:
        conn.close()
        return jsonify({"error": "No active attendance session. Teacher has not started attendance yet."}), 400
    teacher_lat = session_row['teacher_latitude']
    teacher_lon = session_row['teacher_longitude']
    d = distance(teacher_lat, teacher_lon, student_lat, student_lon)
    status = "Present" if d <= 50 else "Absent"
    result = conn.execute("""
        UPDATE attendance SET status=?, marked_at=datetime('now')
        WHERE student_id=? AND subject_id=? AND date=?
    """, (status, session['student_id'], subject_id, today))
    rows_updated = result.rowcount
    conn.commit()
    conn.close()
    if rows_updated == 0:
        return jsonify({"error": "Attendance record not found.", "distance": round(d, 2)}), 400
    return jsonify({"status": status, "distance": round(d, 2), "message": f"Marked {status}! Distance: {round(d, 2)}m"})

# ========== VIEW ATTENDANCE ==========
@app.route('/view_attendance/<int:subject_id>')
def view_attendance(subject_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    conn = get_db_connection()
    subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
        (subject_id, session['teacher_id'])).fetchone()
    if not subject:
        flash("Subject not found", "error")
        return redirect(url_for('teacher_dashboard'))
    attendance_records = conn.execute("""
        SELECT s.roll_no, s.name, a.date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.subject_id = ?
        GROUP BY a.student_id, a.date
        ORDER BY a.date DESC, s.roll_no
    """, (subject_id,)).fetchall()
    conn.close()
    return render_template('view_attendance.html', subject=subject, attendance_records=attendance_records)

# ========== GENERATE REPORT ==========
@app.route('/generate_report/<int:subject_id>')
def generate_report(subject_id):
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    conn = get_db_connection()
    subject = conn.execute("SELECT * FROM subjects WHERE id=? AND teacher_id=?",
        (subject_id, session['teacher_id'])).fetchone()
    if not subject:
        flash("Subject not found", "error")
        return redirect(url_for('teacher_dashboard'))
    students_summary = conn.execute("""
        SELECT
            s.roll_no, s.name,
            COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_count,
            COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_count,
            COUNT(DISTINCT a.date) as total_classes,
            ROUND(
                CAST(COUNT(CASE WHEN a.status = 'Present' THEN 1 END) AS FLOAT) * 100.0 /
                NULLIF(COUNT(DISTINCT a.date), 0), 2
            ) as attendance_percentage
        FROM students s
        JOIN enrollments e ON s.id = e.student_id
        LEFT JOIN attendance a ON s.id = a.student_id AND a.subject_id = ?
        WHERE e.subject_id = ?
        GROUP BY s.id, s.roll_no, s.name
        ORDER BY s.roll_no
    """, (subject_id, subject_id)).fetchall()
    conn.close()
    return render_template('generate_report.html', subject=subject, students_summary=students_summary)

# ========== STUDENT LOGIN ==========
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    error = None
    if request.method == 'POST':
        roll_no = request.form.get('roll_no', '').strip()
        password = request.form.get('password', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
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
                    if latitude and longitude:
                        conn.execute("""INSERT OR REPLACE INTO student_temp_locations
                            (student_id, latitude, longitude) VALUES (?, ?, ?)""",
                            (student['id'], float(latitude), float(longitude)))
                        conn.commit()
                    conn.close()
                    flash(f"Welcome back, {student['name']}!", "success")
                    return redirect(url_for('student_dashboard'))
                else:
                    error = "Invalid credentials"
                    conn.close()
            except Exception as e:
                error = f"Error: {str(e)}"
    return render_template("student_login.html", error=error)

# ========== STUDENT DASHBOARD ==========
@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (session['student_id'],)).fetchone()
    subjects = conn.execute("""
        SELECT s.id, s.subject_name, s.subject_code, t.name AS teacher_name
        FROM subjects s
        JOIN enrollments e ON s.id = e.subject_id
        JOIN teachers t ON s.teacher_id = t.id
        WHERE e.student_id=?
    """, (session['student_id'],)).fetchall()
    attendance_summary = []
    for subject in subjects:
        subject_id = subject['id']
        total_classes = conn.execute(
            "SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?", (subject_id,)).fetchone()[0]
        present_count = conn.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE subject_id=? AND student_id=? AND status='Present'
        """, (subject_id, session['student_id'])).fetchone()[0]
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
    conn.close()
    return render_template('student_dashboard.html', student=student, attendance_summary=attendance_summary)

# ========== STUDENT ATTENDANCE HISTORY ==========
@app.route('/student_attendance')
def student_attendance():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (session['student_id'],)).fetchone()
    attendance_records = conn.execute("""
        SELECT s.subject_name, s.subject_code, a.date, a.status
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id=?
        ORDER BY a.date DESC
    """, (session['student_id'],)).fetchall()
    conn.close()
    return render_template('student_attendance.html', student=student, attendance_records=attendance_records)

# ========== CHATBOT ROUTE ==========
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    question = data.get('question', '').lower().strip()

    # Determine if it's teacher or student session
    is_teacher = 'teacher_id' in session
    is_student = 'student_id' in session

    if not is_teacher and not is_student:
        return jsonify({"response": "⚠️ Please login to use the assistant."})

    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    response = ""

    try:
        # ============================================================
        # STUDENT CHATBOT
        # ============================================================
        if is_student:
            student_id = session['student_id']

            # Fetch all subjects for student
            subjects = conn.execute("""
                SELECT s.id, s.subject_name, s.subject_code, t.name as teacher_name
                FROM subjects s
                JOIN enrollments e ON s.id = e.subject_id
                JOIN teachers t ON s.teacher_id = t.id
                WHERE e.student_id = ?
            """, (student_id,)).fetchall()

            # ---- Attendance percentage ----
            if any(k in question for k in ['attendance percentage', 'attendance %', 'my attendance', 'percent', 'percentage']):
                if not subjects:
                    response = "📚 You are not enrolled in any subjects yet."
                else:
                    lines = ["📊 <strong>Your Attendance Summary:</strong><br><br>"]
                    for sub in subjects:
                        total = conn.execute(
                            "SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?",
                            (sub['id'],)).fetchone()[0]
                        present = conn.execute(
                            "SELECT COUNT(*) FROM attendance WHERE subject_id=? AND student_id=? AND status='Present'",
                            (sub['id'], student_id)).fetchone()[0]
                        pct = round((present / total * 100), 1) if total > 0 else 0
                        color = "#28a745" if pct >= 75 else "#ffc107" if pct >= 60 else "#dc3545"
                        icon = "✅" if pct >= 75 else "⚠️" if pct >= 60 else "❌"
                        lines.append(f"{icon} <strong>{sub['subject_name']}</strong>: "
                                     f"<span style='color:{color};font-weight:bold;'>{pct}%</span> "
                                     f"({present}/{total} classes)<br>")
                    response = "".join(lines)

            # ---- Today's status ----
            elif any(k in question for k in ['today', 'today status', "today's status", 'aaj']):
                if not subjects:
                    response = "📚 You are not enrolled in any subjects."
                else:
                    lines = [f"📅 <strong>Today's Attendance ({today}):</strong><br><br>"]
                    found_any = False
                    for sub in subjects:
                        record = conn.execute("""
                            SELECT status FROM attendance
                            WHERE student_id=? AND subject_id=? AND date=?
                        """, (student_id, sub['id'], today)).fetchone()
                        if record:
                            found_any = True
                            icon = "✅" if record['status'] == 'Present' else "❌"
                            lines.append(f"{icon} <strong>{sub['subject_name']}</strong>: {record['status']}<br>")
                    if not found_any:
                        lines.append("No attendance has been marked for today yet.")
                    response = "".join(lines)

            # ---- 75% requirement ----
            elif any(k in question for k in ['75', 'requirement', 'need', 'how many classes', 'classes needed']):
                if not subjects:
                    response = "📚 You are not enrolled in any subjects."
                else:
                    lines = ["🎯 <strong>Classes Needed to Reach 75% Attendance:</strong><br><br>"]
                    for sub in subjects:
                        total = conn.execute(
                            "SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?",
                            (sub['id'],)).fetchone()[0]
                        present = conn.execute(
                            "SELECT COUNT(*) FROM attendance WHERE subject_id=? AND student_id=? AND status='Present'",
                            (sub['id'], student_id)).fetchone()[0]
                        pct = round((present / total * 100), 1) if total > 0 else 0
                        if pct >= 75:
                            lines.append(f"✅ <strong>{sub['subject_name']}</strong>: Already at {pct}% — Great job!<br>")
                        else:
                            # Calculate classes needed
                            needed = 0
                            temp_p, temp_t = present, total
                            while temp_t > 0 and round(temp_p / temp_t * 100, 1) < 75:
                                temp_p += 1
                                temp_t += 1
                                needed += 1
                            lines.append(f"⚠️ <strong>{sub['subject_name']}</strong>: Currently {pct}% — "
                                         f"Attend next <strong>{needed}</strong> consecutive class(es) to reach 75%.<br>")
                    response = "".join(lines)

            # ---- Total classes ----
            elif any(k in question for k in ['total classes', 'how many total', 'total class']):
                if not subjects:
                    response = "📚 No subjects enrolled."
                else:
                    lines = ["📚 <strong>Total Classes Per Subject:</strong><br><br>"]
                    for sub in subjects:
                        total = conn.execute(
                            "SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?",
                            (sub['id'],)).fetchone()[0]
                        lines.append(f"📖 <strong>{sub['subject_name']}</strong>: {total} class(es) held so far<br>")
                    response = "".join(lines)

            # ---- Lowest attendance subject ----
            elif any(k in question for k in ['lowest', 'worst', 'bad attendance', 'low attendance']):
                if not subjects:
                    response = "📚 No subjects enrolled."
                else:
                    results = []
                    for sub in subjects:
                        total = conn.execute(
                            "SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?",
                            (sub['id'],)).fetchone()[0]
                        present = conn.execute(
                            "SELECT COUNT(*) FROM attendance WHERE subject_id=? AND student_id=? AND status='Present'",
                            (sub['id'], student_id)).fetchone()[0]
                        pct = round((present / total * 100), 1) if total > 0 else 0
                        results.append((sub['subject_name'], pct, present, total))
                    results.sort(key=lambda x: x[1])
                    worst = results[0]
                    response = (f"📉 <strong>Lowest Attendance Subject:</strong><br><br>"
                                f"❌ <strong>{worst[0]}</strong> with only "
                                f"<span style='color:#dc3545;font-weight:bold;'>{worst[1]}%</span> "
                                f"({worst[2]}/{worst[3]} classes)<br><br>"
                                f"Please focus on attending this subject regularly!")
            else:
                response = (
                    "🤖 <strong>I can help you with:</strong><br><br>"
                    "📊 <em>Attendance percentage</em> — your subject-wise %<br>"
                    "📅 <em>Today's status</em> — present/absent today<br>"
                    "🎯 <em>75% requirement</em> — classes needed<br>"
                    "📚 <em>Total classes</em> — classes held per subject<br>"
                    "📉 <em>Lowest attendance</em> — your weakest subject<br><br>"
                    "Please ask one of the above!"
                )

        # ============================================================
        # TEACHER CHATBOT
        # ============================================================
        elif is_teacher:
            teacher_id = session['teacher_id']

            subjects = conn.execute(
                "SELECT * FROM subjects WHERE teacher_id=?", (teacher_id,)).fetchall()

            # ---- Overall stats ----
            if any(k in question for k in ['overall', 'statistics', 'stats', 'summary', 'overview']):
                if not subjects:
                    response = "📚 You have not added any subjects yet."
                else:
                    lines = ["📊 <strong>Overall Attendance Statistics:</strong><br><br>"]
                    for sub in subjects:
                        total_students = conn.execute("""
                            SELECT COUNT(*) FROM enrollments WHERE subject_id=?
                        """, (sub['id'],)).fetchone()[0]
                        total_classes = conn.execute("""
                            SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?
                        """, (sub['id'],)).fetchone()[0]
                        avg_pct = conn.execute("""
                            SELECT AVG(pct) FROM (
                                SELECT student_id,
                                ROUND(CAST(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS FLOAT)
                                * 100.0 / NULLIF(COUNT(*), 0), 1) as pct
                                FROM attendance WHERE subject_id=?
                                GROUP BY student_id
                            )
                        """, (sub['id'],)).fetchone()[0]
                        avg_pct = round(avg_pct, 1) if avg_pct else 0
                        color = "#28a745" if avg_pct >= 75 else "#ffc107" if avg_pct >= 60 else "#dc3545"
                        lines.append(
                            f"📖 <strong>{sub['subject_name']}</strong> ({sub['subject_code']})<br>"
                            f"&nbsp;&nbsp;&nbsp;Students: {total_students} | Classes: {total_classes} | "
                            f"Avg Attendance: <span style='color:{color};font-weight:bold;'>{avg_pct}%</span><br><br>"
                        )
                    response = "".join(lines)

            # ---- Today's attendance ----
            elif any(k in question for k in ['today', "today's", 'aaj']):
                if not subjects:
                    response = "📚 No subjects found."
                else:
                    lines = [f"📅 <strong>Today's Attendance ({today}):</strong><br><br>"]
                    found_any = False
                    for sub in subjects:
                        present = conn.execute("""
                            SELECT COUNT(*) FROM attendance
                            WHERE subject_id=? AND date=? AND status='Present'
                        """, (sub['id'], today)).fetchone()[0]
                        absent = conn.execute("""
                            SELECT COUNT(*) FROM attendance
                            WHERE subject_id=? AND date=? AND status='Absent'
                        """, (sub['id'], today)).fetchone()[0]
                        total = present + absent
                        if total > 0:
                            found_any = True
                            pct = round(present / total * 100, 1) if total > 0 else 0
                            lines.append(
                                f"📖 <strong>{sub['subject_name']}</strong>: "
                                f"✅ {present} Present | ❌ {absent} Absent | "
                                f"<strong>{pct}%</strong><br>"
                            )
                    if not found_any:
                        lines.append("No attendance has been taken today yet.")
                    response = "".join(lines)

            # ---- Low attendance students ----
            elif any(k in question for k in ['low attendance', 'below 75', 'defaulter', 'at risk', 'warning']):
                if not subjects:
                    response = "📚 No subjects found."
                else:
                    lines = ["⚠️ <strong>Students with Attendance Below 75%:</strong><br><br>"]
                    found_any = False
                    for sub in subjects:
                        students = conn.execute("""
                            SELECT s.name, s.roll_no,
                            ROUND(CAST(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS FLOAT)
                            * 100.0 / NULLIF(COUNT(*), 0), 1) as pct
                            FROM attendance a
                            JOIN students s ON a.student_id = s.id
                            WHERE a.subject_id=?
                            GROUP BY a.student_id
                            HAVING pct < 75
                            ORDER BY pct ASC
                        """, (sub['id'],)).fetchall()
                        if students:
                            found_any = True
                            lines.append(f"📖 <strong>{sub['subject_name']}:</strong><br>")
                            for st in students:
                                lines.append(
                                    f"&nbsp;&nbsp;&nbsp;❌ {st['name']} ({st['roll_no']}) — "
                                    f"<span style='color:#dc3545;font-weight:bold;'>{st['pct']}%</span><br>"
                                )
                            lines.append("<br>")
                    if not found_any:
                        lines.append("✅ All students have attendance above 75%. Great!")
                    response = "".join(lines)

            # ---- Subject-wise report ----
            elif any(k in question for k in ['subject', 'subject wise', 'subject report', 'subject-wise']):
                if not subjects:
                    response = "📚 No subjects found."
                else:
                    lines = ["📚 <strong>Subject-wise Attendance Report:</strong><br><br>"]
                    for sub in subjects:
                        total_students = conn.execute(
                            "SELECT COUNT(*) FROM enrollments WHERE subject_id=?", (sub['id'],)).fetchone()[0]
                        total_classes = conn.execute(
                            "SELECT COUNT(DISTINCT date) FROM attendance WHERE subject_id=?", (sub['id'],)).fetchone()[0]
                        present_today = conn.execute("""
                            SELECT COUNT(*) FROM attendance
                            WHERE subject_id=? AND status='Present'
                        """, (sub['id'],)).fetchone()[0]
                        total_records = conn.execute(
                            "SELECT COUNT(*) FROM attendance WHERE subject_id=?", (sub['id'],)).fetchone()[0]
                        overall_pct = round(present_today / total_records * 100, 1) if total_records > 0 else 0
                        color = "#28a745" if overall_pct >= 75 else "#ffc107" if overall_pct >= 60 else "#dc3545"
                        lines.append(
                            f"📖 <strong>{sub['subject_name']}</strong> ({sub['subject_code']})<br>"
                            f"&nbsp;&nbsp;&nbsp;👥 Students: {total_students} | 📅 Classes Held: {total_classes}<br>"
                            f"&nbsp;&nbsp;&nbsp;Overall Attendance: <span style='color:{color};font-weight:bold;'>{overall_pct}%</span><br><br>"
                        )
                    response = "".join(lines)

            else:
                response = (
                    "🤖 <strong>I can help you with:</strong><br><br>"
                    "📊 <em>Overall statistics</em> — subject-wise overview<br>"
                    "📅 <em>Today's attendance</em> — present/absent count<br>"
                    "⚠️ <em>Low attendance</em> — students below 75%<br>"
                    "📚 <em>Subject report</em> — detailed per-subject data<br><br>"
                    "Please ask one of the above!"
                )

    except Exception as e:
        response = f"❌ Error fetching data: {str(e)}"
    finally:
        conn.close()

    return jsonify({"response": response})

# ========== LOGOUT ==========
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out!", "info")
    return redirect(url_for('home_page'))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎓 ATTENDANCE SYSTEM - GEO-FENCING ENABLED")
    print("="*60)
    print("🌐 http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)