# whisper-transcription
This repository features a Gradio app that transcribes audio and video files, including YouTube content, into text. Utilizing the Whisper speech recognition model and yt-dlp for video downloads, the app offers a simple interface for transcription. Users can upload files or enter a YouTube URL to receive the text output.

## Features

- **File Upload**: Supports uploading local audio and video files for transcription.
- **YouTube Support**: Enter a YouTube URL to transcribe audio from the video.
- **Formatted Output**: Transcriptions are presented in a readable format.
- **Logging and Error Handling**: Provides detailed logs for debugging and robust error management.

## Requirements

- `gradio`
- `whisper`
- `yt-dlp`
- Other standard Python libraries

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo

