from flask import Flask, render_template, request, jsonify, redirect, url_url, session
import sqlite3
import os
import datetime
from face_recognition_module import recognize_face
from qr_generator import generate_qr_session

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'attendance.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/faculty/dashboard')
def faculty_dashboard():
    if 'faculty_id' not in session:
        return redirect(url_for('faculty_login'))
    
    conn = get_db()
    cursor = conn.cursor()
    # Get attendance stats
    cursor.execute("SELECT count(*) as total FROM student")
    total_students = cursor.fetchone()['total']
    
    today = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT count(DISTINCT student_id) as present FROM attendance WHERE date = ?", (today,))
    present_today = cursor.fetchone()['present']
    
    absent_today = total_students - present_today
    attendance_rate = round((present_today / total_students) * 100, 1) if total_students > 0 else 0
    
    # Get today's log
    cursor.execute("""
        SELECT s.roll_number, s.name, c.course_name, a.time, a.method, a.status 
        FROM attendance a
        JOIN student s ON a.student_id = s.student_id
        JOIN course c ON a.course_id = c.course_id
        WHERE a.date = ?
        ORDER BY a.time DESC LIMIT 10
    """, (today,))
    recent_logs = cursor.fetchall()
    conn.close()
    
    return render_template('faculty_dashboard.html', 
                          total=total_students, 
                          present=present_today, 
                          absent=absent_today, 
                          rate=attendance_rate,
                          logs=recent_logs)

@app.route('/api/mark_attendance/face', methods=['POST'])
def mark_face_attendance():
    image_data = request.json.get('image')
    course_id = request.json.get('course_id')
    
    student_id = recognize_face(image_data)
    
    if student_id:
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime('%H:%M:%S')
        
        # Check if already marked
        cursor.execute("SELECT * FROM attendance WHERE student_id=? AND course_id=? AND date=?", 
                      (student_id, course_id, date))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'warning', 'message': 'Attendance already marked'})
            
        cursor.execute("""
            INSERT INTO attendance (student_id, course_id, date, time, method, status)
            VALUES (?, ?, ?, ?, 'Face', 'Present')
        """, (student_id, course_id, date, time))
        conn.commit()
        
        cursor.execute("SELECT name FROM student WHERE student_id=?", (student_id,))
        student_name = cursor.fetchone()['name']
        conn.close()
        
        return jsonify({'status': 'success', 'message': f'Attendance marked for {student_name}'})
    else:
        return jsonify({'status': 'error', 'message': 'Face not recognized'})

if __name__ == '__main__':
    app.run(debug=True)
