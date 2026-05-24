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
- [x] **Settings Panel** ✅ Complete (partial)
  - [x] Transcription model selector (base, small, medium, large)
  - [x] Processing mode selector (GPU, CPU with force_cpu option)
  - [x] Settings persist per session, apply immediately to next transcription
  - [ ] Future: fps, max-chars, pause-threshold settings (lower priority)
- [x] **Progress Bar Improvements** ✅ Complete
  - [x] Workflow-mapped checkpoints (0%, 10%, 20%, 35%, 50%, 90%, 95%, 98%, 100%)
  - [x] Smooth animation (250ms, OutCubic easing) between progress updates
  - [x] Brighter shimmer effect (alpha 125) for better visibility
  - [x] Fixed rapid-completion blinking by spreading final phases
- [x] **Chunk Generation Bug Fix** ✅ Complete
  - [x] Fixed: Generate Comp clicked before typing animation completion resulted in fewer chunks
  - [x] Solution: Store full chunk texts separately as fallback when widgets empty
- [x] **JSON Cleanup** ✅ Complete
  - [x] Moved from after comp generation to app closeEvent
  - [x] Temp JSON files now persist for session, clean up on exit
- [x] Output path picker — SaveFileDialog lets user choose location and filename
- [x] **Splash screen: show on startup (before main window loads)** ✅ Complete
- [x] **Console disabled fix** ✅ Complete
  - [x] Fixed app hanging when running PyInstaller exe without console window
  - [x] Added NullWriter to safely redirect stdout/stderr when None
  - [x] WhisperX and all dependencies now work correctly with console disabled
  - [x] Transcription completes and properly transitions to step 2
- [ ] Particle effects: subtle floating green dots in background
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

### Phase 5 — Packaging & Installer ✅ Complete
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
- [x] **Console-disabled fix:** Exe runs without console window (NullWriter prevents crashes from stdout/stderr being None)
- [x] Exe fully functional: transcription → chunk review → comp generation all work headless

**Optional Enhancements:**
1. (Optional) Code-sign exe to eliminate SmartScreen warnings on first run
2. (Optional) Test on clean Windows VM to verify fresh install experience
3. (Optional) GitHub Releases distribution (for better SmartScreen reputation)

**Build Process:**
```bash
# Rebuild exe if code changes
cd F:\Projects\DD sub
.\venv\Scripts\Activate.ps1
python -m PyInstaller subtitle_comp_app.spec --noconfirm

# Output in: dist\SubtitleGen\
```

### Phase 6 — Future: Template Extensibility (Planned)

**Overview:** Support for additional animation template types beyond the alien-to-English reveal.

**Architecture:** Each unique animation type requires its own subtitle generation module:
- **`core/subtitle_gen_alien.py`** — Alien-to-English translation reveal (current)
- **`core/subtitle_gen_[type].py`** — Future: Each distinct animation type (e.g., fade, typewriter, highlight, dissolve) gets dedicated generator

**Why Separate Modules:**
- Different animation types have fundamentally different keyframe generation logic
- Timing calculations specific to each animation style
- Node names and transform parameters vary per template type
- Clean separation of concerns

**Adding New Template Types:**
1. Create new template file(s) in `templates/My Animation Type.comp`
2. Create `core/subtitle_gen_my_animation.py` with:
   - `generate_single_comp()` function (matches existing signature)
   - Template-specific keyframe logic
   - Animation timing calculations
3. Update UI settings to allow selecting the template type
4. Automatically discovers template .comp files in `templates/` folder (no spec updates needed)

---

**Pre-Release Validation Checklist:**

**GUI & Navigation**
- [x] App launches without errors
- [x] Startup time < 5 seconds (development), < 15 seconds (exe)
- [x] Tab navigation works (Step 1 → Step 2 → Step 1)
- [x] Fade transitions smooth
- [x] Step 2 disabled until transcription complete
- [x] Text typing animation plays correctly
- [x] **Console disabled:** App works correctly when exe run without console window (transcription completes, transitions to step 2)

**File Import**
- [x] Drag & drop audio file works
- [x] Click-to-browse file picker works
- [x] Accepts MP4, MOV, MP3, WAV formats
- [x] Rejects unsupported formats with error
- [x] Rejects non-existent files with error
- [x] Validates file size > 0 bytes

**Transcription**
- [x] Progress bar advances smoothly
- [x] Model loads (GPU or CPU detected correctly)
- [x] Transcription completes for 1 min video in < 2 min (GPU) / < 5 min (CPU)
- [x] JSON output created in temp directory
- [x] Detected language shown in logs
- [x] Word-level alignment completes without errors

**Chunk Review & Editing**
- [x] Chunks populated with correct text
- [x] Multi-line text displays correctly (\\n converted to actual newlines)
- [x] Editable text fields accept input
- [x] Original chunks unedited preserve timing
- [x] Edited chunks reconstruct with proper word mapping
- [x] Special characters (quotes, apostrophes) handled correctly
- [x] Adding words to chunk splits timing proportionally
- [x] Removing words from chunk merges timing correctly

**Comp Generation**
- [x] Generate button enabled only after transcription
- [x] Comp generation completes without errors
- [x] Generated .comp file valid (can import to DaVinci Resolve)
- [x] Alien text keyframes at correct times
- [x] English text keyframes at correct times
- [x] Text overlaps correctly in template (check horizontal & vertical resolutions)
- [x] Render range updated to match audio duration
- [x] Success message displays with filename

**Cross-Platform Testing**
- [x] Runs on Windows 10 (tested)
- [x] Runs on Windows 11 (tested)
- [x] Works without NVIDIA GPU (CPU mode)
- [x] Works with NVIDIA GPU (if CUDA driver present - RTX 3060 Ti verified)
- [x] FFmpeg bundled version found and used (no system FFmpeg required)

**Cache Management**
- [x] Models downloaded to `~/.cache/huggingface/` (~5GB)
- [x] PyTorch cache created in `~/.cache/torch/` (~360MB)
- [x] Whisper cache in `~/.cache/whisper/` (~3GB)
- [x] Temp JSON files auto-deleted after comp generation
- [x] Cache paths logged at startup

**Error Handling**
- [x] Transcription failure shows user-friendly error
- [x] Model loading failure shows user-friendly error
- [x] File not found shows user-friendly error
- [x] Comp generation failure shows user-friendly error
- [x] App doesn't crash on edge cases
- [x] Invalid chunk text handled gracefully

**Installer Testing** (After Inno Setup)
- [x] Installer downloads/installs cleanly (1.98 GB, under GitHub 2GB limit)
- [x] Desktop shortcut created and works
- [x] Start Menu entry created
- [x] App launches from Start Menu
- [x] Uninstall removes app folder
- [x] Optional: uninstall prompt to delete cache offers checkbox
- [x] Uninstall removes shortcuts

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

---

## Known Issues / To-Do

- [ ] Fix template filename typo: rename `Monsterrat to Galictico.comp` → `Montserrat to Galictico.comp`
