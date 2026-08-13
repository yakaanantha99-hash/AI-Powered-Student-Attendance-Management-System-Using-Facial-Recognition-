import sqlite3
import os

def init_db():
    if os.path.exists('attendance.db'):
        os.remove('attendance.db')
        
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE student (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        roll_number TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        year INTEGER NOT NULL,
        face_encoding_path TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE faculty (
        faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        subject TEXT NOT NULL
    )''')
    
    cursor.execute('''
    CREATE TABLE course (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        course_code TEXT UNIQUE NOT NULL,
        faculty_id INTEGER,
        schedule TEXT,
        FOREIGN KEY (faculty_id) REFERENCES faculty (faculty_id)
    )''')
    
    cursor.execute('''
    CREATE TABLE attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        method TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES student (student_id),
        FOREIGN KEY (course_id) REFERENCES course (course_id),
        UNIQUE(student_id, course_id, date)
    )''')
    
    cursor.execute('''
    CREATE TABLE qr_session (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        qr_token TEXT UNIQUE NOT NULL,
        generated_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (course_id) REFERENCES course (course_id)
    )''')
    
    # Insert sample data
    cursor.execute("INSERT INTO faculty (name, email, department, subject) VALUES ('Dr. Sharma', 'sharma@university.edu', 'Computer Science', 'Data Structures')")
    cursor.execute("INSERT INTO course (course_name, course_code, faculty_id) VALUES ('Data Structures', 'CS301', 1)")
    
    students = [
        ('Aarav Singh', 'aarav@university.edu', 'CS2023001', 'CS', 3),
        ('Ananya Gupta', 'ananya@university.edu', 'CS2023002', 'CS', 3),
        ('Rohan Mehta', 'rohan@university.edu', 'CS2023003', 'CS', 3)
    ]
    cursor.executemany("INSERT INTO student (name, email, roll_number, department, year) VALUES (?, ?, ?, ?, ?)", students)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
