import { useState, useRef, useCallback } from 'react';

const useMediaCapture = () => {
    const [isCapturing, setIsCapturing] = useState(false);

    // Refs to hold mutable state without triggering re-renders
    const streamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const videoFramesRef = useRef([]); // Array of base64/Blob
    const captureIntervalRef = useRef(null);

    // Configuration
    const frameIntervalMs = 500; // Capture frame every 500ms

    const requestPermissions = useCallback(async () => {
        try {
            console.log("Requesting Camera & Mic permissions...");
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: { width: 320, height: 240, facingMode: "user" }
            });
            streamRef.current = stream;
            return stream;
        } catch (err) {
            console.error("Permission denied:", err);
            alert("Permission denied. Please allow access to Camera and Microphone.");
            return null;
        }
    }, []);

    const startContinuousCapture = useCallback(async (videoElement) => {
        let stream = streamRef.current;
        if (!stream) {
            stream = await requestPermissions();
            if (!stream) return false;
        }

        // 1. Attach Stream to Video Preview
        if (videoElement) {
            videoElement.srcObject = stream;
            videoElement.play().catch(e => console.error("Video play failed:", e));
        }

        // 2. Setup Audio Recorder with circular buffer
        audioChunksRef.current = [];
        const audioTracks = stream.getAudioTracks();

        if (audioTracks.length === 0) {
            console.error("[MediaCapture] No audio track found!");
            alert("Microphone not detected by browser.");
            return false;
        }

        const audioStream = new MediaStream(audioTracks);
        try {
            mediaRecorderRef.current = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
        } catch (e) {
            console.error("[MediaCapture] MediaRecorder init failed:", e);
            alert("MediaRecorder initialization failed. " + e.message);
            return false;
        }

        mediaRecorderRef.current.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunksRef.current.push(event.data);
            }
        };

        // Request data every second for continuous buffering
        mediaRecorderRef.current.start(1000);

        // 3. Setup Video Frame Capture (continuous)
        videoFramesRef.current = [];
        const canvas = document.createElement('canvas');
        canvas.width = 320;
        canvas.height = 240;
        const ctx = canvas.getContext('2d');

        captureIntervalRef.current = setInterval(() => {
            if (videoElement && videoElement.readyState === videoElement.HAVE_ENOUGH_DATA) {
                ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
                canvas.toBlob((blob) => {
                    if (blob) {
                        videoFramesRef.current.push(blob);
                        // Keep only last 20 frames (circular buffer)
                        if (videoFramesRef.current.length > 20) {
                            videoFramesRef.current.shift();
                        }
                    }
                }, 'image/jpeg', 0.8);
            }
        }, frameIntervalMs);

        setIsCapturing(true);
        console.log("Continuous capture started: Audio + Video Frames.");
        return true;
    }, [requestPermissions]);

    const captureCurrentBuffer = useCallback(() => {
        return new Promise((resolve) => {
            if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
                console.warn("No active recording to capture buffer from.");
                resolve(null);
                return;
            }

            // Request final chunk from MediaRecorder
            mediaRecorderRef.current.requestData();

            // Wait a bit for the data to be available
            setTimeout(() => {
                // Create blob from current audio chunks
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm; codecs=opus' });

                // Clone current video frames
                const framesCopy = [...videoFramesRef.current];

                // Clear buffers for next turn
                audioChunksRef.current = [];
                videoFramesRef.current = [];

                console.log(`Buffer captured. Audio Size: ${audioBlob.size}, Frames: ${framesCopy.length}`);

                resolve({
                    audioBlob: audioBlob,
                    videoFrames: framesCopy
                });
            }, 100); // Small delay to ensure data is collected
        });
    }, []);

    const endSession = useCallback(() => {
        console.log("Ending continuous capture session...");

        if (captureIntervalRef.current) {
            clearInterval(captureIntervalRef.current);
            captureIntervalRef.current = null;
        }

        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        }

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }

        audioChunksRef.current = [];
        videoFramesRef.current = [];
        setIsCapturing(false);

        console.log("Session ended. All resources released.");
    }, []);

    return {
        isCapturing,
        startContinuousCapture,
        captureCurrentBuffer,
        endSession
    };
};

export default useMediaCapture;
