"""What the voice is given to say: prose cut into sentences and tidied, and code read the way a person says it."""

from voce.speech.code import spoken_code, spoken_line, spoken_name, spoken_path
from voce.speech.prose import speakable
from voce.speech.sentences import ABBREVIATIONS, sentences

__all__ = ["ABBREVIATIONS", "sentences", "speakable", "spoken_code", "spoken_line", "spoken_name", "spoken_path"]
