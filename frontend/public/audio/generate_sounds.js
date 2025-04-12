// Simple script to generate wav files for poker sounds
// Run with Node.js

const fs = require('fs');
const { AudioContext, AudioBuffer } = require('web-audio-api');

// Function to generate WAV file
function generateWav(buffer, filename) {
  const wavHeader = createWavHeader(buffer);
  const wavData = Buffer.concat([wavHeader, buffer]);
  fs.writeFileSync(filename, wavData);
  console.log(`Generated ${filename}`);
}

// Function to create WAV header
function createWavHeader(audioBuffer) {
  const headerLength = 44;
  const header = Buffer.alloc(headerLength);
  const sampleRate = 44100;
  const numChannels = 1;
  const bytesPerSample = 2;
  const blockAlign = numChannels * bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataSize = audioBuffer.length;

  // RIFF chunk descriptor
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + dataSize, 4);
  header.write('WAVE', 8);

  // FMT sub-chunk
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16); // Subchunk1Size
  header.writeUInt16LE(1, 20); // AudioFormat (PCM)
  header.writeUInt16LE(numChannels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bytesPerSample * 8, 34); // BitsPerSample

  // Data sub-chunk
  header.write('data', 36);
  header.writeUInt32LE(dataSize, 40);

  return header;
}

// Generate CHECK sound (a simple tap sound)
function generateCheckSound() {
  const sampleRate = 44100;
  const duration = 0.15;
  const numSamples = Math.floor(sampleRate * duration);
  const buffer = Buffer.alloc(numSamples * 2); // 16-bit audio = 2 bytes per sample
  
  for (let i = 0; i < numSamples; i++) {
    // Generate a short sine wave with decay
    const time = i / sampleRate;
    const frequency = 1000; // Hz
    const amplitude = 0.5 * Math.exp(-time * 30); // Decay
    
    // Convert to 16-bit PCM
    const sample = Math.floor(amplitude * 32767 * Math.sin(2 * Math.PI * frequency * time));
    buffer.writeInt16LE(sample, i * 2);
  }
  
  generateWav(buffer, 'check.wav');
}

// Generate CHIPS sound (poker chips clinking)
function generateChipsSound() {
  const sampleRate = 44100;
  const duration = 0.3;
  const numSamples = Math.floor(sampleRate * duration);
  const buffer = Buffer.alloc(numSamples * 2);
  
  // Generate multiple overlapping short sounds for chip effect
  for (let i = 0; i < numSamples; i++) {
    const time = i / sampleRate;
    
    // Multiple frequencies for richer sound
    const freq1 = 1200 + Math.random() * 300;
    const freq2 = 800 + Math.random() * 200;
    
    // Add randomness to create "clinking" effect
    const noise = (Math.random() * 2 - 1) * 0.2;
    
    // Combine with rapid decay
    let sample = 0;
    
    // First clink
    if (time < 0.15) {
      sample += 0.5 * Math.exp(-time * 30) * Math.sin(2 * Math.PI * freq1 * time);
    }
    
    // Second clink, slightly delayed
    if (time > 0.05 && time < 0.2) {
      const t2 = time - 0.05;
      sample += 0.6 * Math.exp(-t2 * 25) * Math.sin(2 * Math.PI * freq2 * t2);
    }
    
    // Third clink, further delayed
    if (time > 0.12 && time < 0.25) {
      const t3 = time - 0.12;
      sample += 0.4 * Math.exp(-t3 * 35) * Math.sin(2 * Math.PI * (freq1 + freq2) / 2 * t3);
    }
    
    // Add noise
    sample += noise * Math.exp(-time * 10);
    
    // Convert to 16-bit PCM
    const pcmSample = Math.floor(sample * 16384); // Lower amplitude to avoid clipping
    buffer.writeInt16LE(pcmSample, i * 2);
  }
  
  generateWav(buffer, 'chips.wav');
}

// Generate sounds
generateCheckSound();
generateChipsSound();

console.log('Sound generation complete');