import numpy as np
import os

class AudioProcessor:
    def __init__(self, model_size="base"):
        # Lazy loading to prevent startup lag if not needed immediately
        self.model_size = model_size
        self.model = None
        self.has_libs = False
        try:
            import librosa
            import whisper
            self.has_libs = True
        except ImportError:
            print("Warning: Librosa/Whisper not found. Audio features will be mocked.")

    def load_model(self):
        if self.has_libs and not self.model:
            import whisper
            import ssl
            import urllib.request
            
            # Fix SSL certificate verification error
            ssl._create_default_https_context = ssl._create_unverified_context
            
            print(f"Loading Whisper model: {self.model_size}...")
            self.model = whisper.load_model(self.model_size)

    def transcribe(self, audio_path):
        """
        Transcribes audio file to text using Whisper.
        """
        if not self.has_libs:
            print("Warning: Wrapper called but libs missing. Returning mock.")
            return "[Audio Transcription Mock]"
            
        try:
            self.load_model()
            # Suppress warnings
            import warnings
            warnings.filterwarnings("ignore")
            
            result = self.model.transcribe(audio_path, fp16=False) # fp16=False for CPU compatibility
            return result['text']
        except Exception as e:
            print(f"Transcription Error: {e}")
            return ""

    def extract_prosodic_features(self, audio_path):
        """
        Extracts MFCC, Pitch, and Energy using Librosa.
        Returns a feature vector.
        """
        if not self.has_libs:
             return np.zeros(15)

        try:
            import librosa
            # Load audio for 7 seconds (matching max capture)
            y, sr = librosa.load(audio_path, duration=7.0)
            
            # MFCC (13 coeffs)
            mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
            
            # Pitch (Zero Crossing Rate as robust proxy for pitch variability)
            zcr = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # Energy (RMS)
            rms = np.mean(librosa.feature.rms(y=y))
            
            # Return merged vector
            return np.concatenate([mfcc, [zcr, rms]])
        except Exception as e:
             print(f"Librosa Error: {e}")
             return np.zeros(15)
