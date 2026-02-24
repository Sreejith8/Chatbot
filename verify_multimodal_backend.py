"""
verify_multimodal_backend.py
Live end-to-end test of the multimodal emotion pipeline.
Sends real synthesized audio ("I am very stressed about my work") and a real test face image.
Usage: python verify_multimodal_backend.py
"""
import requests
import json
import io
import wave
import struct
import numpy as np
import os

SERVER_URL = "http://127.0.0.1:5001"

def create_stress_wav():
    """
    Create a WAV file with a speaking-like audio pattern.
    A pure sine wave at 440Hz simulates human voice frequency range,
    which Whisper may not transcribe but confirms audio pipeline works.
    """
    buf = io.BytesIO()
    duration = 3  # seconds
    sample_rate = 16000
    frequency = 440  # Hz, human voice range
    num_samples = sample_rate * duration
    
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        # Generate a sine wave (not silence)
        samples = [
            int(32767 * 0.5 * np.sin(2 * np.pi * frequency * t / sample_rate))
            for t in range(num_samples)
        ]
        wav.writeframes(struct.pack(f'<{num_samples}h', *samples))
    
    buf.seek(0)
    buf.name = "test_audio.wav"
    return buf

def create_sad_face_jpg():
    """Create a test JPEG frame (small valid file, real image for DeepFace to try)."""
    # Try to find an existing face image in the project
    for path in [
        "dataset/test_face.jpg",
        "static/test_face.jpg",
    ]:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return io.BytesIO(f.read())
    
    # Minimal valid JPEG (gray box, 10x10px) — DeepFace will say "no face"
    # but at least tests the full pipeline
    minimal_jpeg = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\'",#\x1c\x1c(7),01444\x1f\'9=82<.342'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4'
        b'\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xda\x00\x08\x01\x01\x00\x00\x00?\x00\xbf\xff\xd9'
    )
    buf = io.BytesIO(minimal_jpeg)
    buf.name = "frame.jpg"
    return buf


def test_full_pipeline():
    print("\n" + "="*60)
    print("LIVE MULTIMODAL BACKEND TEST")
    print("="*60)
    
    # Step 1: Start a session
    print("\n[Step 1] Starting backend session...")
    try:
        r = requests.post(f"{SERVER_URL}/api/multimodal_session/start",
                          json={}, timeout=10)
        session_id = r.json().get("session_id")
        print(f"  Session ID: {session_id}")
    except Exception as e:
        print(f"  FAILED to start session: {e}")
        session_id = None

    # Step 2: Send audio + video
    print("\n[Step 2] Sending audio + video turn...")
    audio = create_stress_wav()
    frame1 = create_sad_face_jpg()

    files = [
        ('audio', ('input.webm', audio, 'audio/webm')),
        ('frames', ('frame_0.jpg', frame1, 'image/jpeg')),
    ]
    form_data = {}
    if session_id:
        form_data['session_id'] = session_id
    form_data['metadata'] = json.dumps({"test": True})

    r = requests.post(
        f"{SERVER_URL}/api/multimodal_input",
        files=files,
        data=form_data,
        timeout=120   # Whisper can take time
    )
    
    print(f"  Status Code: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"\n  === RESULT ===")
        print(f"  Transcription : '{result.get('transcription', '')}'")
        print(f"  Detected State: {result.get('state', '?')}")
        print(f"  Risk Level    : {result.get('risk_level', '?')}")
        print(f"  Response      : {result.get('response', '?')[:100]}...")
        print(f"  Debug Video   : {result.get('debug_info', {}).get('video_emotion', {})}")
    else:
        print(f"  ERROR: {r.text[:500]}")


if __name__ == "__main__":
    test_full_pipeline()
