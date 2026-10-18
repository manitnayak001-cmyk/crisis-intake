
import json
from tts import speak
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from llm import chat
from models import CaseFile
from agents.tools import TOOLS, execute_tool
from database import init_db, save_case
from main_simulation import build_intake_prompt, finalize_if_complete


SAMPLE_RATE = 16000
FRAME_SECONDS = 0.25
SILENCE_SECONDS = 1.8
SPEECH_THRESHOLD = 0.01
MAX_UTTERANCE_SECONDS = 20

FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_SECONDS)


def listen_for_utterance(stream, model) -> str:
    """Record speech until the caller pauses, then transcribe it."""

    audio_frames = []
    speech_started = False
    silent_frames = 0
    max_frames = int(MAX_UTTERANCE_SECONDS / FRAME_SECONDS)
    required_silence = int(SILENCE_SECONDS / FRAME_SECONDS)

    print("\nListening... Speak when ready.")

    while True:
        audio, overflowed = stream.read(FRAME_SAMPLES)
        frame = audio[:, 0].copy()

        if overflowed:
            print("Warning: microphone audio may have been dropped.")

        volume = float(np.sqrt(np.mean(frame ** 2)))

        if volume >= SPEECH_THRESHOLD:
            speech_started = True
            silent_frames = 0
            audio_frames.append(frame)

        elif speech_started:
            audio_frames.append(frame)
            silent_frames += 1

        if speech_started and (
            silent_frames >= required_silence
            or len(audio_frames) >= max_frames
        ):
            break

    audio_data = np.concatenate(audio_frames)

    print("Transcribing...")

    segments, _ = model.transcribe(
        audio_data,
        language="en",
        vad_filter=True,
        condition_on_previous_text=False,
    )

    transcript = " ".join(
        segment.text.strip() for segment in segments
    ).strip()

    if transcript:
        print(f"\nCaller: {transcript}")
    else:
        print("\nNo clear speech detected.")

    return transcript


def run_voice_intake():
    init_db()
    case = CaseFile()

    messages = [
        {
            "role": "system",
            "content": build_intake_prompt(),
        }
    ]

    print("Loading Whisper model...")
    model = WhisperModel(
        "base.en",
        device="cpu",
        compute_type="int8",
    )

    print("\n=== VOICE INTAKE TRAINING SIMULATOR ===")
    print("Speak into your microphone.")
    print("Press Ctrl+C to stop the simulation.")

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=FRAME_SAMPLES,
        ) as stream:

            while case.status != "finalized":
                transcript = listen_for_utterance(stream, model)

                if not transcript:
                    continue

                messages.append({
                    "role": "user",
                    "content": transcript,
                })

                # Keep processing tool calls until the intake agent
                # produces its next conversational response.
                while True:
                    response = chat(messages, tools=TOOLS)
                    message = response.choices[0].message

                    if message.tool_calls:
                        messages.append(message)

                        for tool_call in message.tool_calls:
                            result = execute_tool(
                                case=case,
                                tool_name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                            )

                            print(
                                f"\nTool: {tool_call.function.name}"
                            )
                            print(f"Result: {result}")

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result),
                            })

                        if case.status == "finalized":
                            case_id = save_case(case)
                            print(f"\nCase saved with ID: {case_id}")
                            break

                        if finalize_if_complete(case):
                            break

                        continue

                    reply = message.content or ""
                    messages.append(message)

                    print(f"\nIntake Agent: {reply}")
                    speak(reply)

                    if finalize_if_complete(case):
                        break

                    # Wait for the caller's next spoken response.
                    break

                if case.status == "finalized":
                    print("\nCase successfully finalized.")
                    break

    except KeyboardInterrupt:
        print("\nVoice intake stopped.")

    print("\n=== FINAL CASEFILE ===")
    print(case.model_dump_json(indent=2))


if __name__ == "__main__":
    run_voice_intake()
