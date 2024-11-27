import argparse
import json
import os
import subprocess
from urllib.parse import parse_qs, urlparse

import requests
import yt_dlp
from dotenv import load_dotenv
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.parsers.audio import \
    OpenAIWhisperParser


def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed and accessible."""
    try:
        # Try to run ffmpeg -version
        result = subprocess.run(['ffmpeg', '-version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_transcription_with_whisper(video_url: str, openai_api_key: str) -> dict:
    # Check for ffmpeg installation first
    if not check_ffmpeg_installed():
        return {
            "success": False,
            "error": "FFmpeg is not installed. Please install FFmpeg first:\n"
                    "- On Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                    "- On MacOS: brew install ffmpeg\n"
                    "- On Windows: Download from https://ffmpeg.org/download.html"
        }

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'temp_audio.%(ext)s',  # Specify output template
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
        # Initialize the Whisper parser
        parser = OpenAIWhisperParser(api_key=openai_api_key)
        
        # Process the audio file with Whisper
        audio_file_path = "temp_audio.mp3"
        with open(audio_file_path, "rb") as audio_file:
            transcription = parser.parse(audio_file)
        
        # Clean up the temporary audio file
        os.remove(audio_file_path)
        
        return {
            "success": True,
            "transcription": transcription
        }
            
    except Exception as e:
        # Clean up in case of error
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        return {
            "success": False,
            "error": f"Failed to process video: {str(e)}"
        }

def download_subtitles(subtitle_url: str, format: str) -> str:
    """
    Download and parse subtitles from the YouTube API URL.
    """
    try:
        response = requests.get(subtitle_url)
        response.raise_for_status()
        
        if format == 'json3':
            # Parse JSON3 format
            data = json.loads(response.text)
            if 'events' in data:
                return data['events']
        else:
            # Return raw content for other formats
            return response.text
            
    except Exception as e:
        print(f"Error downloading subtitles: {str(e)}")
        return None

def process_transcript(subtitle_data: list, format: str = 'text') -> str:
    """
    Process subtitle data into either plain text or markdown format.
    """
    if not subtitle_data:
        print("Debug: No subtitle data received")
        return ""
    
    # If we have a list of subtitle format options
    if isinstance(subtitle_data, list):
        # Prefer json3 format as it's easiest to parse
        json3_format = next((fmt for fmt in subtitle_data if fmt['ext'] == 'json3'), None)
        
        if json3_format:
            subtitle_content = download_subtitles(json3_format['url'], 'json3')
            if subtitle_content:
                if format == 'text':
                    # Concatenate all text segments
                    text_parts = []
                    for event in subtitle_content:
                        if 'segs' in event:
                            for seg in event['segs']:
                                if 'utf8' in seg:
                                    text_parts.append(seg['utf8'].strip())
                    return ' '.join(text_parts)
                
                elif format == 'markdown':
                    # Create markdown with timestamps
                    markdown_lines = []
                    for event in subtitle_content:
                        if 'segs' in event:
                            # Convert tstart from milliseconds to seconds
                            start_time = int(event.get('tStartMs', 0) / 1000)
                            
                            # Convert to HH:MM:SS format
                            hours = start_time // 3600
                            minutes = (start_time % 3600) // 60
                            seconds = start_time % 60
                            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                            
                            # Collect all segments for this timestamp
                            text_parts = []
                            for seg in event['segs']:
                                if 'utf8' in seg:
                                    text_parts.append(seg['utf8'].strip())
                            
                            if text_parts:
                                line = f"[{timestamp}] {' '.join(text_parts)}"
                                markdown_lines.append(line)
                    
                    return '\n\n'.join(markdown_lines)
    
    return ""

def get_youtube_content(video_url: str, transcript_format: str = 'text') -> dict:
    try:
        # Configure yt-dlp options
        ydl_opts = {
            'quiet': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'skip_download': True,
            'force_generic_extractor': False
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(video_url, download=False)
            
            processed_info = {
                'video_id': video_info.get('id'),
                'thumbnail_url': video_info.get('thumbnail'),
                'description': video_info.get('description', ''),
                'length': video_info.get('duration', 0),
                'views': video_info.get('view_count', 0),
                'author': video_info.get('uploader', ''),
                'channel_id': video_info.get('channel_id'),
                'channel_url': video_info.get('channel_url'),
                'publish_date': video_info.get('upload_date'),
                'rating': video_info.get('average_rating', 0.0),
                'keywords': video_info.get('tags', []),
                'age_restricted': video_info.get('age_limit', 0) > 0
            }

            # Get available subtitles
            subtitles = video_info.get('subtitles', {})
            auto_subtitles = video_info.get('automatic_captions', {})
            
            # Try to get English subtitles, first manual then auto-generated
            if 'en' in subtitles:
                subtitle_data = subtitles['en']
                processed_info['transcript'] = process_transcript(subtitle_data, transcript_format)
                processed_info['transcript_source'] = 'manual'
            elif 'en' in auto_subtitles:
                subtitle_data = auto_subtitles['en']
                processed_info['transcript'] = process_transcript(subtitle_data, transcript_format)
                processed_info['transcript_source'] = 'auto-generated'
            else:
                processed_info['transcript'] = None
                processed_info['transcript_source'] = None
                print("No English subtitles or auto-captions found")
        
        return processed_info
        
    except Exception as e:
        print(f"Top-level error: {str(e)}")
        return {
            'error': f"Error processing video: {str(e)}"
        }

def download_thumbnail(url: str, filename: str) -> str:
    """
    Download the thumbnail image.
    
    Args:
        url (str): Video URL
        filename (str): Desired filename for saving
        
    Returns:
        str: Path to saved thumbnail
    """
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(url, download=False)
            thumbnail_url = video_info['thumbnail']
            
            # Download the thumbnail using yt-dlp's download_webpage function
            ydl.download_webpage(thumbnail_url, filename)
            return filename
            
    except Exception as e:
        return f"Error downloading thumbnail: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract content from YouTube videos')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--method', choices=['transcript', 'whisper'], 
                       default='transcript',
                       help='Choose extraction method: transcript (default) or whisper')
    parser.add_argument('--format', choices=['text', 'markdown'],
                       default='text',
                       help='Choose transcript format: text (default) or markdown')
    
    args = parser.parse_args()
    
    if args.method == 'whisper':
        load_dotenv()
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_key:
            print("Error: OPENAI_API_KEY environment variable is not set")
            exit(1)
            
        result = get_transcription_with_whisper(args.url, openai_key)
        print(result)
    else:
        result = get_youtube_content(args.url, args.format)
        print(result)