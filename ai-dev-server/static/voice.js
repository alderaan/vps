class VoiceAssistant {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
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
        this.responseAudio = document.getElementById('responseAudio');
        this.loginModal = document.getElementById('loginModal');
        this.loginForm = document.getElementById('loginForm');
        this.passwordInput = document.getElementById('passwordInput');
        this.loginError = document.getElementById('loginError');
        this.loadingOverlay = document.getElementById('loadingOverlay');
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

        // Audio ended event  
        this.responseAudio.addEventListener('ended', () => {
            // Audio playback finished
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

    toggleRecording() {
        if (!this.isAuthenticated) return;
        
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }

    async startRecording() {
        if (!this.isAuthenticated || this.isRecording) return;

        try {
            // Request lower quality audio for faster processing
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 16000,  // Lower sample rate for faster STT
                    channelCount: 1,    // Mono audio
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            // Use lower quality MediaRecorder settings if supported
            const options = {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 32000  // Lower bitrate for smaller files
            };
            
            // Fall back to default if options not supported
            this.mediaRecorder = MediaRecorder.isTypeSupported(options.mimeType) 
                ? new MediaRecorder(stream, options)
                : new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateUI(true);

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
        this.updateUI(false);
    }

    updateUI(recording) {
        if (recording) {
            this.recordButton.classList.add('recording');
            this.buttonText.textContent = 'Click to Stop';
            this.recordingStatus.classList.remove('hidden');
        } else {
            this.recordButton.classList.remove('recording');
            this.buttonText.textContent = 'Click to Talk';
            this.recordingStatus.classList.add('hidden');
        }
    }

    async processRecording() {
        if (this.audioChunks.length === 0) return;

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');

        try {
            // Step 1: Convert speech to text
            const sttResponse = await fetch('/voice/api/stt', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            if (!sttResponse.ok) {
                throw new Error('Speech recognition failed');
            }

            const sttResult = await sttResponse.json();
            const userText = sttResult.text;

            // Add user message to conversation
            this.addMessage('user', userText);

            // Step 2: Get AI response with streaming for faster text display
            const chatResponse = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer sk-a5b86f89590eb746312b24043cd5d668db635d0e9e832f0a'
                },
                body: JSON.stringify({
                    model: 'multi-agent-system',
                    messages: [
                        {
                            role: 'user',
                            content: userText
                        }
                    ],
                    stream: true  // Enable streaming for faster response
                }),
                credentials: 'same-origin'
            });

            if (!chatResponse.ok) {
                throw new Error('AI response failed');
            }

            // Process streaming response with early TTS trigger
            const reader = chatResponse.body.getReader();
            const decoder = new TextDecoder();
            let aiText = '';
            let messageElement = null;
            let ttsTriggered = false;
            let ttsPromise = null;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') continue;

                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.choices && parsed.choices[0] && parsed.choices[0].delta) {
                                const content = parsed.choices[0].delta.content;
                                if (content) {
                                    aiText += content;
                                    
                                    // Update UI with streaming text
                                    if (!messageElement) {
                                        messageElement = this.addMessage('assistant', aiText);
                                    } else {
                                        // Update existing message
                                        const span = messageElement.querySelector('span');
                                        if (span) span.textContent = aiText;
                                    }

                                    // Trigger TTS early when we have enough content (first sentence or 50 chars)
                                    if (!ttsTriggered && (aiText.includes('.') || aiText.length > 50)) {
                                        ttsTriggered = true;
                                        console.log('🎵 Starting early TTS with:', aiText.slice(0, 50) + '...');
                                        
                                        // Start TTS in parallel while continuing to stream
                                        ttsPromise = this.startTTS(aiText);
                                    }
                                }
                            }
                        } catch (e) {
                            // Ignore JSON parse errors for incomplete chunks
                        }
                    }
                }
            }

            // Ensure we have the complete message
            if (!messageElement) {
                this.addMessage('assistant', aiText);
            }

            // If TTS wasn't triggered early, start it now with complete text
            if (!ttsTriggered) {
                console.log('🎵 Starting TTS with complete text');
                ttsPromise = this.startTTS(aiText);
            }

            // Wait for TTS to complete and play audio
            if (ttsPromise) {
                try {
                    await ttsPromise;
                } catch (error) {
                    console.error('TTS error:', error);
                    this.addMessage('system', `TTS Error: ${error.message}`);
                }
            }

        } catch (error) {
            console.error('Processing error:', error);
            this.addMessage('system', `Error: ${error.message}`);
        }
    }

    async startTTS(text) {
        try {
            // Step 3: Convert text to speech
            const ttsResponse = await fetch('/voice/api/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text }),
                credentials: 'same-origin'
            });

            if (!ttsResponse.ok) {
                throw new Error('Text-to-speech failed');
            }

            // Play the audio response
            const audioArrayBuffer = await ttsResponse.arrayBuffer();
            const contentType = ttsResponse.headers.get('content-type') || 'audio/opus';
            const audioBlob = new Blob([audioArrayBuffer], { type: contentType });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            this.responseAudio.src = audioUrl;
            this.responseAudio.play();

        } catch (error) {
            console.error('TTS processing error:', error);
            throw error;
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
        
        return messageDiv;  // Return the element for streaming updates
    }

    showLogin() {
        this.loginModal.classList.remove('hidden');
        this.passwordInput.focus();
    }

    hideLogin() {
        this.loginModal.classList.add('hidden');
    }

    showLoading() {
        this.loadingOverlay.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingOverlay.classList.add('hidden');
    }
}

// Initialize the voice assistant when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new VoiceAssistant();
});