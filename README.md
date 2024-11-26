# YouTube Content Extractor

A Python script to extract transcripts and content from YouTube videos using either YouTube's built-in transcript feature or OpenAI's Whisper model.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. If using Whisper method, you'll need an OpenAI API key.

## Usage

### Basic Usage

```bash
python extract.py "VIDEO_URL"
```

### Options

- `url`: YouTube video URL (required)
- `--method`: Transcription method (`transcript` or `whisper`, default: `transcript`)
- `--openai-key`: OpenAI API key (required when using whisper method)

### Examples

```bash
# Extract using YouTube's transcript (default method)
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Extract using Whisper
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID" --method whisper --openai-key YOUR_API_KEY
```

## Features

- Extract video transcripts using YouTube's built-in transcript feature
- Alternative transcription using OpenAI's Whisper model
- Retrieves video metadata including title and thumbnail URL
- Supports English language transcripts

## Requirements

- Python 3.8+
- langchain-community
- pytube
- openai (for Whisper transcription)

## Error Handling

The script will return an error message in the response dictionary if:

- There's an issue processing the video
- The OpenAI API key is missing when using the whisper method
- The video URL is invalid

## License

This project is licensed under the MIT License - see the LICENSE file for details.
