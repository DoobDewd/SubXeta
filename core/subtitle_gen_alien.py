#!/usr/bin/env python3
"""
WhisperX → DaVinci Resolve Fusion comp automation.
Takes WhisperX JSON (word-level timestamps) and generates a single subtitle comp.
"""
import logging
from pathlib import Path
from typing import List
from core.models import Word
from core.chunks import chunk_to_texts

debug_logger = logging.getLogger(f"{__name__}.debug")


def get_available_templates() -> List[str]:
    """Get list of available template filenames."""
    templates_dir = Path(__file__).parent.parent / "templates"
    if not templates_dir.exists():
        return []
    return sorted([f.name for f in templates_dir.glob("*.comp")])


def load_template(template_name: str = "Zeta Reticuli Template.comp") -> str:
    """Load the Fusion comp template from templates folder."""
    template_path = Path(__file__).parent.parent / "templates" / template_name
    with open(template_path) as f:
        return f.read()


def generate_text_keyframes(chunks: List[List[List[Word]]], fps: int, is_english: bool, pause_threshold: float = 0.3) -> str:
    """Generate BezierSpline keyframes with text values for all chunks."""
    keyframes_lines = []
    text_type = "English" if is_english else "Alien"
    debug_logger.debug(f"Generating {text_type} text keyframes for {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        all_words = []
        for line in chunk:
            all_words.extend(line)

        start_time = all_words[0].start
        start_frame = round(start_time * fps)

        text_variant = chunk_to_texts(chunk, pause_threshold)
        text = text_variant.english if is_english else text_variant.alien

        escaped_text = text.replace('"', '\\"')
        debug_logger.debug(f"  Chunk {i}: frame {start_frame}, text: {text[:50]}..." if len(text) > 50 else f"  Chunk {i}: frame {start_frame}, text: {text}")

        if i == 0 and len(chunks) > 1:
            next_frame = round(chunks[i + 1][0][0].start * fps)
            rh_frame = start_frame + (next_frame - start_frame) // 3
            handles = f"{i}, RH = " + "{ " + f"{rh_frame}, {i}.333333333333333" + " }"
            debug_logger.debug(f"    First chunk: RH frame at {rh_frame}")
        elif i == len(chunks) - 1 and i > 0:
            prev_frame = round(chunks[i - 1][0][0].start * fps)
            lh_frame = prev_frame + (start_frame - prev_frame) // 3
            handles = "LH = " + "{ " + f"{lh_frame}, {i - 1}.666666666666667" + " }" + f", {i}"
            debug_logger.debug(f"    Last chunk: LH frame at {lh_frame}")
        elif len(chunks) > 1:
            prev_frame = round(chunks[i - 1][0][0].start * fps)
            next_frame = round(chunks[i + 1][0][0].start * fps)
            lh_frame = prev_frame + (start_frame - prev_frame) // 3
            rh_frame = start_frame + (next_frame - start_frame) // 3
            handles = "LH = " + "{ " + f"{lh_frame}, {i - 1}.666666666666667" + " }" + f", {i}, RH = " + "{ " + f"{rh_frame}, {i}.333333333333333" + " }"
            debug_logger.debug(f"    Middle chunk: LH at {lh_frame}, RH at {rh_frame}")
        else:
            handles = str(i)
            debug_logger.debug(f"    Single chunk")

        frame_line = (
            f"\t\t\t\t[{start_frame}] = " + "{ " + handles + ", Flags = { Linear = true, LockedY = true }, Value = Text {\n"
            f"\t\t\t\t\tValue = \"{escaped_text}\"\n"
            "\t\t\t\t} }"
        )

        keyframes_lines.append(frame_line)

    return "{\n" + ",\n".join(keyframes_lines) + "\n\t\t\t}"


def generate_animation_keyframes(chunks: List[List[List[Word]]], fps: int, pause_threshold: float = 0.3, frame_offset: int = 0) -> str:
    """Generate animation keyframes - each chunk animates 0->1, with reset at next chunk."""
    keyframes = {}
    reset_frames = []
    debug_logger.debug(f"Generating animation keyframes for {len(chunks)} chunks at {fps} fps, frame_offset={frame_offset}")

    # Ensure frame 1 starts at 0.0 (nothing revealed before first chunk)
    keyframes[1] = 0.0

    for chunk_idx, chunk in enumerate(chunks):
        all_words = []
        for line in chunk:
            all_words.extend(line)

        # Edge case checks
        if not all_words:
            debug_logger.debug(f"WARN: Chunk {chunk_idx} is empty, skipping")
            continue

        start_time = all_words[0].start
        end_time = all_words[-1].end
        duration = end_time - start_time

        # Check for zero-duration chunks
        if duration <= 0:
            debug_logger.debug(f"WARN: Chunk {chunk_idx} has zero/negative duration ({start_time:.3f}s → {end_time:.3f}s)")

        # Check for zero-duration words
        zero_duration_words = [w.text for w in all_words if w.end - w.start <= 0]
        if zero_duration_words:
            debug_logger.debug(f"WARN: Chunk {chunk_idx} has {len(zero_duration_words)} zero-duration words: {zero_duration_words}")

        text_variant = chunk_to_texts(chunk, pause_threshold)
        english_text = text_variant.english
        total_len_eng = len(english_text.replace("\\n", "\n"))

        debug_logger.debug(f"Chunk {chunk_idx}: {len(all_words)} words, {start_time:.3f}s → {end_time:.3f}s, text_len={total_len_eng}")

        word_char_positions = []
        word_end_positions = []
        char_pos = 0
        for i, word in enumerate(all_words):
            word_char_positions.append(char_pos)
            char_pos += len(word.text)
            word_end_positions.append(char_pos)
            if i < len(all_words) - 1:
                char_pos += 1

        start_frame = round(start_time * fps) - frame_offset
        final_frame = round(end_time * fps) - frame_offset
        debug_logger.debug(f"  Frame range: {start_frame} → {final_frame} ({final_frame - start_frame + 1} frames)")

        # Sparse keyframing: generate keyframes only when characters are revealed
        char_keyframe_count = 0
        for char_idx in range(total_len_eng):
            progress = (char_idx + 1) / total_len_eng
            progress = min(1.0, progress)

            # Find which word contains this character
            word_idx = None
            char_in_word = None
            for i in range(len(all_words)):
                if word_char_positions[i] <= char_idx < word_end_positions[i]:
                    word_idx = i
                    char_in_word = char_idx - word_char_positions[i]
                    break

            if word_idx is None:
                # Character is likely in spacing between words
                continue

            word = all_words[word_idx]
            word_duration = word.end - word.start
            if word_duration <= 0:
                continue

            # Calculate reveal time for this character within the word
            char_fraction = char_in_word / len(word.text)
            reveal_time = word.start + char_fraction * word_duration
            frame = round(reveal_time * fps) - frame_offset

            # Only add keyframe if this frame hasn't been added yet
            if frame not in keyframes:
                keyframes[frame] = progress
                char_keyframe_count += 1

        debug_logger.debug(f"  Sparse keyframes: {char_keyframe_count} character-based keyframes (vs {final_frame - start_frame + 1} frames)")

        keyframes[final_frame] = 1.0

        if chunk_idx < len(chunks) - 1:
            next_chunk = chunks[chunk_idx + 1]
            next_words = []
            for line in next_chunk:
                next_words.extend(line)
            next_start_time = next_words[0].start
            next_start_frame = round(next_start_time * fps)

            # Sparse hold: just two boundary keyframes instead of one per frame
            if next_start_frame > final_frame:
                keyframes[next_start_frame - 1] = 1.0
                debug_logger.debug(f"  Hold at 1.0 until frame {next_start_frame - 1}")

            if next_start_frame != final_frame:
                reset_frames.append(next_start_frame)
                debug_logger.debug(f"  Reset to 0.0 at frame {next_start_frame}")

    for reset_frame in reset_frames:
        keyframes[reset_frame] = 0.0

    debug_logger.debug(f"Final animation keyframes: {len(keyframes)} total frames with {len(reset_frames)} resets")

    lines = []
    for frame in sorted(keyframes.keys()):
        val = keyframes[frame]
        lines.append(
            f"\t\t\t\t\t[{frame}] = {{ {val:.6f}, RH = {{ {frame}, {val:.6f} }}, "
            f"Flags = {{ Linear = true }} }},"
        )
    return "{\n" + "\n".join(lines) + "\n\t\t\t\t}"


def generate_jpeg_damage_keyframes(chunks: List[List[List[Word]]], fps: int,
                                   start_value: float, mid_value: float, label: str = "") -> str:
    """Generate JPEG-damage keyframes: start_value at each chunk start, mid_value
    at its midpoint (degrade then reset at the next chunk). Used for both the
    quality and resolution splines, which differ only in their two values."""
    keyframes = {}
    debug_logger.debug(f"Generating JPEG damage {label} keyframes for {len(chunks)} chunks")

    for chunk_idx, chunk in enumerate(chunks):
        all_words = []
        for line in chunk:
            all_words.extend(line)

        if not all_words:
            debug_logger.debug(f"WARN: Chunk {chunk_idx} is empty, skipping")
            continue

        start_time = all_words[0].start
        end_time = all_words[-1].end
        duration = end_time - start_time

        start_frame = round(start_time * fps)
        mid_frame = round((start_time + duration / 2) * fps)

        # Start of chunk: clear, fresh alien text
        keyframes[start_frame] = start_value
        debug_logger.debug(f"  Chunk {chunk_idx}: frame {start_frame} = {start_value} (start/clear)")

        # Midpoint of chunk: degraded/corrupted alien text
        keyframes[mid_frame] = mid_value
        debug_logger.debug(f"  Chunk {chunk_idx}: frame {mid_frame} = {mid_value} (midpoint/degraded)")

    debug_logger.debug(f"Final JPEG damage {label} keyframes: {len(keyframes)} keyframes")

    # Generate keyframe output
    lines = []
    for frame in sorted(keyframes.keys()):
        val = keyframes[frame]
        lines.append(
            f"\t\t\t\t\t[{frame}] = {{ {val:.2f}, RH = {{ {frame}, {val:.2f} }}, "
            f"Flags = {{ Linear = true }} }},"
        )
    return "{\n" + "\n".join(lines) + "\n\t\t\t\t}"


def replace_keyframes_block(content: str, spline_name: str, new_keyframes: str) -> str:
    """Replace KeyFrames block within a specific BezierSpline."""
    search_str = f'{spline_name} = BezierSpline'
    idx = content.find(search_str)

    if idx < 0:
        debug_logger.debug(f"WARN: Spline '{spline_name}' not found in template - keyframes may not be replaced!")
        return content

    debug_logger.debug(f"Found spline '{spline_name}' at position {idx}")

    keyframes_start = content.find('KeyFrames = {', idx)
    if keyframes_start < 0:
        debug_logger.debug(f"WARN: KeyFrames block not found for '{spline_name}' - replacement failed!")
        return content

    keyframes_start += len('KeyFrames = ')
    debug_logger.debug(f"  KeyFrames block starts at {keyframes_start}")

    brace_count = 0
    pos = keyframes_start
    while pos < len(content):
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
            if brace_count == 0:
                break
        pos += 1

    keyframes_end = pos + 1
    old_keyframes_size = keyframes_end - keyframes_start
    new_keyframes_size = len(new_keyframes)
    debug_logger.debug(f"  Replaced {old_keyframes_size} bytes with {new_keyframes_size} bytes")

    return content[:keyframes_start] + new_keyframes + content[keyframes_end:]


def generate_single_comp(chunks: List[List[List[Word]]], fps: int, pause_threshold: float = 0.3, template_name: str = "Zeta Reticuli Template.comp") -> str:
    """Generate a single comp with keyframed text for all chunks."""
    debug_logger.debug(f"Starting comp generation: {len(chunks)} chunks, {fps} fps, template: {template_name}")

    try:
        content = load_template(template_name)
        debug_logger.debug(f"Template loaded: {len(content)} bytes")
    except Exception as e:
        debug_logger.debug(f"ERROR: Failed to load template: {e}")
        return ""

    if not chunks:
        debug_logger.debug("WARN: No chunks provided, returning empty template")
        return content

    all_words = []
    for chunk in chunks:
        for line in chunk:
            all_words.extend(line)

    if all_words:
        end_time = all_words[-1].end
        total_frames = round(end_time * fps)
        debug_logger.debug(f"Content duration: {end_time:.3f}s = {total_frames} frames")
    else:
        total_frames = 333
        debug_logger.debug("WARN: No words found, using default frame range")

    debug_logger.debug(f"Updating render range to: 0 → {total_frames}")
    content = content.replace(
        'RenderRange = { 0, 333 }',
        f'RenderRange = {{ 0, {total_frames} }}'
    )
    content = content.replace(
        'GlobalRange = { 0, 333 }',
        f'GlobalRange = {{ 0, {total_frames} }}'
    )

    debug_logger.debug("Generating text keyframes (English and Alien)...")
    alien_keyframes = generate_text_keyframes(chunks, fps, False, pause_threshold)
    english_keyframes = generate_text_keyframes(chunks, fps, True, pause_threshold)

    content = content.replace(
        'StyledText = Input { Value = "this is alien text", },',
        'StyledText = Input { SourceOp = "TemplateStyledText", Source = "Value", },'
    )

    content = content.replace(
        'StyledText = Input { Value = "this is english text", },',
        'StyledText = Input { SourceOp = "Template_1StyledText", Source = "Value", },'
    )

    alien_spline = f"""TemplateStyledText = BezierSpline {{
\t\tSplineColor = {{ Red = 237, Green = 142, Blue = 243 }},
\t\tNameSet = true,
\t\tKeyFrames = {alien_keyframes}
\t}},
"""

    english_spline = f"""Template_1StyledText = BezierSpline {{
\t\tSplineColor = {{ Red = 200, Green = 150, Blue = 200 }},
\t\tNameSet = true,
\t\tKeyFrames = {english_keyframes}
\t}},
"""

    tools_idx = content.find('\t\tTemplateWriteOnEnd = BezierSpline')
    if tools_idx > 0:
        content = content[:tools_idx] + alien_spline + english_spline + content[tools_idx:]

    debug_logger.debug("Generating animation keyframes (English and Alien)...")
    alien_anim_keyframes = generate_animation_keyframes(chunks, fps, pause_threshold, frame_offset=0)
    english_anim_keyframes = generate_animation_keyframes(chunks, fps, pause_threshold, frame_offset=0)

    if all_words:
        end_time = all_words[-1].end
        final_frame = round(end_time * fps)
    else:
        final_frame = 333

    const_one_keyframes = f"""{{
\t\t\t\t\t[0] = {{ 1.0, RH = {{ 0, 1.0 }}, Flags = {{ Linear = true }} }},
\t\t\t\t\t[{final_frame}] = {{ 1.0, LH = {{ {final_frame}, 1.0 }}, Flags = {{ Linear = true }} }}
\t\t\t\t}}"""

    const_zero_keyframes = f"""{{
\t\t\t\t\t[0] = {{ 0.0, RH = {{ 0, 0.0 }}, Flags = {{ Linear = true }} }},
\t\t\t\t\t[{final_frame}] = {{ 0.0, LH = {{ {final_frame}, 0.0 }}, Flags = {{ Linear = true }} }}
\t\t\t\t}}"""

    debug_logger.debug("Generating JPEG damage keyframes (alien text degradation)...")
    jpeg_damage_quality = generate_jpeg_damage_keyframes(chunks, fps, 68.82, 10.0, "quality")
    jpeg_damage_resolution = generate_jpeg_damage_keyframes(chunks, fps, 1.0, 1.87, "resolution")

    debug_logger.debug("Replacing keyframe blocks in template...")
    content = replace_keyframes_block(content, 'TemplateWriteOnStart', alien_anim_keyframes)
    content = replace_keyframes_block(content, 'TemplateWriteOnEnd', const_one_keyframes)
    content = replace_keyframes_block(content, 'Template_1WriteOnStart', const_zero_keyframes)
    content = replace_keyframes_block(content, 'Template_1WriteOnEnd', english_anim_keyframes)
    content = replace_keyframes_block(content, 'JPEGDamage1Quality', jpeg_damage_quality)
    content = replace_keyframes_block(content, 'JPEGDamage1Resolution', jpeg_damage_resolution)

    debug_logger.debug("Comp generation complete")
    return content
