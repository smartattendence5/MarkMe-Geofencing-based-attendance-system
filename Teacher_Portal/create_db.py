import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")

# Delete old database if exists
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("🗑️ Old database deleted")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("📦 Creating tables...")

# ================= TEACHERS =================
c.execute('''CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    department TEXT,
    phone TEXT
)''')

# ================= STUDENTS =================
c.execute('''CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    year TEXT,
    branch TEXT,
    password TEXT NOT NULL DEFAULT 'student123',
    email TEXT,
    phone TEXT
)''')

# ================= SUBJECTS =================
c.execute('''CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    subject_code TEXT,
    teacher_id INTEGER NOT NULL,
    year TEXT,
    branch TEXT,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id)
)''')

# ================= ENROLLMENTS =================
c.execute('''CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    UNIQUE(student_id, subject_id)
)''')

# ================= ATTENDANCE =================
c.execute('''CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
    marked_by INTEGER,
    marked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id),
    FOREIGN KEY(marked_by) REFERENCES teachers(id)
)''')

# ------------------- Temporary student location -------------------
c.execute('''
CREATE TABLE IF NOT EXISTS student_temp_locations (
    student_id INTEGER PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
''')

# ------------------- Student Mark Requests (per subject) -------------------
c.execute('''
CREATE TABLE IF NOT EXISTS student_mark_requests (
    student_id INTEGER,
    subject_id INTEGER,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    marked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(student_id, subject_id),
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(subject_id) REFERENCES subjects(id)
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS teacher_temp_locations (
    teacher_id INTEGER PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id)
)
''')

print("✅ All tables created\n")

# ================= INSERT SAMPLE DATA =================
print("📝 Inserting sample data...\n")

# ---------- Teachers ----------
teachers = [
    ('Dr. Shitole Sir', 'shitole@college.com', '12345', 'Computer Science', '9876543210'),
    ('Prof. Margi Maam', 'margi@college.com', 'teacher123', 'Computer Science', '9876543211'),
    ('Dr. Patil Sir', 'patil@college.com', 'teacher123', 'Information Technology', '9876543212'),
    ('Prof. Deshmukh Maam', 'deshmukh@college.com', 'teacher123', 'Electronics', '9876543213'),
    ('Dr. Kulkarni Sir', 'kulkarni@college.com', 'teacher123', 'Computer Science', '9876543214')
]
c.executemany(
    "INSERT INTO teachers (name,email,password,department,phone) VALUES (?,?,?,?,?)",
    teachers
)

# ---------- Students ----------
students = [
    ('Rahul Sharma','CSE2021001','Second Year','Computer Science','student123','rahul@student.edu','9123456780'),
    ('Priya Patel','CSE2021002','Second Year','Computer Science','student123','priya@student.edu','9123456781'),
    ('Arjun Kumar','CSE2021003','Second Year','Computer Science','student123','arjun@student.edu','9123456782'),
    ('Sneha Reddy','CSE2021004','Second Year','Computer Science','student123','sneha@student.edu','9123456783'),
    ('Vikram Singh','CSE2021005','Second Year','Computer Science','student123','vikram@student.edu','9123456784'),
    ('Neha Gupta','CSE2021006','Second Year','Computer Science','student123','neha@student.edu','9123456785'),
    ('Rohan Joshi','CSE2021007','Second Year','Computer Science','student123','rohan@student.edu','9123456786'),
    ('Ananya Das','CSE2021008','Second Year','Computer Science','student123','ananya@student.edu','9123456787'),
    ('Karan Mehta','CSE2021009','Second Year','Computer Science','student123','karan@student.edu','9123456788'),
    ('Ishita Rao','CSE2021010','Second Year','Computer Science','student123','ishita@student.edu','9123456789'),
]
c.executemany(
    "INSERT INTO students (name,roll_no,year,branch,password,email,phone) VALUES (?,?,?,?,?,?,?)",
    students
)

# ---------- Subjects ----------
subjects = [
    ('Data Structures','CS201',1,'Second Year','Computer Science'),
    ('Web Development','CS202',2,'Second Year','Computer Science'),
    ('Python Programming','CS203',5,'Second Year','Computer Science'),
    ('Digital Logic','CS204',1,'Second Year','Computer Science'),
    ('Computer Architecture','CS205',3,'Second Year','Computer Science'),
    ('Discrete Mathematics','CS206',3,'Second Year','Computer Science'),
    ('Operating Systems','CS207',2,'Second Year','Computer Science'),
    ('Software Engineering','CS208',4,'Second Year','Computer Science'),
    ('Database Management','CS209',5,'Second Year','Computer Science'),
    ('Computer Networks','CS210',1,'Second Year','Computer Science')
]
c.executemany(
    "INSERT INTO subjects (subject_name,subject_code,teacher_id,year,branch) VALUES (?,?,?,?,?)",
    subjects
)

# ---------- Enrollments ----------
enrollments = []
for subject_id in range(1, 11):  # 10 subjects
    for student_id in range(1, 11):  # 10 students
        enrollments.append((student_id, subject_id))

c.executemany(
    "INSERT INTO enrollments (student_id,subject_id) VALUES (?,?)",
    enrollments
)

# ---------- Attendance ----------
attendance_records = []
for subject_id in range(1, 11):  # 10 subjects
    for student_id in range(1, 11):  # 10 students
        total_classes = 15
        classes_attended = random.randint(10, 15)  # Random attendance
        for i in range(total_classes):
            status = 'Present' if i < classes_attended else 'Absent'
            date = (datetime.now() - timedelta(days=total_classes-i)).strftime("%Y-%m-%d")
            marked_by = random.randint(1, 5)  # Random teacher
            attendance_records.append((student_id, subject_id, date, status, marked_by))

c.executemany(
    "INSERT INTO attendance (student_id, subject_id, date, status, marked_by) VALUES (?,?,?,?,?)",
    attendance_records
)

conn.commit()
conn.close()

print("🎉 DATABASE READY WITH MORE SUBJECTS & ATTENDANCE!")
print("🚀 Run: python app.py to see the dashboard")
