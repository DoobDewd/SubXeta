"""WhisperX transcription worker thread."""
import json
import logging
import tempfile
import os
import sys
import time
from pathlib import Path
from enum import Enum
from PyQt6.QtCore import QThread, pyqtSignal

# Patch tqdm BEFORE any HuggingFace imports to intercept all progress bars
import tqdm as tqdm_module
import tqdm.auto as tqdm_auto
_original_tqdm = tqdm_module.tqdm
_active_worker = None
_preparing_completed = False

class _ProgressEmittingTqdm(_original_tqdm):
    """Custom tqdm that emits Qt signals for real-time download progress."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stage = None
        self._last_emitted_for_stage = -1

    def update(self, n=1):
        super().update(n)
        if self.total and self.total > 0 and _active_worker:
            # Determine stage on first update (based on filename/size)
            if self._stage is None:
                global _preparing_completed

                # First download has started, complete PREPARING if not already done
                if not _preparing_completed:
                    _active_worker.progress.emit(TranscriptionStage.PREPARING.value, 100)
                    _preparing_completed = True

                # Check filename in tqdm description
                if self.desc:
                    desc_str = str(self.desc).lower()
                    if 'model.bin' in desc_str:
                        self._stage = TranscriptionStage.DOWNLOADING.value
                    elif 'wav2vec' in desc_str or '.pth' in desc_str:
                        self._stage = TranscriptionStage.DOWNLOADING_ALIGNMENT.value
                    else:
                        self._stage = TranscriptionStage.DOWNLOADING_METADATA.value
                # Fallback to file size if no description
                elif self.total > 500_000_000:  # 500MB threshold
                    self._stage = TranscriptionStage.DOWNLOADING.value
                elif 100_000_000 < self.total <= 500_000_000:  # 100MB-500MB range (alignment models)
                    self._stage = TranscriptionStage.DOWNLOADING_ALIGNMENT.value
                else:
                    self._stage = TranscriptionStage.DOWNLOADING_METADATA.value

                # Emit initial 0% for this stage
                _active_worker.progress.emit(self._stage, 0)
                self._last_emitted_for_stage = 0

            percentage = int((self.n / self.total) * 100)
            # Only emit if percentage actually changed (avoid excessive updates)
            if percentage != self._last_emitted_for_stage:
                self._last_emitted_for_stage = percentage
                _active_worker.progress.emit(self._stage, percentage)

# Patch all tqdm variants
tqdm_module.tqdm = _ProgressEmittingTqdm
tqdm_auto.tqdm = _ProgressEmittingTqdm
if hasattr(tqdm_module, 'std'):
    tqdm_module.std.tqdm = _ProgressEmittingTqdm

# Progress stages for transcription workflow
class TranscriptionStage(Enum):
    PREPARING = "Preparing"
    DOWNLOADING_METADATA = "Downloading metadata"
    DOWNLOADING = "Downloading model"
    LOADING = "Loading model"
    TRANSCRIBING = "Transcribing audio"
    DOWNLOADING_ALIGNMENT = "Downloading alignment model"
    ALIGNING = "Aligning words"
    SAVING = "Saving results"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)
logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")
logging.getLogger('whisperx').setLevel(logging.WARNING)


class TranscriptionWorker(QThread):
    """Background worker for WhisperX transcription via python -m whisperx."""

    progress = pyqtSignal(str, int)  # stage_name (str), percentage (int 0-100)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_path: str, model: str = "large", force_cpu: bool = False):
        super().__init__()
        self.audio_path = audio_path
        self.model = model
        self.force_cpu = force_cpu

    def run(self):
        """Run transcription using whisperx library directly."""
        global _active_worker, _preparing_completed
        try:
            # Reset state for this transcription run
            _active_worker = self
            _preparing_completed = False
            self.progress.emit(TranscriptionStage.PREPARING.value, 0)

            # Ensure bundled FFmpeg is in PATH (for PyInstaller exe)
            ffmpeg_bundled = Path(sys.executable).parent / "_internal" / "ffmpeg" / "bin"
            if not ffmpeg_bundled.exists():
                ffmpeg_bundled = Path(sys.executable).parent / "ffmpeg" / "bin"

            if ffmpeg_bundled.exists():
                os.environ["PATH"] = str(ffmpeg_bundled) + os.pathsep + os.environ.get("PATH", "")

            self.progress.emit(TranscriptionStage.PREPARING.value, 12)

            # Validate audio file
            audio_file = Path(self.audio_path).resolve()

            if not audio_file.exists():
                self.error.emit(f"File not found: {self.audio_path}")
                return

            audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.mov', '.avi', '.mkv'}
            if audio_file.suffix.lower() not in audio_extensions:
                self.error.emit(f"Unsupported file format: {audio_file.suffix}")
                return

            if audio_file.stat().st_size == 0:
                self.error.emit("Audio file is empty")
                return

            self.progress.emit(TranscriptionStage.PREPARING.value, 25)

            # Detect device
            try:
                import torch
                if self.force_cpu:
                    device = "cpu"
                    logger.info("Forcing CPU mode per user settings")
                else:
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    if device == "cuda":
                        gpu_name = torch.cuda.get_device_name(0)
                        logger.info(f"GPU detected: {gpu_name}")
                    else:
                        logger.info("Using CPU for transcription")
            except Exception as e:
                logger.warning(f"Could not detect GPU: {e}, using CPU")
                device = "cpu"

            self.progress.emit(TranscriptionStage.PREPARING.value, 40)

            # Output directory (use temp folder to avoid clutter)
            output_dir = Path(tempfile.gettempdir()) / "SubXeta_transcriptions"
            output_dir.mkdir(exist_ok=True, parents=True)

            self.progress.emit(TranscriptionStage.PREPARING.value, 55)

            logger.info(f"Starting transcription - Model: {self.model}, Device: {device}")

            self.progress.emit(TranscriptionStage.PREPARING.value, 70)

            # Import whisperx library
            import whisperx

            self.progress.emit(TranscriptionStage.PREPARING.value, 85)

            # Load transcription model (with automatic retry on lock/permission errors)
            # tqdm will emit PREPARING: 100 when first download starts, then DOWNLOADING_METADATA and DOWNLOADING stages
            model = None
            for attempt in range(2):
                try:
                    debug_logger.debug(f"Loading WhisperX {self.model} model on {device}..." + (f" (attempt {attempt + 1}/2)" if attempt > 0 else ""))
                    model = whisperx.load_model(self.model, device=device)
                    debug_logger.debug(f"Model loaded successfully")
                    self.progress.emit(TranscriptionStage.LOADING.value, 100)
                    break
                except (OSError, PermissionError) as e:
                    if attempt == 0 and ("WinError 1314" in str(e) or "required privilege" in str(e) or "lock" in str(e).lower()):
                        debug_logger.debug(f"Cache lock/permission issue, retrying immediately...")
                        continue
                    logger.error(f"Failed to load model: {e}")
                    self.error.emit(f"Failed to load model: {str(e)}")
                    return
                except Exception as e:
                    logger.error(f"Failed to load model: {e}")
                    self.error.emit(f"Failed to load model: {str(e)}")
                    return

            if model is None:
                logger.error("Failed to load model after retries")
                self.error.emit("Failed to load model after retries")
                return

            self.progress.emit(TranscriptionStage.TRANSCRIBING.value, 0)
            transcribe_last_emit = [0, time.time()]  # [percentage, timestamp]

            try:
                debug_logger.debug(f"Transcribing audio: {audio_file.name}")

                def transcribe_progress(progress_pct):
                    """Callback for transcription progress (0-100), throttled by time and percentage."""
                    pct_int = int(progress_pct)
                    now = time.time()
                    time_since_last = (now - transcribe_last_emit[1]) * 1000  # Convert to ms

                    # Emit if: (1) at least 200ms passed, or (2) reached 100%, or (3) percentage changed by 10%+
                    if time_since_last >= 200 or pct_int == 100 or pct_int >= transcribe_last_emit[0] + 10:
                        transcribe_last_emit[0] = pct_int
                        transcribe_last_emit[1] = now
                        self.progress.emit(TranscriptionStage.TRANSCRIBING.value, pct_int)

                result = model.transcribe(str(audio_file), batch_size=16, progress_callback=transcribe_progress)
                language = result.get('language', 'unknown')
                segments = result.get('segments', [])
                debug_logger.debug(f"Transcription complete: {len(segments)} segments detected")
                debug_logger.debug(f"Sample segments: {[seg.get('text', '')[:40] for seg in segments[:3]]}")
                logger.info(f"Transcription complete - Language: {language}, Segments: {len(segments)}")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                self.error.emit(f"Transcription failed: {str(e)}")
                return

            self.progress.emit(TranscriptionStage.TRANSCRIBING.value, 100)

            self.progress.emit(TranscriptionStage.DOWNLOADING_ALIGNMENT.value, 0)
            try:
                debug_logger.debug(f"Loading alignment model for language: {result.get('language', 'unknown')}")
                model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
                debug_logger.debug(f"Alignment model loaded")
            except Exception as e:
                logger.error(f"Failed to load alignment model: {e}")
                self.error.emit(f"Failed to load alignment model: {str(e)}")
                return

            # Alignment model is now loaded, start aligning
            self.progress.emit(TranscriptionStage.ALIGNING.value, 0)
            align_last_emit = [0, time.time()]  # [percentage, timestamp]

            try:
                debug_logger.debug(f"Aligning {len(segments)} segments to audio...")

                def align_progress(progress_pct):
                    """Callback for alignment progress (0-100), throttled by time and percentage."""
                    pct_int = int(progress_pct)
                    now = time.time()
                    time_since_last = (now - align_last_emit[1]) * 1000  # Convert to ms

                    # Emit if: (1) at least 200ms passed, or (2) reached 100%, or (3) percentage changed by 10%+
                    if time_since_last >= 200 or pct_int == 100 or pct_int >= align_last_emit[0] + 10:
                        align_last_emit[0] = pct_int
                        align_last_emit[1] = now
                        self.progress.emit(TranscriptionStage.ALIGNING.value, pct_int)

                result = whisperx.align(result["segments"], model_a, metadata, str(audio_file), device, return_char_alignments=True, progress_callback=align_progress)
                segments = result.get('segments', [])
                total_words = sum(len(seg.get('words', [])) for seg in segments)
                debug_logger.debug(f"Alignment complete: {total_words} words aligned across {len(segments)} segments")
                if total_words > 0:
                    words_per_seg = total_words / len(segments)
                    debug_logger.debug(f"Average: {words_per_seg:.1f} words/segment")
                logger.info(f"Alignment complete - Words: {total_words}")
            except Exception as e:
                logger.error(f"Alignment failed: {e}")
                self.error.emit(f"Alignment failed: {str(e)}")
                return

            self.progress.emit(TranscriptionStage.ALIGNING.value, 100)

            self.progress.emit(TranscriptionStage.SAVING.value, 0)
            try:
                json_file = output_dir / f"{audio_file.stem}.json"
                debug_logger.debug(f"Writing transcription JSON to: {json_file}")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                debug_logger.debug(f"JSON file size: {json_file.stat().st_size} bytes")
                self.progress.emit(TranscriptionStage.SAVING.value, 100)
            except Exception as e:
                logger.error(f"Failed to save JSON: {e}")
                self.error.emit(f"Failed to save JSON: {str(e)}")
                return

            if not json_file.exists():
                self.error.emit("No JSON output from WhisperX")
                return

            # Final completion signal - same stage, 100%
            debug_logger.debug(f"Transcription workflow complete")
            logger.info(f"Transcription saved: {json_file}")
            self.finished.emit(str(json_file))

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            self.error.emit(f"Transcription error: {str(e)}")
