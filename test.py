from dotenv import load_dotenv
load_dotenv()
from utlis.audio_processor import process_input
from core.transcriber import transcribe_all
import os



os.environ["PATH"] += os.pathsep + r"C:\Users\desktop\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin"

source = "https://www.youtube.com/watch?v=vFP1mgZ_LEY"
language = "hinglish"

chunks = process_input(source)
transcript = transcribe_all(chunks,language=language)
print("\n=== TRANSCRIPT ===\n ")
print(transcript)