class RealtimeVoiceAssistant {
    constructor() {
        this.isConnected = false;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.websocket = null;
        this.audioContext = null;
        this.audioQueue = [];
        this.isAuthenticated = false;
        this.activeSources = [];
        this.audioBufferQueue = [];
        this.playbackInterval = null;
        
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
        console.log(`📨 WebSocket message received: type=${message.type}, size=${message.data ? message.data.length : 0}`);
        
        switch (message.type) {
            case 'audio':
                // Queue audio for timed playback instead of immediate play
                console.log('🎵 Adding audio to buffer queue...');
                this.queueAudioChunk(message.data);
                break;
            case 'text':
                // Display AI response text
                console.log('📝 Text received:', message.text);
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
            // Server sends raw PCM from Gemini → base64 encode → WebSocket
            // We need to decode base64 and play as 24kHz 16-bit PCM directly
            const binaryString = atob(audioDataB64);
            const audioBytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                audioBytes[i] = binaryString.charCodeAt(i);
            }
            
            // Gemini sends 16-bit PCM at 24kHz - convert to Int16Array
            const pcmSamples = new Int16Array(audioBytes.buffer);
            
            // Create Web Audio buffer at 24kHz (Gemini's output rate)
            const sampleRate = 24000;
            const audioBuffer = this.audioContext.createBuffer(1, pcmSamples.length, sampleRate);
            const channelData = audioBuffer.getChannelData(0);
            
            // Convert 16-bit PCM to float32 for Web Audio (-1.0 to 1.0)
            for (let i = 0; i < pcmSamples.length; i++) {
                channelData[i] = pcmSamples[i] / 32768.0;
            }
            
            // Play IMMEDIATELY - no scheduling delays for real-time conversation
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start(0); // Play immediately
            
            console.log(`✅ Audio source started - ${pcmSamples.length} samples, duration: ${audioBuffer.duration.toFixed(3)}s`);
            
            // Track active source for cleanup
            this.activeSources.push(source);
            
            // Remove from tracking when done
            source.onended = () => {
                console.log(`🏁 Audio source ended`);
                const index = this.activeSources.indexOf(source);
                if (index > -1) {
                    this.activeSources.splice(index, 1);
                }
            };
            
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }


    queueAudioChunk(audioDataB64) {
        // Add audio to buffer queue
        this.audioBufferQueue.push(audioDataB64);
        console.log(`📦 Audio queued, buffer size: ${this.audioBufferQueue.length}`);
        
        // Start playback timer if not already running
        if (!this.playbackInterval) {
            this.startBufferedPlayback();
        }
    }
    
    startBufferedPlayback() {
        console.log('▶️ Starting buffered audio playback');
        
        // Play audio chunks from buffer at regular intervals (40ms = 960 samples at 24kHz)
        this.playbackInterval = setInterval(() => {
            if (this.audioBufferQueue.length > 0) {
                const audioData = this.audioBufferQueue.shift();
                console.log(`🎵 Playing buffered audio chunk, remaining: ${this.audioBufferQueue.length}`);
                this.playAudioChunk(audioData);
            } else if (this.audioBufferQueue.length === 0) {
                // Keep running to handle new incoming audio
            }
        }, 40); // 40ms intervals for smooth playback
    }
    
    stopBufferedPlayback() {
        if (this.playbackInterval) {
            clearInterval(this.playbackInterval);
            this.playbackInterval = null;
            console.log('⏹️ Stopped buffered audio playback');
        }
    }

    clearAudioQueue() {
        // Stop playback timer
        this.stopBufferedPlayback();
        
        // Clear buffer queue
        this.audioBufferQueue = [];
        
        // Stop all active audio sources
        this.activeSources.forEach(source => {
            try {
                source.stop();
            } catch (e) {
                // Source may already be stopped
            }
        });
        this.activeSources = [];
        console.log('🔄 All audio cleared - sources stopped, buffers cleared');
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
            
            // Use the EXACT working solution from StackOverflow
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            // CRITICAL: Connect processor to destination FIRST (from working solution)
            this.scriptProcessor.connect(this.audioContext.destination);
            
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
            
            // Connect source to processor (from working solution)
            source.connect(this.scriptProcessor);
            
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
        
        // STOP ALL AUDIO IMMEDIATELY
        this.clearAudioQueue();
        
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
            this.buttonText.textContent = 'End Conversation';
            this.recordingStatus.classList.remove('hidden');
        } else {
            this.recordButton.disabled = false;
            this.recordButton.classList.remove('recording');
            this.buttonText.textContent = 'Start Conversation';
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