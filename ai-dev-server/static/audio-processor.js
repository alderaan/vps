class AudioProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input.length > 0) {
      // Send raw Float32Array audio data to main thread
      this.port.postMessage(input[0]);
    }
    return true; // Keep processor alive
  }
}

registerProcessor('audio-processor', AudioProcessor);