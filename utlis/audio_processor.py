import os
import uuid
import requests
import yt_dlp

from pydub import AudioSegment

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """
    Download YouTube audio through the external downloader API
    and return the downloaded WAV file path.
    """

    downloader_api = os.getenv("DOWNLOADER_API_URL")

    if not downloader_api:
        raise ValueError(
            "DOWNLOADER_API_URL is not configured."
        )

    print("Downloading YouTube audio through Downloader API...")

    try:
        response = requests.get(
            downloader_api,
            params={"url": url},
            timeout=900
        )

        response.raise_for_status()

        wav_path = os.path.join(
            DOWNLOAD_DIR,
            f"{uuid.uuid4()}.wav"
        )

        with open(wav_path, "wb") as f:
            f.write(response.content)

        if not os.path.exists(wav_path):
            raise FileNotFoundError(
                "Downloader API did not create the WAV file."
            )

        print(f"Downloaded WAV: {wav_path}")

        return wav_path

    except requests.RequestException as e:
        print(f"❌ Downloader API failed: {e}")
        raise


def convert_to_wav(input_path: str) -> str:

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)

    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(output_path, format="wav")

    return output_path


def chunk_audio(
    wav_path: str,
    chunks_minutes: int = 10
) -> list:

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunks_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(
        range(0, len(audio), chunk_ms)
    ):
        chunk = audio[start:start + chunk_ms]

        chunk_path = f"{wav_path}_chunk_{i}.wav"

        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:

    if source.startswith("http://") or source.startswith("https://"):

        print(
            "Detected YouTube URL. "
            "Using Downloader API..."
        )

        wav_path = download_youtube_audio(source)

    else:

        print(
            "Detected local file. "
            "Converting to WAV..."
        )

        wav_path = convert_to_wav(source)

    if not os.path.exists(wav_path):
        raise FileNotFoundError(
            f"Audio file does not exist: {wav_path}"
        )

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(
        f"Audio ready - {len(chunks)} chunks created!"
    )

    return chunks