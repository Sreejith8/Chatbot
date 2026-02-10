/**
 * media_capture.js
 * Handles low-level media APIs: getUserMedia, MediaRecorder, and Canvas Frame Capture.
 */

class MediaCapture {
    constructor() {
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.videoFrames = []; // Array of base64 strings or Blob
        this.captureInterval = null;

        // Configuration
        this.frameIntervalMs = 500; // Capture frame every 500ms
        this.maxRecordingTimeMs = 7000; // 7 seconds fixed window
    }

    async requestPermissions() {
        try {
            console.log("Requesting Camera & Mic permissions...");
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: { width: 320, height: 240, facingMode: "user" }
            });
            return this.mediaStream;
        } catch (err) {
            console.error("Permission denied:", err);
            throw new Error("Permission denied. Please allow access to Camera and Microphone.");
        }
    }

    startRecording(videoPreviewElement) {
        if (!this.mediaStream) {
            console.error("No media stream. Call requestPermissions first.");
            return;
        }

        // 1. Attach Stream to Video Preview
        if (videoPreviewElement) {
            videoPreviewElement.srcObject = this.mediaStream;
            videoPreviewElement.play();
        }

        // 2. Setup Audio Recorder
        this.audioChunks = [];
        const audioTracks = this.mediaStream.getAudioTracks();
        console.log(`[MediaCapture] Found ${audioTracks.length} audio tracks.`);

        if (audioTracks.length === 0) {
            console.error("[MediaCapture] No audio track found!");
            // Fallback or error handling
            alert("Microphone not detected by browser.");
            return;
        }

        // Extract only audio tracks for the MediaRecorder to match "audio/webm"
        const audioStream = new MediaStream(audioTracks);
        try {
            this.mediaRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
        } catch (e) {
            console.error("[MediaCapture] MediaRecorder init failed:", e);
            alert("MediaRecorder initialization failed. " + e.message);
            return;
        }

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };

        this.mediaRecorder.start();

        // 3. Setup Video Frame Capture
        this.videoFrames = [];
        const canvas = document.createElement('canvas');
        canvas.width = 320;
        canvas.height = 240;
        const ctx = canvas.getContext('2d');

        this.captureInterval = setInterval(() => {
            if (videoPreviewElement) {
                ctx.drawImage(videoPreviewElement, 0, 0, canvas.width, canvas.height);
                // Convert to Blob (JPEG)
                canvas.toBlob((blob) => {
                    if (blob) this.videoFrames.push(blob);
                }, 'image/jpeg', 0.8);
            }
        }, this.frameIntervalMs);

        console.log("Recording started: Audio + Video Frames.");
    }

    async stopRecording() {
        return new Promise((resolve) => {
            if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
                resolve(null);
                return;
            }

            // Stop Frame Capture
            if (this.captureInterval) {
                clearInterval(this.captureInterval);
                this.captureInterval = null;
            }

            // Stop Media Recorder
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

                // Stop Tracks to turn off hardware light
                this.mediaStream.getTracks().forEach(track => track.stop());
                this.mediaStream = null;

                console.log(`Recording stopped. Audio Size: ${audioBlob.size}, Frames: ${this.videoFrames.length}`);
                resolve({
                    audioBlob: audioBlob,
                    videoFrames: this.videoFrames // Array of JPEG Blobs
                });
            };

            this.mediaRecorder.stop();
        });
    }

    /**
     * Start continuous capture mode (for live conversation sessions)
     * Camera and mic stay active until endSession() is called
     */
    startContinuousCapture(videoPreviewElement) {
        if (!this.mediaStream) {
            console.error("No media stream. Call requestPermissions first.");
            return;
        }

        // 1. Attach Stream to Video Preview
        if (videoPreviewElement) {
            videoPreviewElement.srcObject = this.mediaStream;
            videoPreviewElement.play();
        }

        // 2. Setup Audio Recorder with circular buffer
        this.audioChunks = [];
        const audioTracks = this.mediaStream.getAudioTracks();
        console.log(`[MediaCapture] Continuous mode: Found ${audioTracks.length} audio tracks.`);

        if (audioTracks.length === 0) {
            console.error("[MediaCapture] No audio track found!");
            alert("Microphone not detected by browser.");
            return;
        }

        const audioStream = new MediaStream(audioTracks);
        try {
            this.mediaRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
        } catch (e) {
            console.error("[MediaCapture] MediaRecorder init failed:", e);
            alert("MediaRecorder initialization failed. " + e.message);
            return;
        }

        // Collect audio chunks continuously
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };

        // Request data every second for continuous buffering
        this.mediaRecorder.start(1000);

        // 3. Setup Video Frame Capture (continuous)
        this.videoFrames = [];
        const canvas = document.createElement('canvas');
        canvas.width = 320;
        canvas.height = 240;
        const ctx = canvas.getContext('2d');

        this.captureInterval = setInterval(() => {
            if (videoPreviewElement) {
                ctx.drawImage(videoPreviewElement, 0, 0, canvas.width, canvas.height);
                canvas.toBlob((blob) => {
                    if (blob) {
                        this.videoFrames.push(blob);
                        // Keep only last 20 frames (circular buffer)
                        if (this.videoFrames.length > 20) {
                            this.videoFrames.shift();
                        }
                    }
                }, 'image/jpeg', 0.8);
            }
        }, this.frameIntervalMs);

        console.log("Continuous capture started: Audio + Video Frames.");
    }

    /**
     * Capture current buffer without stopping the session
     * Used when user clicks "Send" during active session
     */
    async captureCurrentBuffer() {
        if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
            console.warn("No active recording to capture buffer from.");
            return null;
        }

        return new Promise((resolve) => {
            // Request final chunk from MediaRecorder
            this.mediaRecorder.requestData();

            // Wait a bit for the data to be available
            setTimeout(() => {
                // Create blob from current audio chunks
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm; codecs=opus' });

                // Clone current video frames
                const framesCopy = [...this.videoFrames];

                // Clear buffers for next turn
                this.audioChunks = [];
                this.videoFrames = [];

                console.log(`Buffer captured. Audio Size: ${audioBlob.size}, Frames: ${framesCopy.length}`);

                resolve({
                    audioBlob: audioBlob,
                    videoFrames: framesCopy
                });
            }, 100); // Small delay to ensure data is collected
        });
    }

    /**
     * End the continuous session and release all resources
     */
    endSession() {
        console.log("Ending continuous capture session...");

        // Stop frame capture
        if (this.captureInterval) {
            clearInterval(this.captureInterval);
            this.captureInterval = null;
        }

        // Stop media recorder
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        // Stop all media tracks (turns off camera/mic lights)
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        // Clear buffers
        this.audioChunks = [];
        this.videoFrames = [];

        console.log("Session ended. All resources released.");
    }
}

// Export global instance
window.MediaCapture = MediaCapture;
