import requests
import json
import io
import wave
import struct

def create_valid_wav():
    # Create 1 second of silence
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b'\x00\x00' * 16000)
    buf.seek(0)
    buf.name = "test_audio.wav"
    return buf

def create_valid_jpg():
    # 1x1 Pixel valid JPEG
    return io.BytesIO(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00\x00?\x00\xbf\xff\xd9')

def test_multimodal():
    url = "http://127.0.0.1:5001/api/multimodal_input"
    
    audio = create_valid_wav()
    # Need image bytes
    jpg = create_valid_jpg()
    jpg.name = "frame.jpg"
    
    files = [
        ('audio', ('test_audio.wav', audio, 'audio/wav')),
        ('frames', ('frame1.jpg', jpg, 'image/jpeg'))
    ]
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, files=files, data={"metadata": '{"test": true}'}, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_multimodal()
