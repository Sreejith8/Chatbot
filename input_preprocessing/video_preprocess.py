import cv2
import numpy as np
try:
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False
except AttributeError:
    MP_AVAILABLE = False

class VideoPreprocessor:
    def __init__(self):
        self.mp_face_detection = None
        self.face_detection = None
        
        if MP_AVAILABLE:
            try:
                if hasattr(mp, 'solutions'):
                    self.mp_face_detection = mp.solutions.face_detection
                    self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
                else:
                    print("Warning: MediaPipe found but 'solutions' missing. Using mock.")
                    self.mp_face_detection = None
            except Exception as e:
                print(f"MediaPipe Init Error: {e}")
        else:
            print("Warning: MediaPipe not available. Using mock video processing.")

    def extract_face_emotions(self, image_bytes):
        """
        Processes a single image frame (bytes) to detect faces and estimate emotion.
        Returns a dict of emotion probabilities.
        """
        # Fallback if no detector - removed to allow DeepFace to try its own detection
        # if self.face_detection is None:
        #     return { ... }


        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return None

            # DeepFace for robust Emotion Detection
            from deepface import DeepFace
            
            # DeepFace expects path or numpy array (BGR is fine if backend is opencv)
            # analyze() returns a list of result dicts
            # We enforce detection to False to speed up processing since we can crop faces if needed, 
            # but DeepFace handles it. To be safe, let's use enforce_detection=False so it doesn't crash on partial faces.
            analysis = DeepFace.analyze(
                img_path=frame, 
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='opencv',
                silent=True
            )
            
            if not analysis:
                return None
                
            # Take the first face found
            emotions = analysis[0]['emotion']
            
            # Normalize keys to match our system (DeepFace returns lowercase keys sometimes, normalizing to Title Case)
            # DeepFace: {'angry': 0.1, 'disgust': 0.0, 'fear': 0.0, 'happy': 99.0, 'sad': 0.0, 'surprise': 0.0, 'neutral': 0.0}
            normalized = {
                "Angry": emotions.get('angry', 0) / 100.0,
                "Fear": emotions.get('fear', 0) / 100.0,
                "Happy": emotions.get('happy', 0) / 100.0,
                "Sad": emotions.get('sad', 0) / 100.0,
                "Surprise": emotions.get('surprise', 0) / 100.0,
                "Neutral": emotions.get('neutral', 0) / 100.0,
                "Disgust": emotions.get('disgust', 0) / 100.0,
            }
            return normalized

        except Exception as e:
            # Start returning None if DeepFace fails so we don't spam errors, 
            # but for debugging let's print
            # print(f"DeepFace processing error: {e}")
            return None
