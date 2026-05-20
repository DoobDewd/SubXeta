# Subtitle Generator App - Build Plan

## Project Overview
Standalone desktop GUI application that wraps WhisperX transcription and the subtitle comp generator into one user-friendly tool. Target user: non-technical video editor.

## Tech Stack
- **GUI Framework**: PyQt6
- **Transcription**: WhisperX (bundled with exe)
- **Comp Generation**: subtitle_gen.py (integrated)
- **Packaging**: PyInstaller one-dir mode (~85 MB exe + dependencies folder)

## Design Direction
**Alien/Sci-Fi Theme**
- Dark background (#1a1a1a) with neon green (#00ff88 / #00ffaa) accents
- CRT scanline effects on cards and import hover
- Smooth micro-animations (typing, fade, slide)
- Fits the "alien to English translation" concept

## App Workflow (User Perspective)
1. Open app
2. Select audio/video file (drag & drop or file browser)
3. Click "Start Transcription" → see progress bar
4. WhisperX generates JSON
5. Review & edit subtitle chunks in editable cards (text + timestamps)
6. Click "Generate Comp" → see progress
7. .comp file saved to `subs/` folder
8. Import .comp into DaVinci Resolve

---

## Architecture (Layered)

```
main.py                        ← entry point only
ui/
  main_window.py               ← MainWindow class
  tab_bar.py                   ← custom tab bar with animations
  styles.py                    ← global dark theme stylesheet
  widgets.py                   ← DragDropArea, CRTEffect, ParticleOverlay
  steps/
    step1_transcribe.py        ← Step 1 widget
    step2_review.py            ← Step 2 widget + ChunkCard
core/
  transcription.py             ← WhisperX QThread worker
  chunks.py                    ← group_into_chunks(), chunk_to_texts()
  subtitle_gen.py              ← comp generation (moved from root)
  models.py                    ← Word, Chunk dataclasses
```

**Rules:**
- `ui/` never imports from `core/` except `models.py`
- `core/` has no PyQt6 imports except QThread/QObject/pyqtSignal for workers
- Workers communicate to UI via signals only

---

## Implementation Phases

### Phase 1 — UI Framework ✅ Complete
- [x] PyQt6 app with dark alien theme
- [x] Top tab navigation with sliding underline + typing animations, step gating
- [x] Step 1: drag-drop / click-to-browse audio file import
- [x] Step 2: editable chunk cards with timestamps
- [x] CRT scanline effect on chunk cards (animated)
- [x] CRT hover effect on import box
- [x] Fade transitions between steps
- [x] Generate Comp button with progress bar placeholder

### Phase 2 — Code Refactor ✅ Complete
- [x] Create `core/models.py` (Word, Chunk dataclasses)
- [x] Create `core/chunks.py` (move chunk logic from subtitle_gen.py)
- [x] Move `subtitle_gen.py` → `core/subtitle_gen.py`
- [x] Extract `core/transcription.py` (WhisperX QThread worker)
- [x] Update all imports
- [x] Minimal `requirements.txt` (PyQt6 + whisperx only)

### Phase 3 — Backend Integration ✅ Complete
- [x] `core/transcription.py` — WhisperX QThread worker with progress signals + cache logging
- [x] Wire Step 1 transcribe button → worker → populate Step 2 cards
- [x] Wire Step 2 Generate button → comp generation with chunk editing support
- [x] Chunk editing: users can modify text in cards before generation
- [x] Smart word mapping: handles insertions/deletions via SequenceMatcher
- [x] Timestamp preservation: maps edited words back to original timings with proportional split
- [x] **Replacement/insertion split timing:** Multiple edits to same original split time proportionally (replacements + insertions both supported)
- [x] Chunk reconstruction refactored to `core/chunks.py` (consolidate editing logic)
- [x] Error handling (bad file, WhisperX not installed, failed transcription)
- [x] Auto GPU detection (CUDA/CPU) with detailed logging
- [x] File validation (format, size, existence)
- [x] Cross-PC compatibility: bundled FFmpeg with automatic PATH detection
- [x] Tested: transcription ~30s on RTX 3060 Ti, works on PCs without FFmpeg

### Phase 4 — Polish, Logging & Optimization
- [x] **Sparse Keyframing Optimization** ✅ Complete
  - [x] Switch from every-frame to character-based keyframing
  - [x] Generate keyframes only when characters are revealed (not every frame)
  - [x] Same visual output, ~50% fewer animation keyframes (1 keyframe per character)
  - [x] Simplify hold phase: 2 boundary keyframes instead of per-frame hold loop
  - [x] Testing verified: 1329 → 633 animation keyframes on 55s video
- [ ] Splash screen: show on startup (before main window loads)
- [ ] Particle effects: subtle floating green dots in background
- [ ] Settings panel: fps, max-chars, pause-threshold, model selector
- [x] Output path picker — SaveFileDialog lets user choose location and filename
- [ ] "Open folder" button after generation
- [x] **Logging Refactor — Industry Standard** ✅ Complete
  - [x] Remove debug/verbose logging cluttering output
  - [x] Standardize format: `%(asctime)s - %(levelname)s - %(module)s - %(message)s`
  - [x] Core logging levels: `INFO` (milestones), `ERROR` (failures), no DEBUG spam
  - [x] `core/transcription.py`: keep model loading, GPU detection, errors only
  - [x] `ui/main_window.py`: keep file selection, generation status, errors only
  - [x] Remove: cache directory enumeration, individual segment logs, progress spam
  - [x] Add: single-line summary for transcription start/complete
  - [x] No file logging (temp only, cleared on restart)

### Phase 5 — Packaging & Installer ✅ In Progress
**System Requirements:**
- Windows 10/11
- 10 GB free disk space (for models on first run)
- GPU support: NVIDIA driver (optional — CPU-only mode works fine, just slower)

**What's Bundled:**
- Python 3.13 runtime (via PyInstaller)
- PyQt6, WhisperX, PyTorch, TorchAudio
- FFmpeg binaries (in `_internal\ffmpeg\bin\` for audio loading)
- All dependencies auto-detected and bundled

**Current Status:**
- [x] PyInstaller spec file (`subtitle_comp_app.spec`) created with:
  - One-dir mode (faster startup than one-file)
  - FFmpeg bundled and auto-discovered at runtime
  - All whisperx/torch/transformers dependencies included
  - Model selection: large (default), base, small available
- [x] Exe built and tested on multiple PCs
- [x] Cross-PC compatibility verified (FFmpeg auto-detection works)
- [x] Cache logging integrated for uninstall documentation

**Next Steps (for Inno Setup installer):**
1. Create `.iss` script for Windows installer with:
   - Optional cache cleanup on uninstall checkbox
   - Desktop shortcut + Start Menu entry
   - Information about NVIDIA driver for GPU mode (optional)
2. Package installer (~400MB exe, expands to ~2GB on install)
3. Test on clean Windows VM
4. Document first-run cache download (~8.4 GB)

**Build Process:**
```bash
# Rebuild exe if code changes
cd F:\Projects\DD sub
.\venv\Scripts\Activate.ps1
python -m PyInstaller subtitle_comp_app.spec --noconfirm

# Output in: dist\SubtitleGen\
```

**Pre-Release Validation Checklist:**

**GUI & Navigation**
- [ ] App launches without errors
- [ ] Startup time < 5 seconds (development), < 15 seconds (exe)
- [ ] Tab navigation works (Step 1 → Step 2 → Step 1)
- [ ] Fade transitions smooth
- [ ] Step 2 disabled until transcription complete
- [ ] Text typing animation plays correctly

**File Import**
- [ ] Drag & drop audio file works
- [ ] Click-to-browse file picker works
- [ ] Accepts MP4, MOV, MP3, WAV formats
- [ ] Rejects unsupported formats with error
- [ ] Rejects non-existent files with error
- [ ] Validates file size > 0 bytes

**Transcription**
- [ ] Progress bar advances smoothly
- [ ] Model loads (GPU or CPU detected correctly)
- [ ] Transcription completes for 1 min video in < 2 min (GPU) / < 5 min (CPU)
- [ ] JSON output created in temp directory
- [ ] Detected language shown in logs
- [ ] Word-level alignment completes without errors

**Chunk Review & Editing**
- [ ] Chunks populated with correct text
- [ ] Multi-line text displays correctly (\\n converted to actual newlines)
- [ ] Editable text fields accept input
- [ ] Original chunks unedited preserve timing
- [ ] Edited chunks reconstruct with proper word mapping
- [ ] Special characters (quotes, apostrophes) handled correctly
- [ ] Adding words to chunk splits timing proportionally
- [ ] Removing words from chunk merges timing correctly

**Comp Generation**
- [ ] Generate button enabled only after transcription
- [ ] Comp generation completes without errors
- [ ] Generated .comp file valid (can import to DaVinci Resolve)
- [ ] Alien text keyframes at correct times
- [ ] English text keyframes at correct times
- [ ] Text overlaps correctly in template (check horizontal & vertical resolutions)
- [ ] Render range updated to match audio duration
- [ ] Success message displays with filename

**Cross-Platform Testing**
- [ ] Runs on Windows 10 (tested)
- [ ] Runs on Windows 11 (tested)
- [ ] Works without NVIDIA GPU (CPU mode)
- [ ] Works with NVIDIA GPU (if CUDA driver present)
- [ ] FFmpeg bundled version found and used (no system FFmpeg required)

**Cache Management**
- [ ] Models downloaded to `~/.cache/huggingface/` (~5GB)
- [ ] PyTorch cache created in `~/.cache/torch/` (~360MB)
- [ ] Whisper cache in `~/.cache/whisper/` (~3GB)
- [ ] Temp JSON files auto-deleted after comp generation
- [ ] Cache paths logged at startup

**Error Handling**
- [ ] Transcription failure shows user-friendly error
- [ ] Model loading failure shows user-friendly error
- [ ] File not found shows user-friendly error
- [ ] Comp generation failure shows user-friendly error
- [ ] App doesn't crash on edge cases
- [ ] Invalid chunk text handled gracefully

**Installer Testing** (After Inno Setup)
- [ ] Installer downloads/installs cleanly
- [ ] Desktop shortcut created and works
- [ ] Start Menu entry created
- [ ] App launches from Start Menu
- [ ] Uninstall removes app folder
- [ ] Optional: uninstall prompt to delete cache offers checkbox
- [ ] Uninstall removes shortcuts

---

## Key Technical Details

### Background Processing
- WhisperX transcription runs in QThread worker — never blocks UI
- Worker emits `progress(int)` and `finished(str)` signals
- UI connects signals to progress bar and step navigation

### Template System
- Template: `Montserrat to Zeta Reticuli Template.comp`
- Node names must match exactly: `Template`, `Template_1`, `TemplateWriteOnStart`, `TemplateWriteOnEnd`, `Template_1WriteOnStart`, `Template_1WriteOnEnd`
- **Resolution-responsive positioning:** TextPlus node centers use dynamic expressions:
  - Alien (Template): `{ 0.5, 0.5 - 0.0212 * self.Width / self.Height }`
  - English (Template_1): `{ 0.5, 0.5 + 0.0107 * self.Width / self.Height }`
  - These ensure text overlaps correctly at any aspect ratio (landscape/portrait)
- Multiple templates supported — duplicate and change fonts/colors, keep node names

### Chunk Editing System
- Users can edit subtitle text in Step 2 before generation
- **Smart reconstruction:** Edited chunks are re-mapped to original word timings
- **Word alignment:** SequenceMatcher intelligently handles insertions/deletions
- **Split timing:** When edited chunk has more words than original, timing is split proportionally
- **Unedited chunks:** Chunks not modified use original structure as-is (no reconstruction)
- **Flags tracking:** System tracks which chunks were actually edited to minimize reconstruction

### Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| fps | 24 | Frame rate of output comp |
| max-chars | 20 | Max characters per line (in chunks) |
| pause-threshold | 0.3s | Gap to create chunk break |
| frame-offset | 1 | Frames alien starts before English |

---

## Cache Directories (For Installer/Uninstall)

**What gets cached:** WhisperX/Whisper transcription models and PyTorch weights are downloaded on first run to user's cache directory.

**Total download on first use:** ~8.4 GB

**Cache locations (Windows):**

| Directory | Size | Contents |
|-----------|------|----------|
| `C:\Users\[user]\.cache\huggingface\` | 5086.6 MB | Whisper + alignment models |
| `C:\Users\[user]\.cache\whisper\` | 3000.2 MB | Additional Whisper model cache |
| `C:\Users\[user]\.cache\torch\` | 360.2 MB | PyTorch/TorchAudio weights |
| `C:\Users\[user]\.pyannote\` | varies | Speaker detection model (optional, created if diarization used) |
| `%TEMP%\SubtitleGen_transcriptions\` | — | Temporary JSON files (auto-deleted by app after comp generation) |

**Installer Recommendations:**
1. **Uninstall cleanup:** Offer optional checkbox: "Delete cached models on uninstall?" (allow users to keep if they want to avoid re-downloading)
2. **First-run warning:** Notify user that ~8.4 GB will be downloaded on first transcription
3. **Storage requirement:** Document at least 10 GB free space recommended
4. **Model sharing:** Note that `~/.cache/huggingface/` and `~/.cache/torch/` are shared by other ML applications — only delete if user confirms

**Development note:** Cache logging is built into `core/transcription.py` — runs automatically and reports all cache paths/sizes on startup for documentation purposes.
