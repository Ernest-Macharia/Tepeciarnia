import os
import re
import sys
import subprocess
import tempfile
import yt_dlp


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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            file_path = os.path.abspath(file_path)

        # Write the downloaded path to temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(file_path)

        print(f"[OK] Downloaded: {file_path}")
        return file_path

    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return ""


def main():
    if len(sys.argv) < 2:
        print("Usage: downloader.py <url> [-r <resolution>]")
        sys.exit(1)

    url = sys.argv[1]
    res = "1080"

    # Check if resolution flag exists
    if "-r" in sys.argv:
        try:
            res_index = sys.argv.index("-r")
            res = sys.argv[res_index + 1]
        except Exception:
            pass

    if not is_video_url(url):
        print("[SKIP] Input is not a video URL")
        sys.exit(0)

    result = download_video(url, res)
    if not result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
