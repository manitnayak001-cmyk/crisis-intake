
import pyttsx3


_engine = None


def get_engine():
    global _engine

    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 175)
        _engine.setProperty("volume", 1.0)

    return _engine


def speak(text: str) -> None:
    """Speak text using the local system voice."""

    if not text.strip():
        return

    engine = get_engine()
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    speak(
        "Hello. I am the intake assistant. "
        "Can you tell me what happened?"
    )
