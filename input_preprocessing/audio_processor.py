import numpy as np
import os
import subprocess
import tempfile

class AudioProcessor:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self.model = None
        self.has_libs = False
        self.has_ffmpeg = False
        try:
            import librosa
            import whisper
            self.has_libs = True
        except ImportError:
            print("Warning: Librosa/Whisper not found. Audio features will be mocked.")
        
        # Check if ffmpeg is available for webm→wav conversion
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            self.has_ffmpeg = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("[AudioProcessor] Warning: ffmpeg not found. webm conversion may fail.")

    def _convert_to_wav(self, input_path):
        """
        Converts any audio format (webm, ogg, mp4) to wav using ffmpeg.
        Returns path to the converted wav file, or original path if conversion fails.
        """
        if not self.has_ffmpeg:
            return input_path
        
        # Create a temp wav file path
        wav_path = input_path + "_converted.wav"
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",          # overwrite output
                    "-i", input_path,        # input file (any format)
                    "-ar", "16000",          # resample to 16kHz (Whisper optimal)
                    "-ac", "1",             # mono channel
                    "-f", "wav",            # force wav output format
                    wav_path
                ],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0 and os.path.exists(wav_path):
                print(f"[AudioProcessor] Converted {os.path.basename(input_path)} → WAV ({os.path.getsize(wav_path)} bytes)")
                return wav_path
            else:
                print(f"[AudioProcessor] ffmpeg conversion failed: {result.stderr.decode()[:200]}")
                return input_path
        except Exception as e:
            print(f"[AudioProcessor] Conversion error: {e}")
            return input_path

    def load_model(self):
        if self.has_libs and not self.model:
            import whisper
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            print(f"[AudioProcessor] Loading Whisper model: {self.model_size}...")
            self.model = whisper.load_model(self.model_size)

    def transcribe(self, audio_path):
        """
        Transcribes audio file to text using Whisper.
        Automatically converts webm/ogg to wav first.
        """
        if not self.has_libs:
            print("[AudioProcessor] Warning: Whisper not available. Returning Mock.")
            return "[Audio Transcription Mock]"

        # Convert to WAV first (handles webm from browser)
        wav_path = self._convert_to_wav(audio_path)
        
        try:
            self.load_model()
            import warnings
            warnings.filterwarnings("ignore")
            result = self.model.transcribe(wav_path, fp16=False)
            text = result['text'].strip()
            print(f"[AudioProcessor] Transcription: '{text}'")
            return text
        except Exception as e:
            print(f"[AudioProcessor] Transcription Error: {e}")
            return ""
        finally:
            # Clean up temp wav
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)

    def extract_prosodic_features(self, audio_path):
        """
        Extracts PNCC, ZCR, and RMS energy using Librosa and Spafe.
        Automatically converts webm/ogg to wav first.
        Returns a feature vector of shape (15,).
        """
        if not self.has_libs:
            return np.zeros(15)

        # Convert to WAV first (handles webm from browser)
        wav_path = self._convert_to_wav(audio_path)

        try:
            import librosa
            from spafe.features.pncc import pncc
            
            y, sr = librosa.load(wav_path, duration=7.0, sr=16000)
            
            if len(y) == 0:
                print("[AudioProcessor] Librosa loaded empty audio signal!")
                return np.zeros(15)

            # PNCC (13 coefficients) - Replaced MFCC per professor feedback
            p = pncc(sig=y, fs=sr, num_ceps=13)
            pncc_features = np.mean(p, axis=0)
            
            # ZCR (pitch proxy)
            zcr = np.mean(librosa.feature.zero_crossing_rate(y))
            # RMS Energy
            rms = np.mean(librosa.feature.rms(y=y))

            features = np.concatenate([pncc_features, [zcr, rms]])
            print(f"[AudioProcessor] Prosodic features extracted: ZCR={zcr:.4f}, RMS={rms:.4f}")
            return features
        except Exception as e:
            print(f"[AudioProcessor] Librosa Error: {e}")
            return np.zeros(15)
        finally:
            # Clean up temp wav
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
