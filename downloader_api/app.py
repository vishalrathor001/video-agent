from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import yt_dlp
import os
import uuid

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"status": "Downloader API is running"}


@app.get("/download")
def download_audio(url: str):

    file_id = str(uuid.uuid4())
    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{file_id}.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb"]
            }
        },

        "js_runtimes": {
            "deno": {},
            "quickjs": {},
        },

        "force_ipv4": True,

        "noplaylist": True,
        "quiet": False,

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                url,
                download=True
            )

        title = info.get("title", "audio")

        wav_path = os.path.join(
            DOWNLOAD_DIR,
            f"{file_id}.wav"
        )

        if not os.path.exists(wav_path):
            raise Exception("WAV file was not created")

        return FileResponse(
            wav_path,
            media_type="audio/wav",
            filename=f"{title}.wav"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )    