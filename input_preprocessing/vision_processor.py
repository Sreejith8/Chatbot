import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

class VisualProcessor:
    def __init__(self):
        self.mp_face_mesh = None
        self.face_mesh = None
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
        except ImportError:
            print("Warning: MediaPipe not found. Visual features will be mocked.")

    def extract_landmarks(self, image_path):
        """
        Extracts 468/478 face landmarks.
        """
        if self.face_mesh is None or cv2 is None:
             # Mock return
             return np.zeros(1434)

        image = cv2.imread(image_path)
        if image is None:
            return None
            
        # Convert BGR to RGB
        results = self.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            return None
            
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Flatten (x, y, z) into a single vector
        # Flattening 478 points -> 1434 dimensional vector
        feature_vector = []
        for lm in landmarks:
            feature_vector.extend([lm.x, lm.y, lm.z])
            
        return np.array(feature_vector)
