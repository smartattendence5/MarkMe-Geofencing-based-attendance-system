import sqlite3, os, random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "attendance.db")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("🗑️  Old database deleted")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

print("📦 Creating tables...")

c.executescript('''
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL, department TEXT, phone TEXT
);
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, roll_no TEXT UNIQUE NOT NULL,
    year TEXT, branch TEXT,
    password TEXT NOT NULL DEFAULT "student123",
    email TEXT, phone TEXT
);
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL, subject_code TEXT,
    teacher_id INTEGER NOT NULL, year TEXT, branch TEXT,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL, subject_id INTEGER NOT NULL,
    enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE(student_id, subject_id)
);
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL, subject_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ("Present","Absent")),
    marked_by INTEGER, marked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE(student_id, subject_id, date)
);
CREATE TABLE student_temp_locations (
    student_id INTEGER PRIMARY KEY, latitude REAL NOT NULL,
    longitude REAL NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);
CREATE TABLE teacher_temp_locations (
    teacher_id INTEGER PRIMARY KEY, latitude REAL NOT NULL,
    longitude REAL NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);
CREATE TABLE active_attendance_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL, teacher_id INTEGER NOT NULL,
    teacher_latitude REAL NOT NULL, teacher_longitude REAL NOT NULL,
    date TEXT NOT NULL, start_time TEXT DEFAULT CURRENT_TIMESTAMP,
    end_time TEXT NOT NULL,
    FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);
''')
print("✅ Tables created")

# ══ TEACHERS ══
c.executemany(
    "INSERT INTO teachers (name,email,password,department,phone) VALUES (?,?,?,?,?)",
    [
        ('Dr. Shitole Sir',  'shitole@college.com','teacher123','Computer Science',      '9876543210'),
        ('Prof. Margi Maam', 'margi@college.com',  'teacher123','Computer Science',      '9876543211'),
        ('Dr. Patil Sir',    'patil@college.com',  'teacher123','Electronics',           '9876543212'),
        ('Prof. Nehal Maam', 'nehal@college.com',  'teacher123','Information Technology','9876543213'),
    ]
)
print("✅ Teachers inserted (4)")

# ══ SUBJECTS — 4 per teacher = 2 subjects Branch-A + 2 subjects Branch-B ══
c.executemany(
    "INSERT INTO subjects (subject_name,subject_code,teacher_id,year,branch) VALUES (?,?,?,?,?)",
    [
        # Shitole (1) → 2 CSE 3rd yr + 2 DS 3rd yr
        ('Machine Learning',    'CSE301', 1, 'Third Year', 'Computer Science'),
        ('Digital Electronics', 'CSE302', 1, 'Third Year', 'Computer Science'),
        ('Data Mining',         'DS301',  1, 'Third Year', 'Data Science'),
        ('Statistical Analysis','DS302',  1, 'Third Year', 'Data Science'),

        # Margi (2) → 2 CSE 3rd yr + 2 ENC 3rd yr
        ('Data Structures & Algorithms','CSE303', 2, 'Third Year', 'Computer Science'),
        ('Object Oriented Programming', 'CSE304', 2, 'Third Year', 'Computer Science'),
        ('Signals & Systems',           'ENC301', 2, 'Third Year', 'Electronics'),
        ('Microcontrollers',            'ENC302', 2, 'Third Year', 'Electronics'),

        # Patil (3) → 2 ENC 3rd yr + 2 DS 3rd yr
        ('Analog Electronics',   'ENC303', 3, 'Third Year', 'Electronics'),
        ('Communication Systems','ENC304', 3, 'Third Year', 'Electronics'),
        ('AI for Data Science',  'DS303',  3, 'Third Year', 'Data Science'),
        ('Data Visualization',   'DS304',  3, 'Third Year', 'Data Science'),

        # Nehal (4) → 2 IT 4th yr + 2 CSE 3rd yr
        ('Cloud Computing', 'IT401',  4, 'Fourth Year', 'Information Technology'),
        ('Cyber Security',  'IT402',  4, 'Fourth Year', 'Information Technology'),
        ('Computer Networks','CSE305', 4, 'Third Year', 'Computer Science'),
        ('Web Development', 'CSE306', 4, 'Third Year', 'Computer Science'),
    ]
)
conn.commit()
print("✅ Subjects inserted: 4 teachers x 4 subjects (2+2 per branch)")

# ══ STUDENTS ══
cse_students = [
    ('Rahul Sharma', 'CSE01','Third Year','Computer Science','student123','cse01@student.edu','9100000001'),
    ('Priya Patel',  'CSE02','Third Year','Computer Science','student123','cse02@student.edu','9100000002'),
    ('Amit Verma',   'CSE03','Third Year','Computer Science','student123','cse03@student.edu','9100000003'),
    ('Sneha Iyer',   'CSE04','Third Year','Computer Science','student123','cse04@student.edu','9100000004'),
    ('Rohit Kumar',  'CSE05','Third Year','Computer Science','student123','cse05@student.edu','9100000005'),
    ('Neha Singh',   'CSE06','Third Year','Computer Science','student123','cse06@student.edu','9100000006'),
    ('Karan Mehta',  'CSE07','Third Year','Computer Science','student123','cse07@student.edu','9100000007'),
    ('Pooja Shah',   'CSE08','Third Year','Computer Science','student123','cse08@student.edu','9100000008'),
    ('Vikas Gupta',  'CSE09','Third Year','Computer Science','student123','cse09@student.edu','9100000009'),
    ('Anjali Desai', 'CSE10','Third Year','Computer Science','student123','cse10@student.edu','9100000010'),
]
enc_students = [
    ('Arjun Patil',    'ENC01','Third Year','Electronics','student123','enc01@student.edu','9200000001'),
    ('Riya Kulkarni',  'ENC02','Third Year','Electronics','student123','enc02@student.edu','9200000002'),
    ('Saurabh Shinde', 'ENC03','Third Year','Electronics','student123','enc03@student.edu','9200000003'),
    ('Pallavi Joshi',  'ENC04','Third Year','Electronics','student123','enc04@student.edu','9200000004'),
    ('Nikhil Rane',    'ENC05','Third Year','Electronics','student123','enc05@student.edu','9200000005'),
    ('Divya Nair',     'ENC06','Third Year','Electronics','student123','enc06@student.edu','9200000006'),
    ('Sahil Bhosale',  'ENC07','Third Year','Electronics','student123','enc07@student.edu','9200000007'),
    ('Shreya Kadam',   'ENC08','Third Year','Electronics','student123','enc08@student.edu','9200000008'),
    ('Omkar Deshpande','ENC09','Third Year','Electronics','student123','enc09@student.edu','9200000009'),
    ('Ankita Salvi',   'ENC10','Third Year','Electronics','student123','enc10@student.edu','9200000010'),
]
ds_students = [
    ('Tanmay More',    'DS01','Third Year','Data Science','student123','ds01@student.edu','9300000001'),
    ('Ishika Tiwari',  'DS02','Third Year','Data Science','student123','ds02@student.edu','9300000002'),
    ('Yash Jadhav',    'DS03','Third Year','Data Science','student123','ds03@student.edu','9300000003'),
    ('Rutuja Chavan',  'DS04','Third Year','Data Science','student123','ds04@student.edu','9300000004'),
    ('Akash Pawar',    'DS05','Third Year','Data Science','student123','ds05@student.edu','9300000005'),
    ('Mrunali Gaikwad','DS06','Third Year','Data Science','student123','ds06@student.edu','9300000006'),
    ('Pratik Wagh',    'DS07','Third Year','Data Science','student123','ds07@student.edu','9300000007'),
    ('Komal Kale',     'DS08','Third Year','Data Science','student123','ds08@student.edu','9300000008'),
    ('Rohan Sabale',   'DS09','Third Year','Data Science','student123','ds09@student.edu','9300000009'),
    ('Sayali Mane',    'DS10','Third Year','Data Science','student123','ds10@student.edu','9300000010'),
]
it_raw = [
    ('IT02','Vaishnavi Hemant Bari'),('IT03','Atreyi Sanjoy Bhattacharyya'),
    ('IT05','Shruti Harichandra Bodke'),('IT06','Saniya Subodh Chavan'),
    ('IT07','Anjali Rajesh Choudhary'),('IT08','Nidhi Babu Darge'),
    ('IT09','Soumya Das'),('IT10','Harsha Sanjay Deore'),
    ('IT11','Gauri Vijay Gadadhe'),('IT12','Vedika Mahesh Ghankutkar'),
    ('IT13','Sanika Narendra Gire'),('IT14','Srushti Anil Gunjal'),
    ('IT15','Aruna Hariharan'),('IT16','Akshata Anant Haryan'),
    ('IT17','Trupti Yashwant Hote'),('IT18','Namita Santosh Jadhav'),
    ('IT19','Sakshi Gopinath Jadhav'),('IT20','Bhoomi Sechulal Jaiswal'),
    ('IT21','Anusha Sanjay Jha'),('IT22','Sneha Jha'),
    ('IT23','Anjali Ashok Kadam'),('IT24','Sakshi Prakash Kadam'),
    ('IT25','Tanavi Ashok Kadam'),('IT26','Vedangi Santosh Kadam'),
    ('IT27','Kirti Sandesh Kathole'),('IT28','Janvi Narshyam Kawtikwar'),
    ('IT29','Swati Salikram Kesarwani'),('IT30','Vaishnavi Mahendra Khedekar'),
    ('IT31','Zainab Aftab Kherani'),('IT32','Srushti Sanjay Khillare'),
    ('IT33','Diya Vasudev Koli'),('IT35','Vasudha Anand Kulkarni'),
    ('IT36','Aishwarya Suresh Kurade'),('IT37','Samriddhy Vilas Lade'),
    ('IT38','Dhanshri Ajaykumar Mankar'),('IT39','Shruti Suresh Meshram'),
    ('IT40','Darshita Atish Mhapankar'),('IT41','Janhvi Ganesh More'),
    ('IT42','Nikita Chandrashekhar Naik'),('IT43','Kiran Samadhan Padghan'),
    ('IT44','Maitree Ranjeet Pandey'),('IT45','Janhavi Tushar Paranjape'),
    ('IT46','Devyani Pravin Patil'),('IT47','Janhavi Suraj Patil'),
    ('IT48','Prachi Deepak Patil'),('IT49','Tanvi Vijay Patil'),
    ('IT50','Tanvi Sandeep Patil'),('IT51','Vaishnavi Anil Patil'),
    ('IT52','Isha Pradeep Pawar'),('IT53','Sakshi Sopan Pawar'),
    ('IT55','Akanksha Rajesh Pukale'),('IT56','Anushka Raghav'),
    ('IT57','Khushboo Raina'),('IT58','Kirti Gayaprasad Rajbhar'),
    ('IT59','Laxmi Mahadev Ranjvan'),('IT60','Ritika Deepak Sakpal'),
    ('IT61','Rameen Nooralam Shaikh'),('IT62','Shaikh Reeba Mohammed Tarique'),
    ('IT63','Shaikh Reena Mohammed Tarique'),('IT64','Vagisha Sharma'),
    ('IT65','Sneha Milind Shejwal'),('IT66','Chaitali Jagadish Shetty'),
    ('IT67','Sreysha Jagdish Shetty'),('IT68','Manasvi Manohar Shinde'),
    ('IT69','Surabhi Sanjay Shirsat'),('IT70','Sneha Rupesh Singh'),
    ('IT71','Smita Ashok Sunka'),('IT72','Ketaki Vishwanath Tari'),
    ('IT73','Vaishnavi Kisanrao Tathe'),('IT74','Shreya Tripathi'),
    ('IT75','Raksha Dinesh Trivedi'),('IT76','Bhakti Devesh Walimbe'),
    ('IT77','Sneha Balraje Warale'),('IT78','Ankita Yadav'),
    ('IT79','Isha Rammanohar Yadav'),('IT80','Vaidehi Sandip Yadav'),
    ('IT81','Sonal Navnath Bhosale'),('IT82','Siddhi Sanjay Sonawane'),
    ('IT83','Siddhi Rajendra Kumbhar'),
]
it_students = [
    (name, roll, 'Fourth Year', 'Information Technology', 'student123',
     f"it{roll[2:]}@student.edu", f"9400{roll[2:].zfill(6)}")
    for roll, name in it_raw
]

all_students = cse_students + enc_students + ds_students + it_students
c.executemany(
    "INSERT INTO students (name,roll_no,year,branch,password,email,phone) VALUES (?,?,?,?,?,?,?)",
    all_students
)
conn.commit()
print(f"✅ Students: CSE=10, ENC=10, DS=10, IT={len(it_students)} → Total={len(all_students)}")

# ══ FETCH IDs ══
def sids(branch):
    return [r[0] for r in c.execute(
        "SELECT id FROM students WHERE branch=? ORDER BY id",(branch,)).fetchall()]

def subj_ids(teacher_id, branch):
    return [r[0] for r in c.execute(
        "SELECT id FROM subjects WHERE teacher_id=? AND branch=? ORDER BY id",(teacher_id,branch)).fetchall()]

cse_ids = sids('Computer Science')
enc_ids = sids('Electronics')
ds_ids  = sids('Data Science')
it_ids  = sids('Information Technology')

sh_cse = subj_ids(1,'Computer Science')
sh_ds  = subj_ids(1,'Data Science')
ma_cse = subj_ids(2,'Computer Science')
ma_enc = subj_ids(2,'Electronics')
pa_enc = subj_ids(3,'Electronics')
pa_ds  = subj_ids(3,'Data Science')
ne_it  = subj_ids(4,'Information Technology')
ne_cse = subj_ids(4,'Computer Science')

print(f"\nSubject IDs:")
print(f"  Shitole→ CSE:{sh_cse} DS:{sh_ds}")
print(f"  Margi  → CSE:{ma_cse} ENC:{ma_enc}")
print(f"  Patil  → ENC:{pa_enc} DS:{pa_ds}")
print(f"  Nehal  → IT:{ne_it}  CSE:{ne_cse}")

# ══ ENROLLMENTS ══
enr = []
for sid in cse_ids:
    for s in sh_cse + ma_cse + ne_cse:   # all 6 CSE subjects
        enr.append((sid, s))
for sid in enc_ids:
    for s in ma_enc + pa_enc:             # all 4 ENC subjects
        enr.append((sid, s))
for sid in ds_ids:
    for s in sh_ds + pa_ds:               # all 4 DS subjects
        enr.append((sid, s))
for sid in it_ids:
    for s in ne_it:                        # 2 IT subjects
        enr.append((sid, s))

c.executemany("INSERT OR IGNORE INTO enrollments (student_id,subject_id) VALUES (?,?)", enr)
conn.commit()
print(f"✅ Enrollments: {len(enr)} records")

# ══ ATTENDANCE — 15 weekday dates ══
def get_dates(n=15):
    dates, d = [], datetime.now() - timedelta(days=1)
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(d.strftime('%Y-%m-%d'))
        d -= timedelta(days=1)
    return dates

dates = get_dates(15)

def gen_att(student_ids, subject_ids, teacher_id, seed=0):
    rng = random.Random(42 + seed)
    recs = []
    for sid in student_ids:
        tendency = rng.uniform(0.45, 0.97)
        for subj in subject_ids:
            for date in dates:
                status = 'Present' if rng.random() < tendency else 'Absent'
                recs.append((sid, subj, date, status, teacher_id))
    return recs

att = []
att += gen_att(cse_ids, sh_cse, 1, seed=0)
att += gen_att(ds_ids,  sh_ds,  1, seed=1)
att += gen_att(cse_ids, ma_cse, 2, seed=2)
att += gen_att(enc_ids, ma_enc, 2, seed=3)
att += gen_att(enc_ids, pa_enc, 3, seed=4)
att += gen_att(ds_ids,  pa_ds,  3, seed=5)
att += gen_att(it_ids,  ne_it,  4, seed=6)
att += gen_att(cse_ids, ne_cse, 4, seed=7)

c.executemany(
    "INSERT OR IGNORE INTO attendance (student_id,subject_id,date,status,marked_by) VALUES (?,?,?,?,?)",
    att
)
conn.commit()
conn.close()

print(f"\n🎉 DATABASE FULLY READY!")
print(f"{'─'*60}")
print(f"  👩‍🏫 Teachers   : 4")
print(f"  📚 Subjects   : 16  (each teacher = 2 subjects × 2 branches)")
print(f"  🎓 Students   : {len(all_students)}  (CSE=10, ENC=10, DS=10, IT={len(it_students)})")
print(f"  📅 Attendance : {len(att)} records  ({len(dates)} class dates)")
print(f"{'─'*60}")
print(f"\n📋 TEACHER LOGINS  (password: teacher123)")
print(f"  shitole@college.com → Machine Learning, Digital Electronics (CSE) + Data Mining, Statistical Analysis (DS)")
print(f"  margi@college.com   → DSA, OOPs (CSE) + Signals & Systems, Microcontrollers (ENC)")
print(f"  patil@college.com   → Analog Electronics, Comm Systems (ENC) + AI for DS, Data Visualization (DS)")
print(f"  nehal@college.com   → Cloud Computing, Cyber Security (IT) + Computer Networks, Web Dev (CSE)")
print(f"\n📋 STUDENT LOGINS  (password: student123)")
print(f"  CSE01-CSE10 | ENC01-ENC10 | DS01-DS10 | IT02-IT83")