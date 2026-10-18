
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
RECORD_SECONDS = 12
AUDIO_PATH = "recording.wav"


def record_audio() -> str:
    """Record a short clip from the default microphone."""

    print(f"\nRecording for {RECORD_SECONDS} seconds...")
    print("Speak clearly into your microphone.")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )

    sd.wait()

    write(AUDIO_PATH, SAMPLE_RATE, audio)

    print(f"Audio saved to {AUDIO_PATH}")
    return AUDIO_PATH


def transcribe_audio(audio_path: str) -> str:
    """Convert a WAV audio file into text."""

    print("\nLoading speech recognition model...")

    model = WhisperModel(
        "base.en",
        device="cpu",
        compute_type="int8",
    )

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
    )

    transcription = " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()

    print(f"\nDetected language: {info.language}")
    print(f"Transcription: {transcription}")

    return transcription


if __name__ == "__main__":
    audio_path = record_audio()
    transcribe_audio(audio_path)
