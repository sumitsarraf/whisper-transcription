import gradio as gr
import whisper
import yt_dlp
import os
import shutil
import textwrap
from datetime import datetime
import mimetypes
import re
import logging
import warnings

warnings.filterwarnings("ignore")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress debug logs from specific libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Load the Whisper model
model = whisper.load_model("base")

# Create directories if they don't exist in project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_unique_filename(prefix="transcription", extension=".txt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"{prefix}_{timestamp}{extension}")

def format_transcription_text(result, youtube_video_name):
    if isinstance(result, dict) and "text" in result:
        result = result["text"]
    else:
        result = str(result)

    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", result)
    paragraphs = []
    paragraph = []

    for sentence in sentences:
        paragraph.append(sentence)
        if len(paragraph) == 4:
            paragraphs.append(" ".join(paragraph))
            paragraph = []

    if paragraph:
        paragraphs.append(" ".join(paragraph))

    formatted = "\n\n".join(paragraphs)
    wrapped = "\n\n".join(["  " + textwrap.fill(p, width=80) for p in formatted.split("\n\n")])
    return wrapped

def transcribe_audio(file_path, youtube_video_name):
    logger.debug(f"Transcribing audio file: {file_path}")
    result = model.transcribe(file_path, fp16=False)
    formatted_text = format_transcription_text(result, youtube_video_name)
    file_name = re.sub(r"[\W_]+", " ", youtube_video_name) + ".txt"
    output_path = os.path.join(OUTPUT_DIR, file_name)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(formatted_text)

    logger.debug(f"Transcription saved to: {output_path}")
    return output_path

def is_valid_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url))

def download_youtube_video(url):
    if not is_valid_youtube_url(url):
        raise gr.Error("Invalid YouTube URL. Please enter a valid YouTube video URL.")

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
        youtube_video_name = info["title"]

        ydl_opts = {
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }],
            "outtmpl": os.path.join(TEMP_DIR, "temp.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_path_wav = os.path.join(TEMP_DIR, "temp.wav")
        if not os.path.exists(file_path_wav):
            raise gr.Error(f"Error downloading YouTube audio: {file_path_wav} not found")

        logger.debug(f"Downloaded YouTube audio to: {file_path_wav}")
        return file_path_wav, youtube_video_name
    except Exception as e:
        logger.error(f"Error downloading YouTube video: {str(e)}")
        raise gr.Error(f"Error downloading YouTube video: {str(e)}")

def process_input(input_type, file_input, url_input):
    try:
        if input_type == "file":
            if file_input is None:
                raise gr.Error("Please upload an audio or video file.")

            mime_type, _ = mimetypes.guess_type(file_input.name)
            if not mime_type or not mime_type.startswith(('audio/', 'video/')):
                raise gr.Error("The uploaded file is not a recognized audio or video format.")

            temp_file = os.path.join(TEMP_DIR, os.path.basename(file_input.name))
            shutil.copy2(file_input.name, temp_file)
            logger.debug(f"Copied uploaded file to: {temp_file}")

            return transcribe_audio(temp_file, os.path.basename(file_input.name))

        elif input_type == "youtube":
            if not url_input:
                raise gr.Error("Please enter a YouTube URL.")
            file_path_wav, youtube_video_name = download_youtube_video(url_input)
            return transcribe_audio(file_path_wav, youtube_video_name)

    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        raise gr.Error(f"Error processing input: {str(e)}")

# Gradio Interface
with gr.Blocks() as app:
    gr.Markdown("# Audio/Video Transcription App")

    with gr.Row():
        input_type = gr.Radio(["file", "youtube"], label="Input Type", value="file")
        file_input = gr.File(label="Upload Audio or Video")
        url_input = gr.Textbox(label="YouTube URL")

    transcribe_button = gr.Button("Transcribe")
    output = gr.File(label="Transcription")

    transcribe_button.click(
        fn=process_input,
        inputs=[input_type, file_input, url_input],
        outputs=output
    )

if __name__ == "__main__":
    logger.info("Starting the Audio/Video Transcription App")
    try:
        app.launch()
    finally:
        logger.info(f"Cleaning up temporary directory: {TEMP_DIR}")
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
