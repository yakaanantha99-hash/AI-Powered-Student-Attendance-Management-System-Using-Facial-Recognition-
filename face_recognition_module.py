import cv2
import face_recognition
import numpy as np
import base64
import sqlite3
import os

def load_known_faces():
    """Load known face encodings from database"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, face_encoding_path FROM student")
    records = cursor.fetchall()
    
    known_face_encodings = []
    known_face_ids = []
    
    for record in records:
        student_id, path = record
        if path and os.path.exists(path):
            encoding = np.load(path)
            known_face_encodings.append(encoding)
            known_face_ids.append(student_id)
            
    conn.close()
    return known_face_encodings, known_face_ids

def decode_base64_image(base64_string):
    """Convert base64 string to OpenCV image"""
    encoded_data = base64_string.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def recognize_face(base64_image):
    """Process image and return student_id if recognized"""
    img = decode_base64_image(base64_image)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_img)
    if not face_locations:
        return None
        
    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
    known_encodings, known_ids = load_known_faces()
    
    if not known_encodings:
        return None
        
    # Check first face found
    matches = face_recognition.compare_faces(known_encodings, face_encodings[0], tolerance=0.5)
    face_distances = face_recognition.face_distance(known_encodings, face_encodings[0])
    
    best_match_index = np.argmin(face_distances)
    if matches[best_match_index]:
        return known_ids[best_match_index]
        
    return None

def register_new_face(student_id, images):
    """Process multiple images to create robust encoding for a new student"""
    encodings = []
    for img_path in images:
        img = face_recognition.load_image_file(img_path)
        locations = face_recognition.face_locations(img)
        if locations:
            encoding = face_recognition.face_encodings(img, locations)[0]
            encodings.append(encoding)
            
    if encodings:
        avg_encoding = np.mean(encodings, axis=0)
        save_path = f'encodings/{student_id}.npy'
        np.save(save_path, avg_encoding)
        
        # Update database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE student SET face_encoding_path=? WHERE student_id=?", 
                      (save_path, student_id))
        conn.commit()
        conn.close()
        return True
    return False
