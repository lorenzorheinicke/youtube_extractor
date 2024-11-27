# YouTube Content Extractor

A Python script to extract transcripts and content from YouTube videos using either YouTube's built-in transcript feature or OpenAI's Whisper model.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. If using Whisper method, create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_api_key_here
```

3. Make sure you have FFmpeg installed (required for audio processing):
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - MacOS: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html

## Usage

### Basic Usage

```bash
python extract.py "VIDEO_URL"
```

### Options

- `url`: YouTube video URL (required)
- `--method`: Transcription method (`transcript` or `whisper`, default: `transcript`)
- `--format`: Output format (`text` or `markdown`, default: `text`)

### Examples

```bash
# Extract using YouTube's transcript in plain text (default)
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Extract using YouTube's transcript in markdown format
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID" --format markdown

# Extract using Whisper
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID" --method whisper
```

## Features

- Extract video transcripts using YouTube's built-in transcript feature
- Alternative transcription using OpenAI's Whisper model
- Support for both manual and auto-generated captions
- Output in plain text or markdown format with timestamps
- Retrieves comprehensive video metadata including:
  - Title and description
  - View count and ratings
  - Channel information
  - Publication date
  - Keywords/tags
- Supports English language transcripts

## Requirements

- Python 3.8+
- yt-dlp
- requests
- openai (for Whisper transcription)
- python-dotenv
- FFmpeg (for audio processing)

## Output Formats

### Text Format

Plain text output combines all transcript segments into a continuous text.

### Markdown Format

Markdown output includes timestamps and proper formatting:

```markdown
[00:00:00] First line of transcript

[00:00:03] Next line with timestamp
```

## Error Handling

The script will return an error message in the response dictionary if:

- There's an issue processing the video
- The OpenAI API key is missing when using the whisper method
- FFmpeg is not installed (required for Whisper method)
- The video URL is invalid
- No transcripts are available for the video

## License

This project is licensed under the MIT License - see the LICENSE file for details.
