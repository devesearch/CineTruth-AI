import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytesseract
import speech_recognition as sr
from PIL import Image

from sentiment_analyzer import analyze_text_sentiment

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def _find_tesseract():
    """Return a usable Tesseract executable path, if available."""
    configured = os.getenv("TESSERACT_CMD")
    candidates = [configured, shutil.which("tesseract")]

    if os.name == "nt":
        candidates.extend([
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            str(Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe"),
        ])

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return candidate

    return None


def _find_ffmpeg():
    """Return a usable FFmpeg executable path."""
    configured = os.getenv("FFMPEG_BINARY")
    if configured and os.path.isfile(configured):
        return configured

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # pip fallback: imageio-ffmpeg ships/locates an ffmpeg binary on desktop systems.
    try:
        import imageio_ffmpeg
        executable = imageio_ffmpeg.get_ffmpeg_exe()
        if executable and os.path.isfile(executable):
            return executable
    except Exception:
        pass

    return None


def _clean_ocr_text(text):
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return "\n".join(lines).strip()


def _ocr_image_array(rgb_image):
    """Run OCR using two preprocessing passes and keep the richer result."""
    if not _find_tesseract():
        raise RuntimeError(
            "Tesseract OCR is not installed or could not be found. "
            "On Windows install Tesseract OCR, then restart Streamlit."
        )

    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)

    # Upscale smaller text for OCR.
    height, width = gray.shape[:2]
    if max(height, width) < 1800:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    denoised = cv2.GaussianBlur(gray, (3, 3), 0)
    binary = cv2.threshold(
        denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    config = "--oem 3 --psm 6"
    attempts = []
    for candidate in (gray, binary):
        try:
            attempts.append(_clean_ocr_text(
                pytesseract.image_to_string(candidate, config=config)
            ))
        except Exception:
            attempts.append("")

    return max(attempts, key=len, default="")


def analyze_image(image_bytes):
    """Extract visible text from an image and analyze its sentiment."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        rgb = np.array(image)
        extracted_text = _ocr_image_array(rgb)

        if not extracted_text:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "text": "",
                "visual_text": "",
                "audio_text": "",
                "warnings": ["No readable text was detected in the image."],
            }

        sentiment = analyze_text_sentiment(extracted_text)
        sentiment.update({
            "text": extracted_text,
            "visual_text": extracted_text,
            "audio_text": "",
            "warnings": [],
        })
        return sentiment

    except Exception as exc:
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "text": "",
            "visual_text": "",
            "audio_text": "",
            "error": f"Image text extraction failed: {exc}",
            "warnings": [],
        }


def _deduplicate_texts(items):
    unique = []
    seen = set()
    for item in items:
        cleaned = _clean_ocr_text(item)
        if not cleaned:
            continue
        key = " ".join(cleaned.lower().split())
        if key not in seen:
            seen.add(key)
            unique.append(cleaned)
    return unique


def _extract_text_from_video_frames(video_path, max_frames=12):
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        video.release()
        return "", ["OpenCV could not open the uploaded video."]

    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(video.get(cv2.CAP_PROP_FPS) or 0)

    if frame_count <= 0:
        indexes = list(range(max_frames))
    else:
        sample_count = min(max_frames, max(1, frame_count))
        indexes = np.linspace(0, max(frame_count - 1, 0), num=sample_count, dtype=int).tolist()

    extracted = []
    warnings = []

    try:
        for index in indexes:
            video.set(cv2.CAP_PROP_POS_FRAMES, int(index))
            ok, frame = video.read()
            if not ok:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                text = _ocr_image_array(rgb)
                if text:
                    extracted.append(text)
            except RuntimeError as exc:
                warnings.append(str(exc))
                break
            except Exception:
                continue
    finally:
        video.release()

    unique = _deduplicate_texts(extracted)
    if not unique and not warnings:
        warnings.append("No readable on-screen text was detected in sampled video frames.")

    return "\n".join(unique), list(dict.fromkeys(warnings))


def _extract_wav(video_path, wav_path):
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg was not found. Install FFmpeg or run `pip install imageio-ffmpeg`, "
            "then restart Streamlit."
        )

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        wav_path,
    ]
    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if process.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) <= 44:
        message = (process.stderr or "").strip()
        if "does not contain any stream" in message.lower() or "matches no streams" in message.lower():
            raise RuntimeError("The uploaded video does not contain an audio track.")
        raise RuntimeError(message or "FFmpeg could not extract audio from the video.")


def _recognize_wav(wav_path):
    recognizer = sr.Recognizer()
    texts = []

    with sr.AudioFile(wav_path) as source:
        duration = float(getattr(source, "DURATION", 0) or 0)
        # Google Speech Recognition is more reliable with moderate chunks.
        chunk_seconds = 40
        max_seconds = min(duration if duration > 0 else 300, 300)
        consumed = 0.0

        while consumed < max_seconds:
            remaining = max_seconds - consumed
            audio = recognizer.record(source, duration=min(chunk_seconds, remaining))
            consumed += min(chunk_seconds, remaining)

            if not getattr(audio, "frame_data", b""):
                break

            try:
                text = recognizer.recognize_google(audio)
                if text and text.strip():
                    texts.append(text.strip())
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                raise RuntimeError(
                    f"Speech recognition service could not be reached: {exc}"
                ) from exc

    return " ".join(texts).strip()


def extract_audio_from_video(video_path):
    """Extract speech from a video's audio track and analyze that speech."""
    wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav_path = wav_file.name
    wav_file.close()

    try:
        _extract_wav(video_path, wav_path)
        text = _recognize_wav(wav_path)

        if not text:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "text": "",
                "audio_text": "",
                "warnings": ["Audio was extracted, but no speech could be recognized."],
            }

        sentiment = analyze_text_sentiment(text)
        sentiment.update({
            "text": text,
            "audio_text": text,
            "warnings": [],
        })
        return sentiment

    except Exception as exc:
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "text": "",
            "audio_text": "",
            "error": f"Audio extraction/recognition failed: {exc}",
            "warnings": [],
        }
    finally:
        try:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        except OSError:
            pass


def analyze_video(video_path):
    """
    Extract BOTH on-screen text and spoken audio from a video, then analyze the
    combined text. Either source can still produce a result if the other fails.
    """
    visual_text, visual_warnings = _extract_text_from_video_frames(video_path)
    audio_result = extract_audio_from_video(video_path)
    audio_text = audio_result.get("audio_text", "") or ""

    warnings = list(visual_warnings)
    if audio_result.get("warnings"):
        warnings.extend(audio_result["warnings"])
    if audio_result.get("error"):
        warnings.append(audio_result["error"])

    sections = []
    if visual_text:
        sections.append(f"On-screen text:\n{visual_text}")
    if audio_text:
        sections.append(f"Spoken audio:\n{audio_text}")

    combined_for_sentiment = "\n\n".join(
        part for part in (visual_text, audio_text) if part.strip()
    ).strip()

    if not combined_for_sentiment:
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "text": "",
            "visual_text": visual_text,
            "audio_text": audio_text,
            "warnings": list(dict.fromkeys(warnings)) or [
                "No readable text or recognizable speech was detected in the video."
            ],
        }

    sentiment = analyze_text_sentiment(combined_for_sentiment)
    sentiment.update({
        "text": "\n\n".join(sections),
        "visual_text": visual_text,
        "audio_text": audio_text,
        "warnings": list(dict.fromkeys(warnings)),
    })
    return sentiment
