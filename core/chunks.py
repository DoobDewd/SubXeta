"""Subtitle chunk grouping and processing."""
import json
import logging
from difflib import SequenceMatcher
from typing import List, Tuple
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


def group_into_chunks(words: List[Word], max_chars_per_line: int = 20, pause_threshold: float = 0.3, max_lines_per_chunk: int = 2) -> List[List[List[Word]]]:
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


def chunk_to_texts(chunk: List[List[Word]], pause_threshold: float = 0.3) -> TextVariant:
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


def _map_edited_words_to_original(original_words: List[str], edited_words: List[str]):
    """Map edited words to original words using sequence matching.

    When multiple edits map to the same original, timing is split proportionally.
    This enables: replacements (1 word → 2) and insertions (new word splits with adjacent).
    Edge case: truly orphan insertions fall back to copying adjacent timing.

    Returns (mapping dict, set of inserted word indices)."""
    debug_logger.debug(f"Word mapping: original={original_words} → edited={edited_words}")

    if not original_words:
        debug_logger.debug(f"No original words, mapping all {len(edited_words)} edited words to None")
        return {i: None for i in range(len(edited_words))}, set()

    # Use SequenceMatcher to find matching blocks
    matcher = SequenceMatcher(None, original_words, edited_words)
    matching_blocks = matcher.get_matching_blocks()
    debug_logger.debug(f"SequenceMatcher blocks: {matching_blocks}")

    # Build a mapping of edited word index to original word index
    mapping = {}
    used_original_indices = set()
    inserted_indices = set()  # Track which edited words are inserted (no original correspondence)

    for block in matching_blocks[:-1]:  # Skip the final end marker
        orig_start, edit_start, size = block
        debug_logger.debug(f"  Matching block: orig[{orig_start}:{orig_start+size}] ↔ edit[{edit_start}:{edit_start+size}]")
        # Map matched words
        for i in range(size):
            mapping[edit_start + i] = orig_start + i
            used_original_indices.add(orig_start + i)

    # Find unmatched original indices and edited positions
    unmatched_orig_indices = [i for i in range(len(original_words)) if i not in used_original_indices]
    unmatched_edit_indices = [i for i in range(len(edited_words)) if i not in mapping]

    debug_logger.debug(f"  Unmatched original indices: {unmatched_orig_indices}")
    debug_logger.debug(f"  Unmatched edited indices: {unmatched_edit_indices}")

    # Map unmatched edited words to unmatched original words in position order
    for edit_idx, orig_idx in zip(unmatched_edit_indices, unmatched_orig_indices):
        mapping[edit_idx] = orig_idx
        debug_logger.debug(f"    Mapping unmatched edit[{edit_idx}] → orig[{orig_idx}]")

    # Handle extra unmatched edits: map them to adjacent originals so timing can split with those words
    # This enables: replacements (1 word → 2) and insertions (new word → splits with adjacent)
    if len(unmatched_edit_indices) > len(unmatched_orig_indices):
        extra_edits = unmatched_edit_indices[len(unmatched_orig_indices):]
        for edit_idx in extra_edits:
            found = False
            # Try backwards for adjacent word's original
            for check_idx in range(edit_idx - 1, -1, -1):
                if check_idx in mapping:
                    mapping[edit_idx] = mapping[check_idx]
                    debug_logger.debug(f"    Mapping edit[{edit_idx}] → orig[{mapping[edit_idx]}] (will split with preceding edit[{check_idx}])")
                    found = True
                    break
            if not found:
                # Try forwards for adjacent word's original
                for check_idx in range(edit_idx + 1, len(edited_words)):
                    if check_idx in mapping:
                        mapping[edit_idx] = mapping[check_idx]
                        debug_logger.debug(f"    Mapping edit[{edit_idx}] → orig[{mapping[edit_idx]}] (will split with following edit[{check_idx}])")
                        found = True
                        break
            if not found:
                # Fallback: map to first original
                mapping[edit_idx] = 0
                debug_logger.debug(f"    Mapping edit[{edit_idx}] → orig[0] (fallback)")

    # Detect which originals have multiple edits mapping to them
    # Multiple edits to same original triggers proportional split timing
    orig_edit_count = {}
    for edit_idx, orig_idx in mapping.items():
        orig_edit_count[orig_idx] = orig_edit_count.get(orig_idx, 0) + 1

    # Edge case: mark as inserted only if original has single edit (fallback for orphan words)
    # In practice, most edits will have multiple companions, triggering split instead
    for edit_idx in list(inserted_indices):
        orig_idx = mapping.get(edit_idx)
        if orig_idx is not None and orig_edit_count.get(orig_idx, 0) > 1:
            inserted_indices.discard(edit_idx)
        elif orig_idx is not None:
            debug_logger.debug(f"    Edit[{edit_idx}] → orig[{orig_idx}] marked as inserted (fallback)")

    debug_logger.debug(f"Final word mapping: {mapping}, inserted: {inserted_indices}")
    return mapping, inserted_indices


def rebuild_chunks_with_edits(original_chunks: List[List[List[Word]]], edited_chunks: List[Tuple[str, str]], edited_flags: List[bool]) -> List[List[List[Word]]]:
    """Rebuild chunks with edited text but original timing, handling word mapping and proportional splits."""
    rebuilt_chunks = []
    debug_logger.debug(f"Starting chunk reconstruction from {len(edited_chunks)} chunks")

    # Edge case: check for empty edits
    empty_chunks = [i for i, (_, text) in enumerate(edited_chunks) if not text.strip()]
    if empty_chunks:
        debug_logger.debug(f"WARN: {len(empty_chunks)} empty chunks: {empty_chunks}")

    for chunk_idx, (timestamp_str, edited_text) in enumerate(edited_chunks):
        # If chunk wasn't edited, use the original chunk structure as-is
        if chunk_idx < len(edited_flags) and not edited_flags[chunk_idx]:
            debug_logger.debug(f"Chunk {chunk_idx}: UNEDITED, using original structure")
            if chunk_idx < len(original_chunks):
                rebuilt_chunks.append(original_chunks[chunk_idx])
            continue

        debug_logger.debug(f"Chunk {chunk_idx}: EDITED, reconstructing with new text")

        # Chunk was edited, so reconstruct it with new text and timing
        if chunk_idx < len(original_chunks):
            original_chunk = original_chunks[chunk_idx]
        else:
            original_chunk = []
            debug_logger.debug(f"  No original chunk at index {chunk_idx}, starting from scratch")

        chunk_lines = []
        # Split by newlines to preserve line structure
        text_lines = edited_text.split('\n')
        debug_logger.debug(f"  Edited text has {len(text_lines)} line(s)")

        for line_idx, text_line in enumerate(text_lines):
            edited_words = text_line.split()
            debug_logger.debug(f"  Line {line_idx}: {len(edited_words)} edited words: {edited_words}")

            # Get original words for this specific line
            if line_idx < len(original_chunk):
                original_words_list = original_chunk[line_idx]
            else:
                original_words_list = []

            # Map edited words to original words using sequence matching
            original_texts = [w.text for w in original_words_list] if original_words_list else []
            debug_logger.debug(f"    Original line {line_idx}: {original_texts}")
            word_mapping, inserted_indices = _map_edited_words_to_original(original_texts, edited_words)

            line_words = []
            current_line_chars = 0

            # Track which original words have been used for split timing
            split_words = {}

            # Map edited text back to original words
            for edit_idx, word_text in enumerate(edited_words):
                word_len = len(word_text)
                space_len = 1 if line_words else 0

                # Break line if exceeds 20 chars
                if line_words and current_line_chars + space_len + word_len > 20:
                    debug_logger.debug(f"      Line break at word {edit_idx} (total chars would be {current_line_chars + space_len + word_len})")
                    chunk_lines.append(line_words)
                    line_words = []
                    current_line_chars = 0

                # Get the original word this edited word maps to
                orig_idx = word_mapping.get(edit_idx)
                debug_logger.debug(f"      Word {edit_idx}: '{word_text}' maps to original[{orig_idx}]")

                if orig_idx is not None and orig_idx < len(original_words_list):
                    original_word = original_words_list[orig_idx]

                    # Check if this original word needs to be split among multiple edited words
                    # Only count non-inserted words for split timing
                    matching_edited_indices = [i for i, o in word_mapping.items() if o == orig_idx and i not in inserted_indices]

                    if len(matching_edited_indices) > 1:
                        # This original word is being split among multiple edited words
                        if orig_idx not in split_words:
                            # First time encountering this split: calculate split timing
                            duration = original_word.end - original_word.start
                            num_parts = len(matching_edited_indices)
                            split_duration = duration / num_parts
                            split_words[orig_idx] = split_duration
                            debug_logger.debug(f"        SPLIT: Original[{orig_idx}] (duration={duration:.3f}s) split into {num_parts} parts ({split_duration:.3f}s each)")

                        position = matching_edited_indices.index(edit_idx)
                        start_time = original_word.start + (split_words[orig_idx] * position)
                        end_time = original_word.start + (split_words[orig_idx] * (position + 1))
                        debug_logger.debug(f"        Part {position+1}/{len(matching_edited_indices)}: {start_time:.3f}s → {end_time:.3f}s")
                        edited_word = Word(
                            text=word_text,
                            start=start_time,
                            end=end_time
                        )
                    else:
                        # This edited word maps directly to one original word
                        debug_logger.debug(f"        Direct map: {original_word.start:.3f}s → {original_word.end:.3f}s")
                        edited_word = Word(
                            text=word_text,
                            start=original_word.start,
                            end=original_word.end
                        )
                else:
                    debug_logger.debug(f"      Skipping word {edit_idx}: no mapping found")
                    continue

                line_words.append(edited_word)
                current_line_chars += space_len + word_len

            if line_words:
                chunk_lines.append(line_words)

        if chunk_lines:
            rebuilt_chunks.append(chunk_lines)

    debug_logger.debug(f"Chunk reconstruction complete: {len(rebuilt_chunks)} rebuilt chunks")
    return rebuilt_chunks


def _chunk_start(chunk: List[List[Word]]):
    """Start time of a chunk, or None if it has no words."""
    if chunk and chunk[0]:
        return chunk[0][0].start
    return None


def merge_chunks_by_time(original_chunks: List[List[List[Word]]],
                         manual_chunks: List[List[List[Word]]]) -> List[List[List[Word]]]:
    """Merge original and manually-added chunks into one list sorted by start time."""
    combined = []
    for chunk in original_chunks:
        start = _chunk_start(chunk)
        if start is not None:
            combined.append((start, chunk))
    for chunk in manual_chunks:
        start = _chunk_start(chunk)
        if start is not None:
            combined.append((start, chunk))

    combined.sort(key=lambda pair: pair[0])
    debug_logger.debug(f"Merged {len(original_chunks)} original + {len(manual_chunks)} manual "
                       f"into {len(combined)} chunks sorted by time")
    return [chunk for _, chunk in combined]


def assemble_final_chunks(original_chunks: List[List[List[Word]]],
                          edited_chunks: List[Tuple[str, str]],
                          edited_flags: List[bool],
                          manual_timestamps: List[float],
                          manually_added_chunks: List[List[List[Word]]],
                          deleted_timestamps) -> List[List[List[Word]]]:
    """Build the final ordered chunk list for comp generation.

    Drops manual and deleted entries from the edit set, rebuilds the surviving
    original (transcribed) chunks with their edited text/timing, then merges in
    the surviving manually-added chunks sorted by start time.

    Args:
        original_chunks: transcribed chunks (word structures) from grouping.
        edited_chunks: (timestamp_str, text) for every displayed chunk.
        edited_flags: per-chunk "was edited" flags, aligned with edited_chunks.
        manual_timestamps: start times (float) of manually-added chunks.
        manually_added_chunks: word structures for manually-added chunks.
        deleted_timestamps: set of timestamp strings the user deleted.
    """
    # Keep only original (non-manual, non-deleted) edits for the rebuild step
    original_edits = []
    original_edit_flags = []
    for i, (ts, text) in enumerate(edited_chunks):
        ts_float = float(ts)
        is_manual = any(abs(ts_float - mt) < 0.001 for mt in manual_timestamps)
        is_deleted = ts in deleted_timestamps
        if not is_manual and not is_deleted:
            original_edits.append((ts, text))
            original_edit_flags.append(edited_flags[i])

    debug_logger.debug(f"Assembling: {len(original_edits)} original edits "
                       f"(excluded {len(manual_timestamps)} manual, {len(deleted_timestamps)} deleted)")

    # Drop deleted chunks from the original transcription before rebuilding
    surviving_original = [
        chunk for chunk in original_chunks
        if not any(abs(chunk[0][0].start - float(ts)) < 0.001 for ts in deleted_timestamps)
    ]

    rebuilt_original = rebuild_chunks_with_edits(surviving_original, original_edits, original_edit_flags)

    # Drop deleted manually-added chunks
    surviving_manual = []
    for i, chunk in enumerate(manually_added_chunks):
        if i < len(manual_timestamps):
            ts = manual_timestamps[i]
            if not any(abs(ts - float(dts)) < 0.001 for dts in deleted_timestamps):
                surviving_manual.append(chunk)

    return merge_chunks_by_time(rebuilt_original, surviving_manual)
