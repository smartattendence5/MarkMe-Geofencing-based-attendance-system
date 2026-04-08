import sqlite3
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")

# ================= DELETE OLD DB =================
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("🗑️ Old database deleted")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

print("📦 Creating tables...")

# ================= TABLES =================
c.execute('''CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    department TEXT,
    phone TEXT
)''')

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

c.execute('''CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    subject_code TEXT,
    teacher_id INTEGER NOT NULL,
    year TEXT,
    branch TEXT,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE(student_id, subject_id)
)''')

c.execute('''CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
    marked_by INTEGER,
    marked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY(marked_by) REFERENCES teachers(id),
    UNIQUE(student_id, subject_id, date)
)''')

c.execute('''CREATE TABLE student_temp_locations (
    student_id INTEGER PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE teacher_temp_locations (
    teacher_id INTEGER PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE active_attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    teacher_latitude REAL NOT NULL,
    teacher_longitude REAL NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
    end_time TEXT NOT NULL,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
)''')

print("✅ All tables created\n")

# ================= DATA =================

# Teachers
teachers = [
    ('Dr. Shitole Sir', 'shitole@college.com', '12345', 'Computer Science', '9876543210'),
    ('Prof. Margi Maam', 'margi@college.com', 'teacher123', 'Computer Science', '9876543211'),
]
c.executemany("INSERT INTO teachers (name,email,password,department,phone) VALUES (?,?,?,?,?)", teachers)

# ✅ 10 STUDENTS ADDED
students = [
    ('Rahul Sharma','CSE2021001','Second Year','Computer Science','student123','rahul@student.edu','9123456780'),
    ('Priya Patel','CSE2021002','Second Year','Computer Science','student123','priya@student.edu','9123456781'),
    ('Amit Verma','CSE2021003','Second Year','Computer Science','student123','amit@student.edu','9123456782'),
    ('Sneha Iyer','CSE2021004','Second Year','Computer Science','student123','sneha@student.edu','9123456783'),
    ('Rohit Kumar','CSE2021005','Second Year','Computer Science','student123','rohit@student.edu','9123456784'),
    ('Neha Singh','CSE2021006','Second Year','Computer Science','student123','neha@student.edu','9123456785'),
    ('Karan Mehta','CSE2021007','Second Year','Computer Science','student123','karan@student.edu','9123456786'),
    ('Pooja Shah','CSE2021008','Second Year','Computer Science','student123','pooja@student.edu','9123456787'),
    ('Vikas Gupta','CSE2021009','Second Year','Computer Science','student123','vikas@student.edu','9123456788'),
    ('Anjali Desai','CSE2021010','Second Year','Computer Science','student123','anjali@student.edu','9123456789'),
]
c.executemany("INSERT INTO students (name,roll_no,year,branch,password,email,phone) VALUES (?,?,?,?,?,?,?)", students)

# Subjects
subjects = [
    ('Data Structures','CS201',1,'Second Year','Computer Science'),
    ('Web Development','CS202',2,'Second Year','Computer Science'),
    ('Database Management','CS203',1,'Second Year','Computer Science'),
    ('Operating Systems','CS204',2,'Second Year','Computer Science'),
]
c.executemany("INSERT INTO subjects (subject_name,subject_code,teacher_id,year,branch) VALUES (?,?,?,?,?)", subjects)

# ✅ ENROLL ALL 10 STUDENTS IN ALL SUBJECTS
enrollments = []
for subject_id in range(1, 5):
    for student_id in range(1, 11):  # 10 students
        enrollments.append((student_id, subject_id))

c.executemany("INSERT INTO enrollments (student_id,subject_id) VALUES (?,?)", enrollments)

# ================= SAMPLE ATTENDANCE =================
print("📊 Adding sample attendance...")

today = datetime.now()
dates = [
    (today - timedelta(days=2)).strftime('%Y-%m-%d'),
    (today - timedelta(days=1)).strftime('%Y-%m-%d'),
]

attendance_data = []

# Auto generate attendance for all
for student_id in range(1, 11):
    for subject_id in range(1, 5):
        attendance_data.append((student_id, subject_id, dates[0], 'Present' if student_id % 2 == 0 else 'Absent', 1))
        attendance_data.append((student_id, subject_id, dates[1], 'Present', 1))

c.executemany("""
INSERT INTO attendance (student_id,subject_id,date,status,marked_by)
VALUES (?,?,?,?,?)
""", attendance_data)

conn.commit()
conn.close()

print("\n🎉 DATABASE READY WITH 10 STUDENTS & FULL DATA!")