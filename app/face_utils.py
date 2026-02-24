import numpy as np
import os
import pickle
import cv2
from flask import current_app
from datetime import datetime


def allowed_file(filename):
    """Check if file extension is allowed."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def encode_face_from_image(image_path):
    """
    Generate face encoding from an image file.
    Returns encoding array or None if no face detected.
    """
    import face_recognition
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            return None, "No face detected in the image"
        if len(encodings) > 1:
            return None, "Multiple faces detected. Please use an image with a single face"
        return encodings[0], None
    except Exception as e:
        return None, str(e)


def save_encoding(encoding, student_id, encodings_folder):
    """Save face encoding to disk."""
    try:
        os.makedirs(encodings_folder, exist_ok=True)
        encoding_path = os.path.join(encodings_folder, f"{student_id}.pkl")
        with open(encoding_path, 'wb') as f:
            pickle.dump(encoding, f)
        return encoding_path, None
    except Exception as e:
        return None, str(e)


def load_encoding(encoding_path):
    """Load a face encoding from disk."""
    try:
        with open(encoding_path, 'rb') as f:
            return pickle.load(f), None
    except Exception as e:
        return None, str(e)


def load_all_encodings(encodings_folder):
    """
    Load all face encodings from the encodings folder.
    Returns dict {student_id: encoding}
    """
    encodings = {}
    if not os.path.exists(encodings_folder):
        return encodings

    for filename in os.listdir(encodings_folder):
        if filename.endswith('.pkl'):
            student_id = filename[:-4]  # Remove .pkl
            path = os.path.join(encodings_folder, filename)
            enc, err = load_encoding(path)
            if enc is not None:
                encodings[student_id] = enc
    return encodings


def recognize_faces_in_frame(frame, known_encodings, tolerance=0.5):
    """
    Detect and recognize faces in a single frame.
    Returns list of dicts: [{name, student_db_id, confidence, location}]
    """
    import face_recognition
    # Resize frame for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    results = []
    for face_encoding, face_location in zip(face_encodings, face_locations):
        name = "Unknown"
        student_db_key = None
        confidence = 0.0

        if known_encodings:
            keys = list(known_encodings.keys())
            enc_list = list(known_encodings.values())

            distances = face_recognition.face_distance(enc_list, face_encoding)  # noqa
            best_match_idx = np.argmin(distances)
            best_distance = distances[best_match_idx]

            if best_distance <= tolerance:
                name = keys[best_match_idx]
                student_db_key = keys[best_match_idx]
                confidence = 1.0 - best_distance

        # Scale back up face locations (we resized by 0.5)
        top, right, bottom, left = face_location
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        results.append({
            'name': name,
            'student_db_key': student_db_key,
            'confidence': confidence,
            'location': (top, right, bottom, left)
        })

    return results


def draw_recognition_results(frame, results, student_names):
    """
    Draw bounding boxes and name labels on a frame.
    student_names: dict {student_id_string: full_name}
    """
    for result in results:
        top, right, bottom, left = result['location']
        name = result['name']
        confidence = result['confidence']

        if name != "Unknown" and name in student_names:
            display_name = student_names[name]
            color = (0, 255, 0)  # Green for recognized
            label = f"{display_name} ({confidence*100:.1f}%)"
        else:
            display_name = "Unknown"
            color = (0, 0, 255)  # Red for unknown
            label = "Unknown"

        # Draw box
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        # Draw label background
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        # Draw name
        cv2.putText(frame, label, (left + 6, bottom - 10),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1)

    return frame
