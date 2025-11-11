import os
import re
import sys
import logging
import yt_dlp

# Set up logger
logger = logging.getLogger(__name__)

def is_video_url(input_string: str) -> bool:
    """Check if the string looks like a video URL."""
    if not re.match(r'https?://', input_string):
        return False

    video_hosts = ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com"]
    extensions = [".mp4", ".mkv", ".webm", ".mov", ".avi"]
    
    if any(host in input_string for host in video_hosts):
        return True
    if any(ext in input_string for ext in extensions):
        return True
    return False


def download_video(url: str, resolution: str = "1080") -> str:
    """
    Downloads a video using yt-dlp and returns its local path.
    Creates a temp file 'download_path.tmp' with the absolute path.
    """
    download_dir = os.path.join(os.getcwd(), "Downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'noprogress': True,
    }

    temp_path = os.path.join(os.getcwd(), "download_path.tmp")
    try:
        logger.info(f"Starting video download: {url} at resolution {resolution}p")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            file_path = os.path.abspath(file_path)

        # Write the downloaded path to temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(file_path)
        
        logger.info(f"Video downloaded successfully: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        return ""


def main():
    if len(sys.argv) < 2:
        logger.error("No URL provided in command line arguments")
        sys.exit(1)

    url = sys.argv[1]
    res = "1080"

    # Check if resolution flag exists
    if "-r" in sys.argv:
        try:
            res_index = sys.argv.index("-r")
            res = sys.argv[res_index + 1]
            logger.debug(f"Resolution set to: {res}p")
        except Exception as e:
            logger.warning(f"Failed to parse resolution flag, using default: {e}")

    if not is_video_url(url):
        logger.info(f"URL is not a video URL, skipping download: {url}")
        sys.exit(0)

    result = download_video(url, res)
    if not result:
        logger.error(f"Video download failed for: {url}")
        sys.exit(1)
    else:
        logger.info("Video download completed successfully")
        sys.exit(0)


if __name__ == "__main__":
    # Basic logging configuration - can be overridden by calling code
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()