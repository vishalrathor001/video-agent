import whisper
import os
import requests
from pydub import AudioSegment

# Sarvam sync API rejects audio longer than 30 seconds.
SARVAM_PIECE_SECONDS = 25

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


class LanguageMismatchError(RuntimeError):
    """Raised when selected language does not match detected video language."""

    def __init__(self, selected_language, detected_language):
        self.selected_language = selected_language
        self.detected_language = detected_language

        if selected_language == "english":
            message = (
                f"Language mismatch detected. You selected English, "
                f"but the video appears to be {detected_language}. "
                f"Please select Hinglish/Hindi for this video."
            )
        else:
            message = (
                f"Language mismatch detected. You selected Hinglish/Hindi, "
                f"but the video appears to be {detected_language}. "
                f"Please select English for this video."
            )

        super().__init__(message)


def load_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")

    return _model


def detect_chunk_language(chunk_path: str):
    """
    Detect the dominant language of an audio chunk using Whisper.

    Returns:
        language_code: e.g. 'en', 'hi'
        confidence: probability of the detected language
    """

    model = load_model()

    # Load audio
    audio = whisper.load_audio(chunk_path)

    # Use the first ~30 seconds for language detection
    audio = whisper.pad_or_trim(audio)

    # Convert audio to log-Mel spectrogram
    mel = whisper.log_mel_spectrogram(
        audio,
        n_mels=model.dims.n_mels
    ).to(model.device)

    # Detect language
    _, probabilities = model.detect_language(mel)

    detected_language = max(
        probabilities,
        key=probabilities.get
    )

    confidence = probabilities[detected_language]

    return detected_language, confidence


def detect_video_language(chunks: list):
    """
    Detect language from one or more transcript chunks.

    For better reliability, the first few chunks are checked.

    Hindi detected in any sampled chunk -> Hinglish/Hindi.
    Otherwise English is used if English is dominant.
    """

    if not chunks:
        raise RuntimeError("No audio chunks available for language detection.")

    # Check at most first 3 chunks.
    sample_chunks = chunks[:3]

    detections = []

    print("\nDetecting video language...")

    for i, chunk in enumerate(sample_chunks):
        language, confidence = detect_chunk_language(chunk)

        print(
            f"  Chunk {i + 1}: "
            f"{language} "
            f"(confidence: {confidence:.2f})"
        )

        detections.append((language, confidence))

    # If Hindi is confidently detected in any sampled chunk,
    # treat the video as Hindi/Hinglish.
    hindi_detected = any(
        language == "hi" and confidence >= 0.50
        for language, confidence in detections
    )

    if hindi_detected:
        print("Detected video language: Hindi/Hinglish")
        return "hi"

    # Otherwise check whether English is dominant.
    english_detected = any(
        language == "en" and confidence >= 0.50
        for language, confidence in detections
    )

    if english_detected:
        print("Detected video language: English")
        return "en"

    # If neither English nor Hindi is confidently detected,
    # return the highest-confidence language.
    language, confidence = max(
        detections,
        key=lambda x: x[1]
    )

    print(
        f"Detected video language: {language} "
        f"(confidence: {confidence:.2f})"
    )

    return language


def validate_language(chunks: list, selected_language: str):
    """
    Validate the selected language against the actual video language.

    english  -> expects English
    hinglish -> expects Hindi/Hinglish
    """

    selected = selected_language.strip().lower()

    if selected in ("english", "en"):
        expected = "english"
    elif selected in ("hinglish", "hindi", "hi"):
        expected = "hinglish"
    else:
        raise ValueError(
            "Invalid language selection. "
            "Use 'english' or 'hinglish'."
        )

    detected = detect_video_language(chunks)

    # English selected
    if expected == "english":

        if detected != "en":
            detected_name = {
                "hi": "Hindi/Hinglish"
            }.get(detected, detected)

            raise LanguageMismatchError(
                "english",
                detected_name
            )

        print("✓ Language validation passed: English")

    # Hinglish selected
    else:

        if detected != "hi":
            detected_name = {
                "en": "English"
            }.get(detected, detected)

            raise LanguageMismatchError(
                "hinglish",
                detected_name
            )

        print("✓ Language validation passed: Hindi/Hinglish")


def transcribe_chunk_whisper(chunk_path: str) -> str:
    """
    Transcribe English audio using Whisper.
    """

    model = load_model()

    result = model.transcribe(
        chunk_path,
        task="transcribe",
        language="en",
        fp16=False
    )

    return result["text"]


def _send_to_sarvam(piece_path: str) -> str:
    """
    Send one <=25 second WAV file to Sarvam.

    Sarvam speech-to-text-translate returns English transcript.
    """

    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    with open(piece_path, "rb") as f:

        files = {
            "file": (
                os.path.basename(piece_path),
                f,
                "audio/wav"
            )
        }

        data = {
            "model": SARVAM_MODEL,
            "with_diarization": "false"
        }

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:

        print(f"\n❌ Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")

        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Transcribe Hindi/Hinglish audio using Sarvam.

    Audio is divided into <=25 second pieces.
    Sarvam translates the speech into English.
    """

    audio = AudioSegment.from_wav(chunk_path)

    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""

    total_pieces = (
        len(audio) + piece_ms - 1
    ) // piece_ms

    for i, start in enumerate(
        range(0, len(audio), piece_ms)
    ):

        piece = audio[
            start:start + piece_ms
        ]

        piece_path = (
            f"{chunk_path}_sv_{i}.wav"
        )

        piece.export(
            piece_path,
            format="wav"
        )

        try:

            print(
                f"  → Sarvam piece "
                f"{i + 1}/{total_pieces} ..."
            )

            text = _send_to_sarvam(
                piece_path
            )

            full_text += text + " "

        finally:

            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(
    chunk_path: str,
    language: str = "english"
) -> str:

    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(
            chunk_path
        )

    return transcribe_chunk_whisper(
        chunk_path
    )


def transcribe_all(
    chunks: list,
    language: str = "english"
) -> str:

    if not chunks:
        raise RuntimeError(
            "No audio chunks available for transcription."
        )

    # --------------------------------------------------
    # STEP 1: Validate language BEFORE STT
    # --------------------------------------------------

    validate_language(
        chunks,
        language
    )

    # --------------------------------------------------
    # STEP 2: Select transcription engine
    # --------------------------------------------------

    selected = language.lower()

    if selected == "hinglish":

        engine = "Sarvam AI"

    else:

        engine = "Whisper"

    print(
        f"\nUsing {engine} for transcription."
    )

    # --------------------------------------------------
    # STEP 3: Actual transcription
    # --------------------------------------------------

    full_transcript = ""

    for i, chunk in enumerate(chunks):

        print(
            f"Transcribing chunk "
            f"{i + 1}/{len(chunks)}..."
        )

        text = transcribe_chunk(
            chunk,
            language=language
        )

        full_transcript += text + " "

    print("\nTranscription complete.")

    return full_transcript.strip()