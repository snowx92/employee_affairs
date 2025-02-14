# face_recognition/scripts/frame_generator.py
import os
from pathlib import Path
import cv2
import time
from datetime import datetime
import logging
from app.models import FaceRecognition




def generate_frames(recognized_person_id):
    from app.routes import record_appearance
    import cv2
    import numpy as np
    import time

    face_recognition_system = FaceRecognition()
    face_recognition_system.start_recognition()

    frame_buffer = []
    person_scores = {}

    while face_recognition_system.is_recognizing():
        frame, face_scores = face_recognition_system.process_frame()

        if frame is not None:
            # Add current frame scores to the buffer
            frame_buffer.append(face_scores)

            # Process every 5 frames
            if len(frame_buffer) == 5:
                # Update scores for each person
                for scores in frame_buffer:
                    for score_entry in scores:
                        person_id = score_entry['id']
                        score = score_entry['score']
                        print(f"Processing face: {person_id}, Score: {score}")

                        if person_id not in person_scores:
                            person_scores[person_id] = []

                        # Add the current score to the person's list
                        person_scores[person_id].append(score)

                # Determine top 10 scores for each person
                top_scores = {}
                for person_id, scores in person_scores.items():
                    # Sort scores in descending order and keep top 10
                    top_10_scores = sorted(scores, reverse=True)[:5]
                    top_scores[person_id] = top_10_scores

                # Record appearance for the top scores
                for person_id, scores in top_scores.items():
                    best_score = max(scores)
                    print(f"Recording appearance for {person_id} with best score {best_score}")
                    # Call record_appearance with the name of the recognized person
                    record_appearance(person_id)

                # Clear the buffer and reset scores for the next batch
                frame_buffer = []
                person_scores = {}

            # Encode the frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            # Convert the encoded frame to bytes
            frame_bytes = buffer.tobytes()

            # Yield the frame in the format suitable for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        # Optional: Implement a small delay to reduce CPU usage
        time.sleep(0.1)

    face_recognition_system.stop_recognition()
    face_recognition_system.release_camera()
    cv2.destroyAllWindows()
