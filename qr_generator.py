import qrcode
import uuid
import datetime
import sqlite3
import os

def generate_qr_session(course_id, duration_minutes=15):
    """Generate a secure time-limited QR code for a course session"""
    session_token = str(uuid.uuid4())
    now = datetime.datetime.now()
    expires_at = now + datetime.timedelta(minutes=duration_minutes)
    
    # Save session to database
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO qr_session (course_id, qr_token, generated_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (course_id, session_token, now.strftime('%Y-%m-%d %H:%M:%S'), 
          expires_at.strftime('%Y-%m-%d %H:%M:%S')))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Generate QR Code image
    qr_data = f"https://attendance.csdept.edu/mark/qr?token={session_token}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filepath = f"static/qr_codes/session_{session_id}.png"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath)
    
    return {
        'session_id': session_id,
        'token': session_token,
        'expires_at': expires_at.strftime('%H:%M:%S'),
        'qr_path': filepath
    }

def validate_qr_scan(student_id, token):
    """Validate a scanned QR token and mark attendance if valid"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Check token validity
    cursor.execute("""
        SELECT session_id, course_id FROM qr_session 
        WHERE qr_token=? AND is_active=1 AND expires_at > ?
    """, (token, now))
    
    session = cursor.fetchone()
    if not session:
        conn.close()
        return False, "Invalid or expired QR code"
        
    course_id = session[0]
    
    # Mark attendance
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    time = datetime.datetime.now().strftime('%H:%M:%S')
    
    try:
        cursor.execute("""
            INSERT INTO attendance (student_id, course_id, date, time, method, status)
            VALUES (?, ?, ?, ?, 'QR', 'Present')
        """, (student_id, course_id, date, time))
        conn.commit()
        success = True
        msg = "Attendance marked successfully"
    except sqlite3.IntegrityError:
        success = False
        msg = "Attendance already marked"
        
    conn.close()
    return success, msg
