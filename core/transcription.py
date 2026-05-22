"""WhisperX transcription worker thread."""
import json
import logging
import tempfile
import os
import sys
import time
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)
logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")
logging.getLogger('whisperx').setLevel(logging.WARNING)


class TranscriptionWorker(QThread):
    """Background worker for WhisperX transcription via python -m whisperx."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_path: str, model: str = "large", force_cpu: bool = False):
        super().__init__()
        self.audio_path = audio_path
        self.model = model
        self.force_cpu = force_cpu

    def run(self):
        """Run transcription using whisperx library directly."""
        try:
            self.progress.emit(0)

            # Ensure bundled FFmpeg is in PATH (for PyInstaller exe)
            ffmpeg_bundled = Path(sys.executable).parent / "_internal" / "ffmpeg" / "bin"
            if not ffmpeg_bundled.exists():
                ffmpeg_bundled = Path(sys.executable).parent / "ffmpeg" / "bin"

            if ffmpeg_bundled.exists():
                os.environ["PATH"] = str(ffmpeg_bundled) + os.pathsep + os.environ.get("PATH", "")

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

            self.progress.emit(10)

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

            self.progress.emit(20)

            # Output directory (use temp folder to avoid clutter)
            output_dir = Path(tempfile.gettempdir()) / "SubtitleGen_transcriptions"
            output_dir.mkdir(exist_ok=True, parents=True)

            logger.info(f"Starting transcription - Model: {self.model}, Device: {device}")

            # Import whisperx library
            import whisperx

            # Load transcription model
            try:
                debug_logger.debug(f"Loading WhisperX {self.model} model on {device}...")
                model = whisperx.load_model(self.model, device=device)
                debug_logger.debug(f"Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.error.emit(f"Failed to load model: {str(e)}")
                return

            self.progress.emit(35)
            try:
                debug_logger.debug(f"Transcribing audio: {audio_file.name}")
                result = model.transcribe(str(audio_file), batch_size=16)
                language = result.get('language', 'unknown')
                segments = result.get('segments', [])
                debug_logger.debug(f"Transcription complete: {len(segments)} segments detected")
                debug_logger.debug(f"Sample segments: {[seg.get('text', '')[:40] for seg in segments[:3]]}")
                logger.info(f"Transcription complete - Language: {language}, Segments: {len(segments)}")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                self.error.emit(f"Transcription failed: {str(e)}")
                return

            self.progress.emit(50)

            try:
                debug_logger.debug(f"Loading alignment model for language: {result.get('language', 'unknown')}")
                model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
                debug_logger.debug(f"Alignment model loaded")
            except Exception as e:
                logger.error(f"Failed to load alignment model: {e}")
                self.error.emit(f"Failed to load alignment model: {str(e)}")
                return

            self.progress.emit(90)

            try:
                debug_logger.debug(f"Aligning {len(segments)} segments to audio...")
                result = whisperx.align(result["segments"], model_a, metadata, str(audio_file), device, return_char_alignments=True)
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

            self.progress.emit(95)

            try:
                json_file = output_dir / f"{audio_file.stem}.json"
                debug_logger.debug(f"Writing transcription JSON to: {json_file}")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                debug_logger.debug(f"JSON file size: {json_file.stat().st_size} bytes")
                self.progress.emit(98)
            except Exception as e:
                logger.error(f"Failed to save JSON: {e}")
                self.error.emit(f"Failed to save JSON: {str(e)}")
                return

            if not json_file.exists():
                self.error.emit("No JSON output from WhisperX")
                return

            self.progress.emit(100)
            debug_logger.debug(f"Transcription workflow complete")
            logger.info(f"Transcription saved: {json_file}")
            self.finished.emit(str(json_file))

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            self.error.emit(f"Transcription error: {str(e)}")

    def stop(self):
        """Request worker to stop."""
        pass
