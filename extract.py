import argparse
import os

from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.parsers.audio import \
    OpenAIWhisperParser
from pytube import YouTube


def get_transcription_with_whisper(video_url: str, openai_api_key: str) -> str:
    yt = YouTube(video_url)
    
    # Download audio
    audio = yt.streams.filter(only_audio=True).first()
    audio_file = audio.download(filename="temp_audio")
    
    # Initialize Whisper parser
    parser = OpenAIWhisperParser(api_key=openai_api_key)
    
    # Transcribe audio
    with open(audio_file, "rb") as file:
        transcription = parser.parse(file)
    
    # Clean up
    os.remove(audio_file)
    
    return transcription

def get_youtube_content(video_url: str) -> dict:
    try:
        # Initialize YouTube object
        yt = YouTube(video_url)
        
        # Get all available properties with safe fallbacks and debug logging
        try:
            video_info = {}
            
            # Add each property individually with error checking
            properties = [
                ('video_id', lambda: yt.video_id),
                ('thumbnail_url', lambda: yt.thumbnail_url),
                ('description', lambda: yt.description or ''),
                ('length', lambda: int(yt.length) if yt.length is not None else 0),
                ('views', lambda: int(yt.views) if yt.views is not None else 0),
                ('author', lambda: yt.author or ''),
                ('channel_id', lambda: yt.channel_id),
                ('channel_url', lambda: yt.channel_url),
                ('publish_date', lambda: yt.publish_date),
                ('rating', lambda: float(yt.rating) if yt.rating is not None else 0.0),
                ('keywords', lambda: yt.keywords or []),
                ('captions', lambda: yt.captions or {}),
                ('metadata', lambda: yt.metadata or {}),
                ('age_restricted', lambda: bool(yt.age_restricted) if yt.age_restricted is not None else False)
            ]
            
            for prop_name, prop_getter in properties:
                try:
                    video_info[prop_name] = prop_getter()
                except Exception as prop_error:
                    print(f"Error getting {prop_name}: {str(prop_error)}")
                    video_info[prop_name] = None
        
        except Exception as e:
            print(f"Error building video_info dictionary: {str(e)}")
            return {'error': str(e)}
        
        # Get transcript using LangChain's YoutubeLoader
        try:
            loader = YoutubeLoader(
                video_url,
                add_video_info=True,
                language=['en', None],  # Try both English and auto-detect
                translation='en'  # Add translation support
            )
            
            print("Attempting to load transcript...")  # Debug line
            transcript = loader.load()
            
            if transcript and len(transcript) > 0:
                video_info['transcript'] = transcript[0].page_content
                video_info['transcript_metadata'] = transcript[0].metadata
            else:
                print("No transcript content found in loader response")
                # Fallback to captions if available
                if yt.captions:
                    caption_track = yt.captions.get('en') or next(iter(yt.captions.values()))
                    if caption_track:
                        video_info['transcript'] = caption_track.generate_srt_captions()
                        video_info['transcript_metadata'] = {'source': 'youtube_captions'}
                
        except Exception as e:
            print(f"Error getting transcript (detailed): {str(e)}")
            if hasattr(e, '__cause__'):
                print(f"Caused by: {str(e.__cause__)}")
            video_info['transcript'] = None
            video_info['transcript_metadata'] = None
        
        return video_info
        
    except Exception as e:
        print(f"Top-level error: {str(e)}")
        return {
            'error': f"Error processing video: {str(e)}"
        }

# Optional: Function to download thumbnail
def download_thumbnail(url: str, filename: str) -> str:
    """
    Download the thumbnail image.
    
    Args:
        url (str): Thumbnail URL
        filename (str): Desired filename for saving
        
    Returns:
        str: Path to saved thumbnail
    """
    try:
        yt = YouTube(url)
        thumbnail_url = yt.thumbnail_url
        
        # Use pytube to download the thumbnail
        yt.thumbnail_url = filename
        return filename
    except Exception as e:
        return f"Error downloading thumbnail: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract content from YouTube videos')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--method', choices=['transcript', 'whisper'], 
                       default='transcript',
                       help='Choose extraction method: transcript (default) or whisper')
    parser.add_argument('--openai-key', help='OpenAI API key (required for whisper method)')

    result = get_youtube_content("https://www.youtube.com/watch?v=X7GCbGVwcWg")
    print(result)
    
    # args = parser.parse_args()
    
    # if args.method == 'whisper':
    #     if not args.openai_key:
    #         print("Error: OpenAI API key is required for whisper method")
    #         parser.print_help()
    #         exit(1)
    #     result = get_transcription_with_whisper(args.url, args.openai_key)
    #     print(result)
    # else:
    #     result = get_youtube_content(args.url)
    #     print(result)