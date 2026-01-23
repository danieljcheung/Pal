// Sound utility for Pal
// Plays a soft chime when Pal sends a message

let audioContext: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext();
  }
  return audioContext;
}

// Play a soft, pleasant chime sound
export function playChime() {
  try {
    const ctx = getAudioContext();

    // Create oscillator for the main tone
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    // Configure oscillator - soft sine wave
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(880, ctx.currentTime); // A5 note

    // Configure gain envelope - soft attack and decay
    const now = ctx.currentTime;
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(0.15, now + 0.02); // Quick attack
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.3); // Gentle decay

    // Play
    oscillator.start(now);
    oscillator.stop(now + 0.3);

    // Add a subtle harmonic
    const harmonic = ctx.createOscillator();
    const harmonicGain = ctx.createGain();

    harmonic.connect(harmonicGain);
    harmonicGain.connect(ctx.destination);

    harmonic.type = "sine";
    harmonic.frequency.setValueAtTime(1320, now); // E6 note (perfect fifth above)

    harmonicGain.gain.setValueAtTime(0, now);
    harmonicGain.gain.linearRampToValueAtTime(0.05, now + 0.02);
    harmonicGain.gain.exponentialRampToValueAtTime(0.01, now + 0.25);

    harmonic.start(now);
    harmonic.stop(now + 0.25);

  } catch (err) {
    console.warn("Could not play sound:", err);
  }
}

// Resume audio context if suspended (needed for user interaction requirement)
export async function resumeAudio() {
  if (audioContext && audioContext.state === "suspended") {
    await audioContext.resume();
  }
}
