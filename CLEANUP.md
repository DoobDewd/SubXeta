# Code Cleanup Checklist

Specific cleanup items found in codebase. Use before v1.1.

## Imports

- [ ] **Remove duplicate import** — `ui/main_window.py:15`
  - `from pathlib import Path` imported twice (line 2 and line 15)
  - Keep line 2, delete line 15

- [ ] **Remove unused import** — `core/transcription.py:7`
  - `import time` is never used
  - Delete the line

## Debug Code

- [ ] **Set DEBUG flag to False** — `main.py:26`
  - Currently `DEBUG = True` with comment "Enable debug logging (comment out for production)"
  - Set to `False` or wrap in environment variable check

- [ ] **Remove print statements** — `core/subtitle_gen.py:440, 445, 454`
  - Three `print()` statements in the `main()` function
  - Replace with logging calls or remove if this code path isn't maintained

## Code Complexity

- [ ] **Extract helper function** — `core/chunks.py:236`
  - `rebuild_chunks_with_edits()` is 118 lines, nested 4 levels deep
  - Extract word mapping + timing split logic (lines 286-344) into `_apply_word_mapping_to_line()`

- [ ] **Extract helper function** — `core/chunks.py:147`
  - `_map_edited_words_to_original()` is 87 lines
  - Extract fallback mapping logic (lines 193-215) into `_map_extra_edited_words()`

- [ ] **Split large function** — `core/subtitle_gen.py:321`
  - `generate_single_comp()` is 103 lines doing multiple tasks
  - Extract keyframe generation into `_generate_all_keyframes()`
  - Extract spline creation into `_create_spline_objects()`

## Potential Bugs

- [ ] **Check duplicate replacements** — `core/subtitle_gen.py:363-371`
  - Two identical `content.replace()` calls with same search string but different replacements
  - Verify this is intentional or fix copy-paste error
  - Both should probably target different parts of template

## Code Clarity

- [ ] **Add comments** — `ui/main_window.py:273, 281`
  - `self._fade_in_anim` and `self._fade_out_anim` stored as instance variables
  - Add comment explaining they're stored to keep reference alive for QPropertyAnimation

## Notes

- **Not blocking ship** — All items are cleanup/refactoring, no functionality changes
- **Estimated effort** — 1-2 hours to complete all items
- **Priority** — Start with imports + debug code (quick wins), then tackle complexity if time permits
