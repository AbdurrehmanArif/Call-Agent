"""
Audio utility functions for processing and manipulation.
"""
import io
import wave
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
from backend.utils.config import config


class AudioUtils:
    """Audio processing utilities."""

    @staticmethod
    def bytes_to_numpy(audio_bytes: bytes) -> np.ndarray:
        """
        Convert audio bytes to numpy array.

        Args:
            audio_bytes: Raw audio bytes

        Returns:
            Numpy array of audio samples
        """
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_array.astype(np.float32) / 32768.0

    @staticmethod
    def numpy_to_bytes(audio_array: np.ndarray) -> bytes:
        """
        Convert numpy array to audio bytes.

        Args:
            audio_array: Numpy array of audio samples

        Returns:
            Raw audio bytes
        """
        if audio_array.dtype == np.float32 or audio_array.dtype == np.float64:
            audio_array = (audio_array * 32767).astype(np.int16)
        return audio_array.tobytes()

    @staticmethod
    def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio to different sample rate.

        Args:
            audio: Audio array
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio array
        """
        if orig_sr == target_sr:
            return audio

        ratio = target_sr / orig_sr
        target_length = int(len(audio) * ratio)
        return np.interp(
            np.linspace(0, len(audio), target_length),
            np.arange(len(audio)),
            audio
        )

    @staticmethod
    def normalize(audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio amplitude.

        Args:
            audio: Audio array

        Returns:
            Normalized audio array
        """
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio

    @staticmethod
    def trim_silence(
        audio: np.ndarray,
        threshold: float = 0.01,
        min_length: int = 1000
    ) -> np.ndarray:
        """
        Trim silence from beginning and end of audio.

        Args:
            audio: Audio array
            threshold: Amplitude threshold for silence
            min_length: Minimum length to preserve

        Returns:
            Trimmed audio array
        """
        # Find non-silent regions
        non_silent = np.abs(audio) > threshold

        if not np.any(non_silent):
            return audio[:min_length] if len(audio) > min_length else audio

        # Find start and end
        indices = np.where(non_silent)[0]
        start = max(0, indices[0] - 100)
        end = min(len(audio), indices[-1] + 100)

        return audio[start:end]

    @staticmethod
    def pad_audio(audio: np.ndarray, target_length: int) -> np.ndarray:
        """
        Pad audio to target length.

        Args:
            audio: Audio array
            target_length: Target length

        Returns:
            Padded audio array
        """
        if len(audio) >= target_length:
            return audio[:target_length]

        padding = np.zeros(target_length - len(audio), dtype=audio.dtype)
        return np.concatenate([audio, padding])

    @staticmethod
    def create_wav_file(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
        """
        Create WAV file bytes from audio array.

        Args:
            audio: Audio array
            sample_rate: Sample rate

        Returns:
            WAV file bytes
        """
        # Convert to 16-bit PCM
        if audio.dtype == np.float32 or audio.dtype == np.float64:
            audio = (audio * 32767).astype(np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())

        return buffer.getvalue()

    @staticmethod
    def read_wav_file(file_path: str) -> Tuple[np.ndarray, int]:
        """
        Read WAV file.

        Args:
            file_path: Path to WAV file

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        with wave.open(file_path, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            n_channels = wav_file.getnchannels()
            n_frames = wav_file.getnframes()

            raw_data = wav_file.readframes(n_frames)

            if n_channels == 2:
                audio = np.frombuffer(raw_data, dtype=np.int16)
                # Convert stereo to mono
                audio = audio.reshape(-1, 2).mean(axis=1)
            else:
                audio = np.frombuffer(raw_data, dtype=np.int16)

            return audio.astype(np.float32) / 32768.0, sample_rate

    @staticmethod
    def calculate_rms(audio: np.ndarray) -> float:
        """
        Calculate RMS (Root Mean Square) of audio.

        Args:
            audio: Audio array

        Returns:
            RMS value
        """
        return np.sqrt(np.mean(audio ** 2))

    @staticmethod
    def is_silence(audio: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Check if audio is silence.

        Args:
            audio: Audio array
            threshold: Silence threshold

        Returns:
            True if audio is silence
        """
        return np.max(np.abs(audio)) < threshold


# Singleton instance
audio_utils = AudioUtils()
