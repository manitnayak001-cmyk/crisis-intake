
import queue

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
BLOCK_SIZE = 8000       # 0.5 seconds of audio
CHUNK_SECONDS = 3
OVERLAP_SECONDS = 0.5

CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_SECONDS
OVERLAP_SAMPLES = int(SAMPLE_RATE * OVERLAP_SECONDS)

audio_queue = queue.Queue(maxsize=20)


def audio_callback(indata, frames, time_info, status):
    """Receive microphone audio without running the model here."""

    if status:
        print(f"\nAudio status: {status}")

    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        # Drop a block if transcription cannot keep up.
        pass


def main():
    print("Loading Whisper model...")
    model = WhisperModel(
        "base.en",
        device="cpu",
        compute_type="int8",
    )

    audio_buffer = np.empty((0, 1), dtype=np.float32)

    print("\nLive transcription started.")
    print("Speak into your microphone. Press Ctrl+C to stop.\n")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            callback=audio_callback,
        ):
            while True:
                # Collect incoming audio blocks.
                block = audio_queue.get(timeout=2)
                audio_buffer = np.concatenate(
                    (audio_buffer, block),
                    axis=0,
                )

                # Wait until we have enough audio to transcribe.
                if len(audio_buffer) < CHUNK_SAMPLES:
                    continue

                # Transcribe one chunk.
                chunk = audio_buffer[:CHUNK_SAMPLES, 0].copy()

                # Keep a little overlap to reduce cut-off words.
                audio_buffer = audio_buffer[
                    CHUNK_SAMPLES - OVERLAP_SAMPLES:
                ].copy()

                segments, _ = model.transcribe(
                    chunk,
                    language="en",
                    vad_filter=True,
                    condition_on_previous_text=False,
                )

                text = " ".join(
                    segment.text.strip()
                    for segment in segments
                ).strip()

                if text:
                    print(f"You said: {text}")

    except KeyboardInterrupt:
        print("\nLive transcription stopped.")


if __name__ == "__main__":
    main()
