# User model

from datetime import datetime, timedelta , timezone

from sqlalchemy import ForeignKey
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from collections import defaultdict, deque
import math
import face_recognition
import os
import cv2
import numpy as np
import pickle
from tqdm import tqdm
import time
import warnings
from deepface import DeepFace
warnings.filterwarnings("ignore")





# Get the current time in UTC
now_utc = datetime.now(timezone.utc)

# Define the time difference between UTC and Egypt time (UTC+2)
egypt_tz = timezone(timedelta(hours=2))

# Convert UTC time to Egypt time
now_egypt = now_utc.astimezone(egypt_tz)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100))
    photo = db.Column(db.String(100))
    office = db.Column(db.String(50))
# Employee model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)


    job_start_time = db.Column(db.Time, nullable=False)
    job_end_time = db.Column(db.Time, nullable=False)
    sat = db.Column(db.Boolean, default=False)
    sun = db.Column(db.Boolean, default=False)
    mon = db.Column(db.Boolean, default=False)
    tues = db.Column(db.Boolean, default=False)
    wed = db.Column(db.Boolean, default=False)
    thr = db.Column(db.Boolean, default=False)
    fri = db.Column(db.Boolean, default=False)
    certificate = db.Column(db.String(100))
    graduation_year = db.Column(db.String(4))
    employment_start_year = db.Column(db.String(4))

    office_name = db.Column(db.String(50))

    period = db.Column(db.String(50))
    employment_id = db.Column(db.String(10))
    nat_id = db.Column(db.String(14))
    name = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    sec_phone_number = db.Column(db.String(15))
    gender = db.Column(db.String(10), nullable=False)
    exp = db.Column(db.String(3))
    exp_type = db.Column(db.String(50))
    social = db.Column(db.String(50))
    religion = db.Column(db.String(50))
    job_name_modli = db.Column(db.String(50))
    job_name_card = db.Column(db.String(50))

    job_type = db.Column(db.String(50))
    emp_type = db.Column(db.String(50))
    grade = db.Column(db.String(50))
    level = db.Column(db.String(50))
    arda_points = db.Column(db.Integer , nullable=False)
    sanwya_points = db.Column(db.Integer , nullable=False )
    tar7eel_points = db.Column(db.Integer , nullable=False)
    doc_number = db.Column(db.Integer , nullable=False )
    insurance_number = db.Column(db.Integer , nullable=False )
    photo =db.Column(db.String(255))
    active =db.Column(db.String(255))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    period = db.Column(db.String(50), nullable=False)
    check_in_time = db.Column(db.Time )
    check_out_time = db.Column(db.Time)
    
class OfficialHoliday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    submit_date = db.Column(db.Date, nullable=False, default=datetime.now(timezone.utc))
    name = db.Column(db.String(100))
    type = db.Column(db.String(50))   
    
class JobScheduleOverride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Changed to db.Date to store only the date
    job_start_time = db.Column(db.Time, nullable=False)
    job_end_time = db.Column(db.Time, nullable=False)
    submit_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone(timedelta(hours=2))))  # Egypt time

    

    def __repr__(self):
        return f'<JobScheduleOverride {self.date} - {self.job_start_time} to {self.job_end_time}>'
    
    
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    clinic_type = db.Column(db.String(50), nullable=False)
    out_time = db.Column(db.Time, nullable=True)  # Make nullable if it's optional
    back_time = db.Column(db.Time, nullable=True)  # Make nullable if it's optional
    diagnosis = db.Column(db.Text, nullable=True)  # Make nullable if it's optional
    date = db.Column(db.Date, nullable=False)  # Adjust if you need DateTime
    submit_date = db.Column(db.Date, nullable=False)
    approval_status = db.Column(db.String(50), default='Pending')
    from_time = db.Column(db.Time, nullable=False)
    employee = db.relationship('Employee', backref=db.backref('clinics', lazy=True))
    
class Momrya(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    out_time = db.Column(db.Time, nullable=True)  # Make nullable if it's optional
    back_time = db.Column(db.Time, nullable=True)  # Make nullable if it's optional
    reason = db.Column(db.Text, nullable=True)  # Make nullable if it's optional
    date = db.Column(db.Date, nullable=False)  # Adjust if you need DateTime
    to_date = db.Column(db.Date, nullable=False)  # Adjust if you need DateTime
    submit_date = db.Column(db.Date, nullable=False)
    approval_status = db.Column(db.String(50), default='Pending')
    from_time = db.Column(db.Time, nullable=True)
    employee = db.relationship('Employee', backref=db.backref('momryas', lazy=True))

class Ezn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    from_time = db.Column(db.Time, nullable=False)
    to_time = db.Column(db.Time, nullable=False)
    out_time = db.Column(db.Time, nullable=False)
    back_time = db.Column(db.Time, nullable=False)
    submit_date = db.Column(db.Date, nullable=False)
    approval_status = db.Column(db.String(50), default='Pending')

    employee = db.relationship('Employee', backref=db.backref('ezns', lazy=True))

class Agaza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    from_date = db.Column(db.Date)
    to_date = db.Column(db.Date)
    submit_date = db.Column(db.Date)
    type = db.Column(db.String(255))
    alternative = db.Column(db.String(255))
    approval_status = db.Column(db.String(50), default='Pending')
    notes_agaza = db.Column(db.String(255))
    notes_agaza_manager = db.Column(db.String(255))
    deducat = db.Column(db.String(255))  # New column added
    employee = db.relationship('Employee', backref=db.backref('agazas', lazy=True))


class Altmas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    petition = db.Column(db.Text, nullable=False)
    approval_status = db.Column(db.String(50), default='Pending')
    submit_date = db.Column(db.Date, nullable=False)

    
    employee = db.relationship('Employee', backref=db.backref('altmases', lazy=True))

class Approvals(db.Model):
    __tablename__ = 'approvals'
    
    approval_id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(50), nullable=False)
    request_id = db.Column(db.Integer, nullable=False)
    
    office_manager_approval_status = db.Column(db.String(50), default='Pending')
    employee_affairs_approval_status = db.Column(db.String(50), default='Pending')
    secretary_approval_status = db.Column(db.String(50), default='Pending')
    vice_president_approval_status = db.Column(db.String(50), default='Pending')
    president_follower_approval_status = db.Column(db.String(50), default='Pending')
    president_approval_status = db.Column(db.String(50), default='Pending')

    # Index for speeding up queries
    __table_args__ = (
        db.Index('idx_request_type_id', 'request_type', 'request_id'),
    )
    
    def get_request(self):
        """
        Method to retrieve the specific request object.
        """
        if self.request_type == 'agaza':
            return Agaza.query.get(self.request_id)
        elif self.request_type == 'ezn':
            return Ezn.query.get(self.request_id)
        elif self.request_type == 'clinic':
            return Clinic.query.get(self.request_id)
        elif self.request_type == 'altmas':
            return Altmas.query.get(self.request_id)
        else:
            return None
        
    def approval_status_message(self):
        """
        Method to return a custom approval status message based on the sequential approval process.
        """
        # Define the approval stages
        stages = [
            ('office_manager_approval_status', 'في انتظار موافقه رئيس الفرع'),
            ('employee_affairs_approval_status', 'في انتظار موافقه شئون عاملين'),
            ('secretary_approval_status', 'في انتظار موافقة فرع السكرتارية'),
            ('vice_president_approval_status', 'في انتظار موافقة نائب المدير'),
            ('president_follower_approval_status', 'في انتظار متابعة المدير'),
            ('president_approval_status', 'في انتظار موافقة المدير')
        ]
        
        # Initialize counters
        approved_count = 0
        total_stages = len(stages)
        
        for index, (status_field, message) in enumerate(stages):
            status = getattr(self, status_field)
            
            # Check the request type for clinic
            if self.request_type == 'clinic':
                # Increment approved count if status is 'Approved'
                if status == 'Approved':
                    approved_count += 1
                    
                    # If both first and second stages are approved, return fully approved message
                    if approved_count >= 2:
                        return f"تمت الموافقة بالكامل ({approved_count-1} من {2})"
                
                # If status is 'Rejected', return the rejection message
                elif status == 'Rejected':
                    return f"تم رفض الطلب عند مرحلة {message}"
                
                # If status is 'Pending', return the pending message for the current stage
                elif status == 'Pending':
                    return f"{message} ({approved_count} من {2})"
                
                        # Check the request type for clinic
                        
            elif self.request_type == 'momrya':
                # Increment approved count if status is 'Approved'

                if status == 'Approved':
                    approved_count += 1
                    print('approved_count' , approved_count)
                    # If both first and second stages are approved, return fully approved message
                    if approved_count >= 2:
                        return f"تمت الموافقة بالكامل ({approved_count-1} من {2})"
                
                # If status is 'Rejected', return the rejection message
                elif status == 'Rejected':
                    return f"تم رفض الطلب عند مرحلة {message}"
                
                # If status is 'Pending', return the pending message for the current stage
                elif status == 'Pending':
                    return f"{message} ({approved_count} من {2})"
                
                        # Check the request type for clinic                        
            if self.request_type == 'ezn':
                # Increment approved count if status is 'Approved'
                if status == 'Approved':
                    approved_count += 1
                    
                    if approved_count == 6:
                        return f"تمت الموافقة بالكامل ({5} من {5})"
                # If status is 'Rejected', return the rejection message
                elif status == 'Rejected':
                    return f"تم رفض الطلب عند مرحلة {message}"
                
                # If status is 'Pending', return the pending message for the current stage
                elif status == 'Pending':
                    return f"{message} ({approved_count} من {total_stages })"    
            
            else:
                # For non-clinic types, continue with the existing logic
                if status == 'Pending':
                    # Return message for the first pending status
                    return f"{message} ({approved_count} من {total_stages})"
                elif status == 'Approved':
                    approved_count += 1
                elif status == 'Rejected':
                    return f"تم رفض الطلب عند مرحلة {message}"
        
        # If all stages are approved and it's not a clinic type
        return f"تمت الموافقة بالكامل ({approved_count} من {total_stages})"
    
class Appear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, ForeignKey('employee.id'), nullable=False)
    appearance_time = db.Column(db.Time, nullable=False, default=datetime.now().time())
    appearance_date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    
    # Relationship to Employee
    employee = relationship('Employee', back_populates='appearances')

# Establish back_populates in the Employee model
Employee.appearances = relationship('Appear', order_by=Appear.id, back_populates='employee')


def face_confidence(face_distance, face_match_threshold=0.4):
    range = (1.0 - face_match_threshold)
    linear_val = (1.0 - face_distance) / (range * 2.0)
    
    if face_distance > face_match_threshold:
        return str(round(linear_val * 100, 2)) + '%'
    else:
        value = (linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))) * 100
        return str(round(value, 2)) + '%'


class FaceRecognition:
    def __init__(self, data_directory='faces', pickle_file='face_encodings.pkl', timestamps_file='image_timestamps.pkl'):
        self.data_directory = data_directory
        self.pickle_file = pickle_file
        self.timestamps_file = timestamps_file
        self.known_face_encodings = []
        self.known_face_names = []
        self.image_timestamps = {}
        self.recognizing = False
        self.start_time = time.time()

        # Dictionary to store the last 10 matches and their confidence scores for each recognized face
        self.last_10_faces = defaultdict(lambda: deque(maxlen=10))
        self.last_10_confidences = defaultdict(lambda: deque(maxlen=10))

        # To keep track of faces that are currently recognized
        self.current_recognized_faces = set()

        # Load encodings and timestamps if files exist, else encode faces
        if os.path.exists(self.pickle_file) and os.path.exists(self.timestamps_file):
            self.load_encodings()
            self.load_timestamps()
        else:
            self.encode_faces()
            self.save_encodings()
            self.save_timestamps()

        # Initialize the video capture
        self.video_capture = cv2.VideoCapture(0)

        # Check if the camera opened successfully
        if not self.video_capture.isOpened():
            print("Error: Could not open video capture.")
            self.video_capture.release()
            cv2.destroyAllWindows()
            return
        self.frame_count = 0
        self.start_time = time.time()

    def encode_faces(self):
        print(f"Starting encoding process for images in '{self.data_directory}' directory...")
        
        for person_name in tqdm(os.listdir(self.data_directory), desc="Processing directories"):
            person_folder = os.path.join(self.data_directory, person_name)

            if os.path.isdir(person_folder):
                for image_name in tqdm(os.listdir(person_folder), desc=f"Encoding faces for {person_name}"):
                    image_path = os.path.join(person_folder, image_name)
                    modification_time = os.path.getmtime(image_path)

                    # Check if the image is new or modified
                    if (image_path not in self.image_timestamps) or (self.image_timestamps[image_path] < modification_time):
                        face_image = face_recognition.load_image_file(image_path)
                        face_encodings = face_recognition.face_encodings(face_image)

                        if face_encodings:
                            face_encoding = face_encodings[0]
                            self.known_face_encodings.append(face_encoding)
                            self.known_face_names.append(person_name)
                            self.image_timestamps[image_path] = modification_time  # Update timestamp
                        else:
                            print(f"No face found in {image_name}. Skipping...")

        print("Encoding process completed.")

    def save_encodings(self):
        print(f"Saving encodings to {self.pickle_file}...")
        with open(self.pickle_file, 'wb') as f:
            pickle.dump((self.known_face_encodings, self.known_face_names), f)
        print(f"Encodings saved to {self.pickle_file}")

    def load_encodings(self):
        print(f"Loading encodings from {self.pickle_file}...")
        with open(self.pickle_file, 'rb') as f:
            self.known_face_encodings, self.known_face_names = pickle.load(f)
        print(f"Encodings loaded from {self.pickle_file}")

    def save_timestamps(self):
        print(f"Saving image timestamps to {self.timestamps_file}...")
        with open(self.timestamps_file, 'wb') as f:
            pickle.dump(self.image_timestamps, f)
        print(f"Timestamps saved to {self.timestamps_file}")

    def load_timestamps(self):
        print(f"Loading image timestamps from {self.timestamps_file}...")
        with open(self.timestamps_file, 'rb') as f:
            self.image_timestamps = pickle.load(f)
        print(f"Timestamps loaded from {self.timestamps_file}")


    def process_frame(self):
        ret, frame = self.video_capture.read()
        if not ret or frame is None:
            print("Error: Frame capture failed.")
            return None, []

        self.frame_count += 1
        frame = cv2.flip(frame, 1)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Check the frame properties
        print(f"small_frame dtype: {small_frame.dtype}, shape: {small_frame.shape}")

        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
        print(f"rgb_small_frame dtype: {rgb_small_frame.dtype}, shape: {rgb_small_frame.shape}")

        # Detect face locations and encodings in the current frame
        try:
            face_locations = face_recognition.face_locations(rgb_small_frame, number_of_times_to_upsample=2)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        except Exception as e:
            print(f"Error during face recognition: {e}")
            return None, []

        face_scores = []  # List to store face ID and score as dictionaries

        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            # Anti-spoofing check
 #           face_image = rgb_small_frame[top:bottom, left:right]
 #           anti_spoofing_results = DeepFace.extract_faces(
  #              img_path=face_image,
 #               anti_spoofing=True,
 #               enforce_detection=False
  #          )
#

            # Flag to indicate whether spoofing was detected
   #         is_spoofed = False

            # Check anti-spoofing results
  #          for result in anti_spoofing_results:
  #              spoof_score = result.get('is_real', 0)


  #              if spoof_score == False:  # Threshold for spoofing
    #                print("Spoofing detected!")
  #                  is_spoofed = True
  #                  break  # Exit loop since spoofing is detected
#
  #          if is_spoofed:
                # Skip processing and drawing if spoofing is detected
 #               continue

            # Compare the current face encoding to known face encodings
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.4)
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            # Calculate confidence
            confidence = face_confidence(face_distances[best_match_index])
            confidence_value = float(confidence[:-1])  # Remove '%' and convert to float

            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
                face_scores.append({'id': name, 'score': confidence_value})

                # Draw rectangle for known faces
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, f"{name} ({confidence_value:.2f})", (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            else:
                # Handle unknown faces
                print(f"Frame {self.frame_count}: Detected face: Unknown, Confidence: {confidence_value:.2f}")

                # Draw rectangle for unknown faces
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)  # Blue rectangle for unknown faces
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, "Unknown", (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Calculate and display FPS
        elapsed_time = time.time() - self.start_time
        fps = self.frame_count / elapsed_time
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        return frame, face_scores


    def start_recognition(self):
        self.recognizing = True

    def stop_recognition(self):
        self.recognizing = False

    def is_recognizing(self):
        return self.recognizing

    def release_camera(self):
        self.video_capture.release()
 

class Deduction(db.Model):
    __tablename__ = 'deduction'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Unique ID for each deduction
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)  # Foreign key to employee table
    submit_date = db.Column(db.Date, nullable=False)  # Date when the deduction was submitted
    reason = db.Column(db.Text, nullable=True)  # Reason for the deduction (text area)
    deduction_points =db.Column(db.Integer, nullable=False)  # Deduction points (float)

    employee = db.relationship('Employee', backref=db.backref('Deduction', lazy=True))
    
class EmployeeRates(db.Model):
    __tablename__ = 'officer_rates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.employment_id'), nullable=False)
    rate = db.Column(db.Float, nullable=False)  # Rate as a percentage, stored as a float
    submit_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)  # Date when the rate is submitted
    