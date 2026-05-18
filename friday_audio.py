import io
import wave
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3

# ── Tunable constants ─────────────────────────────────────────────────────────
SAMPLE_RATE     = 16000
CHUNK_MS        = 50                          # 50 ms per chunk
CHUNK_FRAMES    = int(SAMPLE_RATE * 0.05)
SPEECH_RMS      = 600        # RMS level that counts as voice (lower = more sensitive)
MIN_SPEECH_MS   = 600        # ignore anything shorter than 600 ms
SILENCE_STOP_MS = 1500       # stop after 1.5 s of silence after speech
MIN_CHUNKS      = MIN_SPEECH_MS   // CHUNK_MS   # 12
SILENCE_CHUNKS  = SILENCE_STOP_MS // CHUNK_MS   # 30
PRE_BUF_CHUNKS  = 6          # keep 300 ms before speech for natural start


class FridayAudio:
    def __init__(self):
        self.engine = pyttsx3.init()
        self._setup_voice()
        self.recognizer = sr.Recognizer()

    def _setup_voice(self):
        for v in self.engine.getProperty("voices"):
            if "Zira" in v.name or "female" in v.name.lower():
                self.engine.setProperty("voice", v.id)
                break
        self.engine.setProperty("rate", 165)
        self.engine.setProperty("volume", 1.0)

    # ── speak ─────────────────────────────────────────────────────────────────
    def speak(self, text: str):
        print(f"FRIDAY: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        time.sleep(0.6)   # let speaker echo die before mic activates

    # ── listen ────────────────────────────────────────────────────────────────
    def listen(self, max_duration: int = 12) -> str:
        """
        VAD-based listener.
        • Waits up to max_duration seconds for speech to start.
        • Records until 1.5 s of silence after speech.
        • Returns Google-recognised text (lower-case) or ''.
        """
        time.sleep(0.5)          # extra buffer after any preceding TTS
        print("Listening…")

        chunks        = []
        pre_buf       = []
        speech_count  = 0
        silence_count = 0
        speech_started = False

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                dtype="int16", blocksize=CHUNK_FRAMES) as stream:

                start = time.time()
                while time.time() - start < max_duration:
                    data, _ = stream.read(CHUNK_FRAMES)
                    rms = float(np.sqrt(np.mean(data.astype(np.float64) ** 2)))

                    # rolling pre-speech buffer
                    pre_buf.append(data.copy())
                    if len(pre_buf) > PRE_BUF_CHUNKS:
                        pre_buf.pop(0)

                    if rms >= SPEECH_RMS:
                        if not speech_started:
                            print(f"[Audio] Speech start (RMS {rms:.0f})")
                            speech_started = True
                            chunks.extend(pre_buf[:-1])
                        silence_count = 0
                        speech_count += 1
                        chunks.append(data.copy())

                    elif speech_started:
                        chunks.append(data.copy())
                        silence_count += 1
                        if silence_count >= SILENCE_CHUNKS:
                            print(f"[Audio] Speech end — {speech_count * CHUNK_MS} ms captured")
                            break

        except Exception as e:
            print(f"[Audio] Stream error: {e}")
            return ""

        if speech_count < MIN_CHUNKS:
            print(f"[Audio] Too short ({speech_count * CHUNK_MS} ms) — skipped")
            return ""

        # ── stitch chunks → in-memory WAV ─────────────────────────────────────
        audio_np = np.concatenate(chunks, axis=0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_np.tobytes())
        buf.seek(0)

        # ── Google STT ────────────────────────────────────────────────────────
        try:
            with sr.AudioFile(buf) as src:
                audio = self.recognizer.record(src)
            text = self.recognizer.recognize_google(audio)
            print(f"[Audio] Recognised: {text}")
            return text.lower()

        except sr.UnknownValueError:
            print("[Audio] Couldn't understand — too noisy or unclear")
            return ""
        except sr.RequestError as e:
            print(f"[Audio] Network error: {e}")
            return ""
        except Exception as e:
            print(f"[Audio] Recognition error: {e}")
            return ""