class RealtimeVoiceAssistant {
    constructor() {
        this.isConnected = false;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.websocket = null;
        this.audioContext = null;
        this.audioQueue = [];
        this.isAuthenticated = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkAuthentication();
    }

    initializeElements() {
        this.recordButton = document.getElementById('recordButton');
        this.buttonText = document.getElementById('buttonText');
        this.recordingStatus = document.getElementById('recordingStatus');
        this.conversationHistory = document.getElementById('conversationHistory');
        this.loginModal = document.getElementById('loginModal');
        this.loginForm = document.getElementById('loginForm');
        this.passwordInput = document.getElementById('passwordInput');
        this.loginError = document.getElementById('loginError');
    }

    setupEventListeners() {
        // Record button click event (toggle recording)
        this.recordButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleRecording();
        });

        // Login form
        this.loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.authenticate();
        });
    }

    async checkAuthentication() {
        try {
            const response = await fetch('/voice/api/auth/check', {
                method: 'GET',
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                this.isAuthenticated = true;
                this.hideLogin();
                this.initializeRealtime();
            } else {
                this.showLogin();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showLogin();
        }
    }

    async authenticate() {
        const password = this.passwordInput.value;
        
        try {
            const response = await fetch('/voice/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password }),
                credentials: 'same-origin'
            });

            if (response.ok) {
                this.isAuthenticated = true;
                this.hideLogin();
                this.loginError.classList.add('hidden');
                this.passwordInput.value = '';
                this.initializeRealtime();
            } else {
                this.loginError.classList.remove('hidden');
                this.passwordInput.value = '';
            }
        } catch (error) {
            console.error('Authentication failed:', error);
            this.loginError.classList.remove('hidden');
            this.loginError.textContent = 'Authentication error';
        }
    }

    async initializeRealtime() {
        if (!this.isAuthenticated) return;
        
        // Initialize Web Audio API for real-time audio processing
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            await this.audioContext.resume();
        } catch (error) {
            console.error('Failed to initialize audio context:', error);
            this.addMessage('system', 'Error: Could not initialize audio. Please check permissions.');
            return;
        }

        // Connect to WebSocket
        this.connectWebSocket();
    }

    connectWebSocket() {
        // Use wss for HTTPS or ws for HTTP
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/voice/api/realtime`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('🔗 WebSocket connected to real-time voice API');
            this.isConnected = true;
            this.addMessage('system', 'Real-time voice connection established. You can now speak naturally!');
            this.updateButtonState();
        };
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.websocket.onclose = () => {
            console.log('📴 WebSocket disconnected');
            this.isConnected = false;
            this.updateButtonState();
            this.addMessage('system', 'Connection lost. Please refresh to reconnect.');
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addMessage('system', 'Connection error. Please check your internet connection.');
        };
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'audio':
                // Play received audio immediately
                this.playAudioChunk(message.data);
                break;
            case 'text':
                // Display AI response text
                this.addMessage('assistant', message.text);
                break;
        }
    }

    async playAudioChunk(audioDataB64) {
        try {
            // Decode base64 audio data
            const audioData = atob(audioDataB64);
            const audioBuffer = new ArrayBuffer(audioData.length);
            const audioView = new Uint8Array(audioBuffer);
            for (let i = 0; i < audioData.length; i++) {
                audioView[i] = audioData.charCodeAt(i);
            }
            
            // Decode PCM audio and play
            const decodedAudio = await this.audioContext.decodeAudioData(this.convertPCMToWAV(audioView));
            const source = this.audioContext.createBufferSource();
            source.buffer = decodedAudio;
            source.connect(this.audioContext.destination);
            source.start();
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

    convertPCMToWAV(pcmData) {
        // Convert PCM to WAV format for Web Audio API
        const sampleRate = 24000;
        const channels = 1;
        const bitsPerSample = 16;
        
        const length = pcmData.length;
        const arrayBuffer = new ArrayBuffer(44 + length);
        const view = new DataView(arrayBuffer);
        
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, channels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * channels * bitsPerSample / 8, true);
        view.setUint16(32, channels * bitsPerSample / 8, true);
        view.setUint16(34, bitsPerSample, true);
        writeString(36, 'data');
        view.setUint32(40, length, true);
        
        // Copy PCM data
        for (let i = 0; i < length; i++) {
            view.setUint8(44 + i, pcmData[i]);
        }
        
        return arrayBuffer;
    }

    toggleRecording() {
        if (!this.isConnected) {
            this.addMessage('system', 'Please wait for connection to be established.');
            return;
        }
        
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    async startRecording() {
        if (!this.isConnected || this.isRecording) return;

        try {
            // Get microphone stream optimized for real-time processing
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 16000,  // Match Google's expected sample rate
                    channelCount: 1,    // Mono audio
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            // Send audio data in real-time chunks
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                    // Convert to PCM and send to WebSocket
                    this.sendAudioChunk(event.data);
                }
            };

            // Start recording with small chunks for real-time streaming
            this.mediaRecorder.start(100); // 100ms chunks for real-time feel
            this.isRecording = true;
            this.updateButtonState();

            // Add user indicator
            this.addMessage('user', '[Speaking...]');

        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.addMessage('system', 'Error: Could not access microphone. Please check permissions.');
        }
    }

    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;

        this.mediaRecorder.stop();
        this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        this.isRecording = false;
        this.updateButtonState();

        // Remove the speaking indicator
        const messages = this.conversationHistory.querySelectorAll('.message.user-message');
        const lastUserMessage = messages[messages.length - 1];
        if (lastUserMessage && lastUserMessage.textContent.includes('[Speaking...]')) {
            lastUserMessage.remove();
        }
    }

    async sendAudioChunk(audioBlob) {
        try {
            // Convert blob to array buffer
            const arrayBuffer = await audioBlob.arrayBuffer();
            const audioData = new Uint8Array(arrayBuffer);
            
            // Convert to base64 for WebSocket transmission
            const base64Audio = btoa(String.fromCharCode(...audioData));
            
            // Send to WebSocket
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    type: 'audio',
                    data: base64Audio
                }));
            }
        } catch (error) {
            console.error('Error sending audio chunk:', error);
        }
    }

    updateButtonState() {
        if (!this.isConnected) {
            this.recordButton.disabled = true;
            this.buttonText.textContent = 'Connecting...';
            this.recordButton.classList.remove('recording');
        } else if (this.isRecording) {
            this.recordButton.disabled = false;
            this.recordButton.classList.add('recording');
            this.buttonText.textContent = 'Speaking...';
            this.recordingStatus.classList.remove('hidden');
        } else {
            this.recordButton.disabled = false;
            this.recordButton.classList.remove('recording');
            this.buttonText.textContent = 'Hold to Talk';
            this.recordingStatus.classList.add('hidden');
        }
    }

    addMessage(type, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        let icon = '';
        switch (type) {
            case 'user':
                icon = '<i class="fas fa-user"></i>';
                break;
            case 'assistant':
                icon = '<i class="fas fa-robot"></i>';
                break;
            case 'system':
                icon = '<i class="fas fa-info-circle"></i>';
                break;
        }

        messageDiv.innerHTML = `${icon}<span>${text}</span>`;
        this.conversationHistory.appendChild(messageDiv);
        
        // Scroll to bottom
        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
        
        return messageDiv;
    }

    showLogin() {
        this.loginModal.classList.remove('hidden');
        this.passwordInput.focus();
    }

    hideLogin() {
        this.loginModal.classList.add('hidden');
    }
}

// Initialize the real-time voice assistant when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new RealtimeVoiceAssistant();
});