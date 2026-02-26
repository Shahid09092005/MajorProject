import pyttsx3
import speech_recognition as sr


_tts_engine = None


def _get_tts_engine():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", 160)
        _tts_engine.setProperty("volume", 0.9)
    return _tts_engine


def speak(text: str) -> None:
    """Convert text to speech using pyttsx3."""
    engine = _get_tts_engine()
    engine.say(text)
    engine.runAndWait()


def listen(timeout: int = 10, phrase_time_limit: int = 30) -> str:
    """Capture speech from microphone and return transcribed text.

    Args:
        timeout: Max seconds to wait for speech to start.
        phrase_time_limit: Max seconds for the full phrase.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    except Exception:
        return ""


def is_microphone_available() -> bool:
    """Check if a microphone is accessible."""
    try:
        with sr.Microphone() as _:
            return True
    except (OSError, AttributeError):
        return False
