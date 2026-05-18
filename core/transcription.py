"""WhisperX transcription worker thread."""
import subprocess
import shutil
import logging
import os
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from core.chunks import load_whisper_json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TranscriptionWorker(QThread):
    """Background worker for WhisperX transcription."""

    progress = pyqtSignal(int)  # 0-100 progress
    finished = pyqtSignal(str)  # JSON file path on success
    error = pyqtSignal(str)     # Error message on failure

    def __init__(self, audio_path: str, model: str = "large"):
        super().__init__()
        self.audio_path = audio_path
        self.model = model
        self._is_running = True

    def run(self):
        """Run transcription in background thread."""
        try:
            logger.info("=" * 60)
            logger.info("Starting transcription worker")

            self.progress.emit(0)

            # Check if WhisperX is installed
            if not shutil.which("whisperx"):
                error_msg = "WhisperX not found. Install with: pip install openai-whisper-x"
                logger.error(error_msg)
                self.error.emit(error_msg)
                return

            self.progress.emit(15)

            # Detect device (import torch locally to avoid startup issues)
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                if device == "cuda":
                    gpu_name = torch.cuda.get_device_name(0)
                    logger.info(f"GPU DETECTED: {gpu_name}")
                else:
                    logger.info("No GPU detected, using CPU")
            except Exception as e:
                logger.warning(f"Could not detect GPU (torch issue): {e}, using CPU")
                device = "cpu"

            # Check file exists and is readable
            audio_file = Path(self.audio_path).resolve()  # Get absolute path
            logger.info(f"Transcribing: {audio_file}")

            if not audio_file.exists():
                error_msg = f"File not found: {self.audio_path}"
                logger.error(error_msg)
                self.error.emit(error_msg)
                return

            if not audio_file.is_file():
                self.error.emit(f"Not a file: {self.audio_path}")
                return

            # Check file is audio (by extension)
            audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.mov', '.avi', '.mkv'}
            if audio_file.suffix.lower() not in audio_extensions:
                self.error.emit(f"File is not audio format (has extension: {audio_file.suffix}). Supported: mp3, wav, m4a, flac, ogg, mp4, mov, avi, mkv")
                return

            # Check file is not empty
            if audio_file.stat().st_size == 0:
                self.error.emit("Audio file is empty")
                return

            self.progress.emit(20)

            # Run WhisperX
            output_dir = audio_file.parent / "transcriptions"
            output_dir.mkdir(exist_ok=True, parents=True)

            cmd = [
                "whisperx",
                str(audio_file),
                "--model", self.model,
                "--device", device,
                "--output_format", "json",
                "--output_dir", str(output_dir)
            ]

            logger.info(f"Model: {self.model}")
            logger.info(f"Device: {device}")
            logger.info("Starting WhisperX transcription...")

            self.progress.emit(30)
            logger.info("Loading model and initializing (this may take a moment)...")

            try:
                # Run whisperx with real-time output parsing
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout_lines = []
                stderr_lines = []
                current_progress = 35

                # Read output and update progress based on stages
                for line in process.stdout:
                    stdout_lines.append(line)
                    logger.info("WhisperX: " + line.strip())

                    # Update progress based on WhisperX stages
                    if "Performing transcription" in line and current_progress < 50:
                        current_progress = 50
                        self.progress.emit(current_progress)
                    elif "Performing alignment" in line and current_progress < 65:
                        current_progress = 65
                        self.progress.emit(current_progress)
                    elif "Performing diarization" in line and current_progress < 75:
                        current_progress = 75
                        self.progress.emit(current_progress)
                    elif current_progress < 45:
                        current_progress = min(45, current_progress + 1)
                        self.progress.emit(current_progress)

                # Collect stderr
                for line in process.stderr:
                    stderr_lines.append(line)

                process.wait(timeout=1800)
                result_returncode = process.returncode
                stdout_text = ''.join(stdout_lines)
                stderr_text = ''.join(stderr_lines)

            except subprocess.TimeoutExpired:
                process.kill()
                error_msg = "Transcription took too long (>30 min). Try a smaller model or shorter audio."
                logger.error(error_msg)
                self.error.emit(error_msg)
                return
            except FileNotFoundError:
                self.error.emit("WhisperX executable not found. Try reinstalling: pip install openai-whisper-x")
                return

            if result_returncode != 0:
                error_msg = stderr_text.strip().split('\n')[-1] if stderr_text else stdout_text.strip().split('\n')[-1] if stdout_text else "Unknown error"
                logger.error(f"WhisperX error: {error_msg}")
                self.error.emit(f"WhisperX error: {error_msg}")
                return

            logger.info("WhisperX transcription completed successfully")
            self.progress.emit(80)

            # Find the JSON output file
            json_files = list(output_dir.glob("*.json"))
            if not json_files:
                self.error.emit("No JSON output from WhisperX. Check console for errors.")
                return

            json_file = json_files[0]
            self.progress.emit(90)

            # Verify we can load it
            try:
                words = load_whisper_json(str(json_file))
                if not words:
                    self.error.emit("No words found in transcription")
                    return
            except Exception as e:
                self.error.emit(f"Failed to parse transcription: {str(e)}")
                return

            self.progress.emit(100)
            logger.info(f"Transcription finished! JSON saved to: {json_file}")
            logger.info("=" * 60)
            self.finished.emit(str(json_file))

        except Exception as e:
            error_msg = f"Transcription error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)

    def stop(self):
        """Request worker to stop."""
        self._is_running = False
