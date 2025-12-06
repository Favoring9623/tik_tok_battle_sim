/**
 * TikTok Battle Simulator - Sound Effects Module
 *
 * Uses Web Audio API for low-latency sound playback.
 * Sounds are generated programmatically (no external files needed).
 */

class BattleSounds {
    constructor() {
        this.enabled = true;
        this.volume = 0.5;
        this.audioContext = null;
        this.initialized = false;
    }

    /**
     * Initialize audio context (must be called after user interaction)
     */
    init() {
        if (this.initialized) return;

        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.initialized = true;
            console.log('🔊 Sound system initialized');
        } catch (e) {
            console.warn('Audio not supported:', e);
            this.enabled = false;
        }
    }

    /**
     * Toggle sound on/off
     */
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }

    /**
     * Set volume (0-1)
     */
    setVolume(vol) {
        this.volume = Math.max(0, Math.min(1, vol));
    }

    /**
     * Play a tone with given parameters
     */
    playTone(frequency, duration, type = 'sine', attack = 0.01, decay = 0.1) {
        if (!this.enabled || !this.audioContext) return;

        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        oscillator.frequency.value = frequency;
        oscillator.type = type;

        const now = this.audioContext.currentTime;
        gainNode.gain.setValueAtTime(0, now);
        gainNode.gain.linearRampToValueAtTime(this.volume, now + attack);
        gainNode.gain.linearRampToValueAtTime(0, now + duration);

        oscillator.start(now);
        oscillator.stop(now + duration);
    }

    /**
     * Play multiple tones in sequence (arpeggio)
     */
    playArpeggio(frequencies, noteDuration = 0.1, type = 'sine') {
        if (!this.enabled || !this.audioContext) return;

        frequencies.forEach((freq, i) => {
            setTimeout(() => {
                this.playTone(freq, noteDuration * 1.5, type);
            }, i * noteDuration * 1000);
        });
    }

    // =========================================================================
    // Battle Event Sounds
    // =========================================================================

    /**
     * Gift received - pitch based on value
     */
    giftReceived(value) {
        if (!this.enabled) return;
        this.init();

        if (value >= 10000) {
            // Whale gift - epic fanfare
            this.playArpeggio([523, 659, 784, 1047], 0.15, 'triangle');
            setTimeout(() => this.playTone(1047, 0.5, 'triangle'), 600);
        } else if (value >= 1000) {
            // Large gift - triumphant
            this.playArpeggio([440, 554, 659], 0.12, 'triangle');
        } else if (value >= 100) {
            // Medium gift - pleasant chime
            this.playTone(880, 0.15, 'sine');
            setTimeout(() => this.playTone(1100, 0.15, 'sine'), 80);
        } else {
            // Small gift - soft blip
            this.playTone(660, 0.08, 'sine');
        }
    }

    /**
     * Glove sent
     */
    gloveSent() {
        if (!this.enabled) return;
        this.init();

        // Punch sound - low thump
        this.playTone(150, 0.1, 'square');
        this.playTone(100, 0.15, 'sine');
    }

    /**
     * Glove x5 activated!
     */
    gloveActivated() {
        if (!this.enabled) return;
        this.init();

        // Powerful activation sound
        this.playTone(200, 0.1, 'sawtooth');
        setTimeout(() => {
            this.playArpeggio([330, 440, 554, 659, 880], 0.08, 'square');
        }, 100);
        setTimeout(() => {
            this.playTone(880, 0.3, 'triangle');
        }, 500);
    }

    /**
     * Hammer used
     */
    hammerSmash() {
        if (!this.enabled) return;
        this.init();

        // Heavy impact
        this.playTone(80, 0.2, 'sawtooth');
        this.playTone(60, 0.3, 'sine');
        setTimeout(() => this.playTone(120, 0.1, 'square'), 100);
    }

    /**
     * Fog activated
     */
    fogActivated() {
        if (!this.enabled) return;
        this.init();

        // Mysterious whoosh
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();

        osc.connect(gain);
        gain.connect(this.audioContext.destination);

        osc.type = 'sine';
        osc.frequency.setValueAtTime(400, this.audioContext.currentTime);
        osc.frequency.exponentialRampToValueAtTime(100, this.audioContext.currentTime + 0.5);

        gain.gain.setValueAtTime(this.volume * 0.3, this.audioContext.currentTime);
        gain.gain.linearRampToValueAtTime(0, this.audioContext.currentTime + 0.5);

        osc.start();
        osc.stop(this.audioContext.currentTime + 0.5);
    }

    /**
     * Time bonus added
     */
    timeBonus() {
        if (!this.enabled) return;
        this.init();

        // Clock tick + chime
        this.playTone(1200, 0.05, 'square');
        setTimeout(() => this.playTone(1400, 0.05, 'square'), 100);
        setTimeout(() => this.playTone(1600, 0.1, 'sine'), 200);
    }

    /**
     * Phase change
     */
    phaseChange(multiplier) {
        if (!this.enabled) return;
        this.init();

        if (multiplier >= 5) {
            // x5 phase - intense
            this.playArpeggio([440, 554, 659, 880, 1047], 0.1, 'sawtooth');
        } else if (multiplier >= 2) {
            // Boost phase
            this.playArpeggio([440, 554, 659], 0.12, 'triangle');
        } else {
            // Normal phase
            this.playTone(440, 0.2, 'sine');
        }
    }

    /**
     * Battle start
     */
    battleStart() {
        if (!this.enabled) return;
        this.init();

        // Epic start fanfare
        setTimeout(() => this.playTone(440, 0.15, 'triangle'), 0);
        setTimeout(() => this.playTone(554, 0.15, 'triangle'), 150);
        setTimeout(() => this.playTone(659, 0.15, 'triangle'), 300);
        setTimeout(() => this.playTone(880, 0.4, 'triangle'), 450);
    }

    /**
     * Battle end
     */
    battleEnd(isWin) {
        if (!this.enabled) return;
        this.init();

        if (isWin) {
            // Victory fanfare
            this.playArpeggio([523, 659, 784, 1047], 0.2, 'triangle');
            setTimeout(() => {
                this.playTone(1047, 0.5, 'triangle');
            }, 800);
        } else {
            // Defeat sound
            this.playArpeggio([440, 349, 294], 0.2, 'sine');
        }
    }

    /**
     * Countdown tick (final seconds)
     */
    countdownTick(secondsLeft) {
        if (!this.enabled) return;
        this.init();

        if (secondsLeft <= 5) {
            this.playTone(800 + (5 - secondsLeft) * 100, 0.1, 'square');
        } else if (secondsLeft <= 10) {
            this.playTone(600, 0.05, 'sine');
        }
    }

    /**
     * Final 30 seconds dramatic urge - intense pulsing heartbeat
     */
    final30Seconds() {
        if (!this.enabled) return;
        this.init();

        // Dramatic low rumble + ascending tension
        this.playTone(60, 0.3, 'sine');
        this.playTone(80, 0.25, 'sawtooth');

        // Tension build arpeggio
        setTimeout(() => {
            this.playArpeggio([220, 277, 330, 415], 0.15, 'sawtooth');
        }, 300);

        // Final dramatic hit
        setTimeout(() => {
            this.playTone(110, 0.4, 'sawtooth');
            this.playTone(220, 0.3, 'triangle');
        }, 900);
    }

    /**
     * Heartbeat pulse for final countdown (call repeatedly)
     */
    heartbeat(intensity = 1) {
        if (!this.enabled) return;
        this.init();

        const baseFreq = 50 + (intensity * 20);
        const vol = this.volume * (0.3 + intensity * 0.2);

        // Double thump like heartbeat
        const osc1 = this.audioContext.createOscillator();
        const gain1 = this.audioContext.createGain();
        osc1.connect(gain1);
        gain1.connect(this.audioContext.destination);
        osc1.type = 'sine';
        osc1.frequency.value = baseFreq;

        const now = this.audioContext.currentTime;
        gain1.gain.setValueAtTime(0, now);
        gain1.gain.linearRampToValueAtTime(vol, now + 0.05);
        gain1.gain.linearRampToValueAtTime(0, now + 0.15);

        osc1.start(now);
        osc1.stop(now + 0.15);

        // Second beat (slightly softer)
        setTimeout(() => {
            const osc2 = this.audioContext.createOscillator();
            const gain2 = this.audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(this.audioContext.destination);
            osc2.type = 'sine';
            osc2.frequency.value = baseFreq * 0.9;

            const now2 = this.audioContext.currentTime;
            gain2.gain.setValueAtTime(0, now2);
            gain2.gain.linearRampToValueAtTime(vol * 0.7, now2 + 0.04);
            gain2.gain.linearRampToValueAtTime(0, now2 + 0.12);

            osc2.start(now2);
            osc2.stop(now2 + 0.12);
        }, 150);
    }

    /**
     * Boost condition met
     */
    boostQualified() {
        if (!this.enabled) return;
        this.init();

        // Achievement unlocked sound
        this.playArpeggio([523, 659, 784], 0.1, 'sine');
        setTimeout(() => this.playTone(1047, 0.3, 'triangle'), 300);
    }

    /**
     * Error/warning sound
     */
    warning() {
        if (!this.enabled) return;
        this.init();

        this.playTone(200, 0.1, 'sawtooth');
        setTimeout(() => this.playTone(200, 0.1, 'sawtooth'), 150);
    }

    /**
     * UI click sound
     */
    click() {
        if (!this.enabled) return;
        this.init();

        this.playTone(800, 0.03, 'sine');
    }
}

// Global instance
window.battleSounds = new BattleSounds();
