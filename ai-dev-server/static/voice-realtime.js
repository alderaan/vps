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
        
        // Don't initialize audio context here - wait for user interaction
        // Connect to WebSocket first
        this.connectWebSocket();
    }

    async initializeAudioContext() {
        // Initialize Web Audio API only after user gesture
        if (!this.audioContext) {
            try {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                await this.audioContext.resume();
                console.log('🔊 Audio context initialized after user interaction');
            } catch (error) {
                console.error('Failed to initialize audio context:', error);
                this.addMessage('system', 'Error: Could not initialize audio. Please check permissions.');
                throw error;
            }
        }
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
            case 'turn_complete':
                // AI finished speaking - clear any hanging state
                console.log('🎤 AI finished speaking (turn complete)');
                this.clearAudioQueue();
                break;
        }
    }

    async playAudioChunk(audioDataB64) {
        try {
            // Decode base64 audio data
            const audioData = atob(audioDataB64);
            
            // Convert to Int16 array (PCM format from Gemini)
            const pcmData = new Int16Array(audioData.length / 2);
            for (let i = 0; i < pcmData.length; i++) {
                pcmData[i] = (audioData.charCodeAt(i * 2 + 1) << 8) | audioData.charCodeAt(i * 2);
            }
            
            // Create AudioBuffer with correct sample rate (24kHz from Gemini)
            const sampleRate = 24000; // Gemini's output sample rate
            const audioBuffer = this.audioContext.createBuffer(1, pcmData.length, sampleRate);
            const channelData = audioBuffer.getChannelData(0);
            
            // Convert Int16 to Float32 for Web Audio API
            for (let i = 0; i < pcmData.length; i++) {
                channelData[i] = pcmData[i] / 32768.0; // Normalize to -1.0 to 1.0
            }
            
            // Play the audio
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start();
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }


    clearAudioQueue() {
        // Clear any pending audio to prevent hanging (Google's approach)
        // Stop any currently playing audio
        try {
            if (this.audioContext && this.audioContext.state === 'running') {
                // This helps prevent audio hanging by resetting the audio context state
                this.audioContext.suspend().then(() => {
                    this.audioContext.resume();
                });
            }
        } catch (error) {
            console.log('Audio queue clear completed');
        }
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
            // Initialize audio context on first user interaction
            await this.initializeAudioContext();

            // Get microphone stream optimized for real-time processing
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 16000,  // Match Google's expected sample rate
                    channelCount: 1,    // Mono audio
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Use Web Audio API to capture PCM directly (like Google's example)
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            this.scriptProcessor.onaudioprocess = (event) => {
                if (this.isRecording) {
                    const inputData = event.inputBuffer.getChannelData(0);
                    // Convert Float32 to Int16 PCM
                    const pcmData = new Int16Array(inputData.length);
                    for (let i = 0; i < inputData.length; i++) {
                        pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
                    }
                    this.sendPCMAudioChunk(pcmData.buffer);
                }
            };
            
            source.connect(this.scriptProcessor);
            this.scriptProcessor.connect(this.audioContext.destination);
            
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
        if (!this.isRecording) return;

        this.isRecording = false;
        
        // Clean up Web Audio API components
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
        }
        
        // Stop media stream tracks
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        // Signal end of turn to Gemini Live
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'end_turn'
            }));
            console.log('🎤 Sent end_turn signal to server');
        }
        
        this.updateButtonState();

        // Remove the speaking indicator
        const messages = this.conversationHistory.querySelectorAll('.message.user-message');
        const lastUserMessage = messages[messages.length - 1];
        if (lastUserMessage && lastUserMessage.textContent.includes('[Speaking...]')) {
            lastUserMessage.remove();
        }
    }

    sendPCMAudioChunk(pcmBuffer) {
        try {
            // Convert PCM buffer to base64 - same as Google's approach
            const audioData = new Uint8Array(pcmBuffer);
            const base64Audio = btoa(String.fromCharCode(...audioData));
            
            // Send to WebSocket with PCM mime type (like Google's code)
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({
                    type: 'audio',
                    data: base64Audio
                }));
            }
        } catch (error) {
            console.error('Error sending PCM audio chunk:', error);
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