"""Subtitle chunk grouping and processing."""
import json
from pathlib import Path
from typing import List
from core.models import Word, TextVariant


def load_whisper_json(json_path: str) -> List[Word]:
    """Parse WhisperX JSON, return list of Word objects."""
    with open(json_path) as f:
        data = json.load(f)

    words = []
    segments = data.get("segments", [])

    for segment in segments:
        for word_obj in segment.get("words", []):
            text = word_obj["word"].strip()
            if text:
                words.append(Word(
                    text=text,
                    start=word_obj["start"],
                    end=word_obj["end"]
                ))

    return words


def group_into_chunks(words: List[Word], max_chars_per_line: int = 30, pause_threshold: float = 0.9, max_lines_per_chunk: int = 2) -> List[List[List[Word]]]:
    """Group words into subtitle chunks, breaking at pauses and character width limits."""
    chunks = []
    current_chunk = []
    current_line = []
    current_line_chars = 0

    for i, word in enumerate(words):
        word_len = len(word.text)
        space_len = 1 if current_line else 0

        if current_line and current_line_chars + space_len + word_len > max_chars_per_line:
            current_chunk.append(current_line)
            current_line = []
            current_line_chars = 0

            if len(current_chunk) >= max_lines_per_chunk:
                chunks.append(current_chunk)
                current_chunk = []

        current_line.append(word)
        current_line_chars += space_len + word_len

        if word.text.endswith((".", "!", "?")):
            current_chunk.append(current_line)
            current_line = []
            current_line_chars = 0
            if len(current_chunk) >= 1:
                chunks.append(current_chunk)
                current_chunk = []

        if i + 1 < len(words):
            gap = words[i + 1].start - word.end
            if gap > pause_threshold and (current_line or current_chunk):
                if current_line:
                    current_chunk.append(current_line)
                    current_line = []
                    current_line_chars = 0
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []

    if current_line or current_chunk:
        if current_line:
            current_chunk.append(current_line)
        if current_chunk:
            chunks.append(current_chunk)

    return chunks


def chunk_to_texts(chunk: List[List[Word]], pause_threshold: float = 0.9) -> TextVariant:
    """Convert chunk to English and alien text strings, preserving lines and adding pauses."""
    english_lines = []
    alien_lines = []

    for line in chunk:
        english_parts = []
        alien_parts = []

        for i, word in enumerate(line):
            english_parts.append(word.text)
            alien_parts.append(word.text)

            if i + 1 < len(line):
                gap = line[i + 1].start - word.end
                if gap > pause_threshold:
                    english_parts.append("\n")
                    alien_parts.append("\n")

        english_lines.append(" ".join(english_parts))
        alien_lines.append(" ".join(alien_parts))

    english_text = "\\n".join(english_lines)
    alien_text = "\\n".join(alien_lines)

    return TextVariant(english=english_text, alien=alien_text)
