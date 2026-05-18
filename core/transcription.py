"""WhisperX transcription worker thread."""
import json
import logging
import tempfile
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from core.chunks import load_whisper_json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enable whisperx logging too
logging.getLogger('whisperx').setLevel(logging.INFO)


class TranscriptionWorker(QThread):
    """Background worker for WhisperX transcription via python -m whisperx."""

    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_path: str, model: str = "large"):
        super().__init__()
        self.audio_path = audio_path
        self.model = model

    def run(self):
        """Run transcription using whisperx library directly."""
        try:
            logger.info("=" * 60)
            logger.info("Starting transcription worker")
            self.progress.emit(0)

            # Validate audio file
            audio_file = Path(self.audio_path).resolve()
            logger.info(f"Transcribing: {audio_file}")

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

            self.progress.emit(15)

            # Detect device
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                if device == "cuda":
                    gpu_name = torch.cuda.get_device_name(0)
                    logger.info(f"GPU DETECTED: {gpu_name}")
                else:
                    logger.info("No GPU detected, using CPU")
            except Exception as e:
                logger.warning(f"Could not detect GPU: {e}, using CPU")
                device = "cpu"

            self.progress.emit(20)

            # Output directory (use temp folder to avoid clutter)
            output_dir = Path(tempfile.gettempdir()) / "SubtitleGen_transcriptions"
            output_dir.mkdir(exist_ok=True, parents=True)

            logger.info(f"Model: {self.model}")
            logger.info(f"Device: {device}")
            logger.info("Loading WhisperX model...")
            self.progress.emit(25)

            # Import whisperx library
            import whisperx

            # Load transcription model
            try:
                logger.info(f"Loading {self.model} model from cache or downloading...")
                self.progress.emit(30)
                model = whisperx.load_model(self.model, device=device)
                self.progress.emit(35)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.error.emit(f"Failed to load model: {str(e)}")
                return

            logger.info("Performing transcription...")
            self.progress.emit(40)
            try:
                logger.info(f"Transcribing: {audio_file.name}")
                self.progress.emit(42)
                result = model.transcribe(str(audio_file), batch_size=16)
                self.progress.emit(48)
                logger.info(f"Transcription complete. Detected language: {result.get('language', 'unknown')}")
                segments = result.get('segments', [])
                logger.info(f"Found {len(segments)} segments")
                for i, segment in enumerate(segments, 1):
                    text = segment.get('text', '').strip()
                    start = segment.get('start', 0)
                    end = segment.get('end', 0)
                    logger.info(f"  Segment {i} [{start:.2f}s - {end:.2f}s]: {text}")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                self.error.emit(f"Transcription failed: {str(e)}")
                return

            self.progress.emit(50)

            logger.info("Loading alignment model...")
            self.progress.emit(55)
            try:
                logger.info(f"Loading alignment model for language: {result.get('language', 'unknown')}")
                self.progress.emit(58)
                model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
                self.progress.emit(62)
                logger.info("Alignment model loaded")
            except Exception as e:
                logger.error(f"Failed to load alignment model: {e}")
                self.error.emit(f"Failed to load alignment model: {str(e)}")
                return

            self.progress.emit(65)

            logger.info("Performing alignment...")
            self.progress.emit(68)
            try:
                logger.info("Aligning segments with audio...")
                result = whisperx.align(result["segments"], model_a, metadata, str(audio_file), device, return_char_alignments=True)
                self.progress.emit(78)
                logger.info("Alignment complete")

                # Log aligned words
                segments = result.get('segments', [])
                total_words = sum(len(seg.get('words', [])) for seg in segments)
                logger.info(f"Total words aligned: {total_words}")
                for i, segment in enumerate(segments, 1):
                    words = segment.get('words', [])
                    if words:
                        word_list = ' '.join(w.get('word', '') for w in words)
                        logger.info(f"  Segment {i} words: {word_list}")
            except Exception as e:
                logger.error(f"Alignment failed: {e}")
                self.error.emit(f"Alignment failed: {str(e)}")
                return

            self.progress.emit(80)

            logger.info("Saving transcription to JSON...")
            try:
                # Save result to JSON file
                json_file = output_dir / f"{audio_file.stem}.json"
                logger.info(f"Writing results to: {json_file}")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info("JSON file saved successfully")
            except Exception as e:
                logger.error(f"Failed to save JSON: {e}")
                self.error.emit(f"Failed to save JSON: {str(e)}")
                return

            self.progress.emit(90)

            # Verify JSON was created
            if not json_file.exists():
                self.error.emit("No JSON output from WhisperX")
                return

            self.progress.emit(100)
            logger.info(f"Transcription complete: {json_file}")
            logger.info("=" * 60)
            self.finished.emit(str(json_file))

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            self.error.emit(f"Transcription error: {str(e)}")

    def stop(self):
        """Request worker to stop."""
        pass
