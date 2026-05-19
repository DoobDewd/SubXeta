"""Subtitle chunk grouping and processing."""
import json
import logging
from pathlib import Path
from typing import List
from core.models import Word, TextVariant

debug_logger = logging.getLogger(f"{__name__}.debug")


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
    debug_logger.debug(f"Grouping {len(words)} words into chunks (max_chars={max_chars_per_line}, pause_threshold={pause_threshold}s)")

    for i, word in enumerate(words):
        word_len = len(word.text)
        space_len = 1 if current_line else 0

        # Check line length limit
        if current_line and current_line_chars + space_len + word_len > max_chars_per_line:
            line_text = " ".join([w.text for w in current_line])
            debug_logger.debug(f"  Line break (word {i}): '{line_text}' exceeds {max_chars_per_line} chars ({current_line_chars + space_len + word_len})")
            current_chunk.append(current_line)
            current_line = []
            current_line_chars = 0

            if len(current_chunk) >= max_lines_per_chunk:
                chunk_text = " | ".join([" ".join([w.text for w in line]) for line in current_chunk])
                debug_logger.debug(f"  Chunk break (reached max_lines={max_lines_per_chunk}): {chunk_text[:60]}...")
                chunks.append(current_chunk)
                current_chunk = []

        current_line.append(word)
        current_line_chars += space_len + word_len

        # Check for sentence end
        if word.text.endswith((".", "!", "?")):
            line_text = " ".join([w.text for w in current_line])
            debug_logger.debug(f"  Sentence break (word {i}): '{line_text}' ends with punctuation")
            current_chunk.append(current_line)
            current_line = []
            current_line_chars = 0
            if len(current_chunk) >= 1:
                chunk_text = " | ".join([" ".join([w.text for w in line]) for line in current_chunk])
                debug_logger.debug(f"  Chunk finalized (sentence end): {chunk_text[:60]}...")
                chunks.append(current_chunk)
                current_chunk = []

        # Check for pause
        if i + 1 < len(words):
            gap = words[i + 1].start - word.end
            if gap > pause_threshold and (current_line or current_chunk):
                debug_logger.debug(f"  Pause break (word {i}→{i+1}): gap={gap:.3f}s > threshold={pause_threshold}s")
                if current_line:
                    current_chunk.append(current_line)
                    current_line = []
                    current_line_chars = 0
                if current_chunk:
                    chunk_text = " | ".join([" ".join([w.text for w in line]) for line in current_chunk])
                    debug_logger.debug(f"  Chunk finalized (pause): {chunk_text[:60]}...")
                    chunks.append(current_chunk)
                    current_chunk = []

    # Handle remaining content
    if current_line or current_chunk:
        if current_line:
            current_chunk.append(current_line)
        if current_chunk:
            chunk_text = " | ".join([" ".join([w.text for w in line]) for line in current_chunk])
            debug_logger.debug(f"  Final chunk: {chunk_text[:60]}...")
            chunks.append(current_chunk)

    debug_logger.debug(f"Grouping complete: {len(chunks)} chunks")

    # Edge case reporting
    for i, chunk in enumerate(chunks):
        chunk_words = sum(len(line) for line in chunk)
        if chunk_words == 1:
            debug_logger.debug(f"  WARN: Chunk {i} has only 1 word")

        # Calculate chunk duration
        all_words = []
        for line in chunk:
            all_words.extend(line)
        if all_words:
            duration = all_words[-1].end - all_words[0].start
            if duration < 0.5:
                debug_logger.debug(f"  WARN: Chunk {i} is very short ({duration:.3f}s)")

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
