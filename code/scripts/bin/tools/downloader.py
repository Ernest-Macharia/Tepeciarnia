import argparse
import sys
import requests
import os
from urllib.parse import urlparse

try:
    import yt_dlp
    from tqdm import tqdm
except ImportError:
    pass

# --- CONFIGURATION ---
TEMP_PATH_FILENAME = "download_path.tmp"

# --- Utility Functions for Console Output ---

def eprint(*args, **kwargs):
    """Prints status messages to standard error (stderr)."""
    print(*args, file=sys.stderr, **kwargs)

def get_target_directory():
    """Returns and creates the target download directory: ~/Downloads/WallVideos/."""
    # Find the user's home directory
    home = os.path.expanduser('~')
    # Use 'Downloads' as the base, which is standard on most OSes
    downloads = os.path.join(home, 'Videos')
    
    # Create the final target path
    target_dir = os.path.join(downloads, 'WallVideos')
    
    # Ensure the directory exists
    try:
        os.makedirs(target_dir, exist_ok=True)
        return target_dir
    except OSError as e:
        eprint(f"Error creating target directory {target_dir}: {e}. Falling back to current directory.")
        # Fallback to current directory if creation fails
        return os.getcwd()

# --- Download Handlers ---

def download_youtube_video(url, output_name_base, resolution, target_dir):
    """Downloads highest quality video-only stream (with fallback) using yt-dlp."""
    try:
        # Define the output template using the target directory
        out_tmpl = os.path.join(target_dir, f'{output_name_base}.%(ext)s')
        
        # 1. Attempt the user-specified resolution (bestvideo[height<=X])
        format_string = f'bestvideo[height<={resolution}]'
        
        ydl_opts_attempt1 = {
            'format': format_string,
            'outtmpl': out_tmpl,
            'progress_hooks': [lambda d: _progress_hook(d, output_name_base)],
            'quiet': False,
            'noplaylist': True,
            'no_warnings': True,
            'verbose': False,
            'noprogress': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_attempt1) as ydl:
            eprint(f"Attempting to download video-only stream at resolution <= {resolution}...")
            info = ydl.extract_info(url, download=True)
            
            # Use 'filepath' from the final location (if available)
            if info.get('requested_downloads'):
                return info['requested_downloads'][0]['filepath']
            else:
                pass

    except Exception as e:
        eprint(f"Download attempt failed for specific resolution or due to error: {e}")
        
    # --- 2. Fallback to Absolute Best Video-Only Stream ---
    eprint("Falling back to absolute best video-only stream available.")
    try:
        ydl_opts_fallback = {
            'format': 'bestvideo',
            'outtmpl': out_tmpl,
            'progress_hooks': [lambda d: _progress_hook(d, output_name_base)],
            'quiet': False,
            'noplaylist': True,
            'no_warnings': True,
            'verbose': False,
            'noprogress': True
        }

        with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
            info = ydl.extract_info(url, download=True)
            if info.get('requested_downloads'):
                return info['requested_downloads'][0]['filepath']
            else:
                eprint("Fallback failed to return a file path.")
                return None
            
    except Exception as e:
        eprint(f"Error: A yt-dlp download error occurred: {e}")
        return None

def _progress_hook(d, title):
    """tqdm progress hook for yt-dlp."""
    global pbar
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes', 0)
        
        if not downloaded_bytes:
            return

        # Initialize tqdm on stderr
        if 'pbar' not in globals() and total_bytes:
            pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, 
                        desc=f"[{title}] Download", file=sys.stderr, leave=True)
        
        if 'pbar' in globals():
            pbar.update(downloaded_bytes - pbar.n)
            
    elif d['status'] == 'finished':
        if 'pbar' in globals():
            pbar.close()
            del globals()['pbar']
            eprint(f"[{title}] Download finished.")
    elif d['status'] == 'error':
        if 'pbar' in globals():
            pbar.close()
            del globals()['pbar']
        eprint(f"[{title}] Download error.")

def download_direct_file(url, output_name_base, target_dir):
    """Downloads a file directly using requests streaming."""
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            
            # Use the output_name_base and the last part of the URL path for extension
            path_filename = urlparse(url).path.split('/')[-1]
            ext = os.path.splitext(path_filename)[1] or ".mp4" 
            
            # Construct the final path within the target directory
            final_filename = os.path.join(target_dir, f"{output_name_base}{ext}")

            total_size = int(response.headers.get('content-length', 0))
            
            with tqdm(total=total_size, unit='B', unit_scale=True, 
                      desc=f"[{output_name_base}] Download", file=sys.stderr) as pbar:
                
                with open(final_filename, 'wb') as f:
                    # shutil.copyfileobj can sometimes be more efficient, but iter_content is clearer with tqdm
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            return os.path.abspath(final_filename)

    except requests.exceptions.RequestException as e:
        eprint(f"Error: Direct download failed: {e}")
        return None
    except Exception as e:
        eprint(f"Error: Could not write file: {e}")
        return None

# --- Main Execution ---

if __name__ == "__main__":
    if 'yt_dlp' not in sys.modules:
        eprint("Error: The 'yt-dlp' and 'tqdm' libraries are required for full functionality.")
        eprint("Please install them using: pip install yt-dlp tqdm")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Downloads videos from YouTube or direct links.")
    parser.add_argument("url", type=str, help="The video URL (YouTube or direct file link).")
    parser.add_argument("-o", "--output-name", type=str, default=None, 
                        help="Base name for the output file (e.g., 'my_clip').")
    parser.add_argument("-r", "--resolution", type=int, default=1080,
                        help="Maximum resolution height for YouTube videos (e.g., 720, 1080).")

    args = parser.parse_args()
    
    # Define the target directory once
    TARGET_DIR = get_target_directory()
    eprint(f"Saving files to: {TARGET_DIR}")

    # --- FILENAME RESOLUTION LOGIC ---
    if args.output_name is None:
        if "youtube.com" in args.url or "youtu.be" in args.url:
            # 1. YouTube: Use yt-dlp to extract the title
            try:
                eprint("Attempting to determine file name from YouTube video title...")
                ydl_opts = {'quiet': True, 'simulate': True, 'noplaylist': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(args.url, download=False)
                    # Sanitize the title and use it
                    args.output_name = ydl.sanitize_info(info)['title'].replace(" ", "_")
            except Exception:
                eprint("Warning: Could not extract YouTube title. Using default name.")
                args.output_name = "downloaded_youtube_video"

        else:
            # 2. Direct File: Extract name from URL path
            parsed_url = urlparse(args.url)
            path = parsed_url.path
            filename_with_ext = path.split('/')[-1]
            
            if filename_with_ext and '.' in filename_with_ext:
                args.output_name = os.path.splitext(filename_with_ext)[0]
                eprint(f"Using filename derived from URL: {args.output_name}")
            else:
                eprint("Warning: Could not determine filename from URL. Using default name.")
                args.output_name = "downloaded_file"
    # --- END FILENAME RESOLUTION LOGIC ---

    final_path = None

    if "youtube.com" in args.url or "youtu.be" in args.url:
        final_path = download_youtube_video(args.url, args.output_name, args.resolution, TARGET_DIR)
    else:
        final_path = download_direct_file(args.url, args.output_name, TARGET_DIR)

    # --- Final Output ---
    # The temporary file is saved in the script's execution directory (os.getcwd())
    temp_file = os.path.join(os.getcwd(), TEMP_PATH_FILENAME)
    
    # Clean up any old temporary file
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except OSError as e:
            eprint(f"Warning: Could not delete old temp file {temp_file}: {e}")

    if final_path:
        # Write the absolute path to a temporary file for AutoIt to read.
        try:
            with open(temp_file, 'w') as f:
                f.write(final_path)
            eprint(f"Success: Wrote path to temporary file: {temp_file}")
            sys.exit(0) # Success
        except Exception as e:
            eprint(f"CRITICAL ERROR: Could not write path to temp file {temp_file}: {e}")
            sys.exit(1) # Failure
    else:
        eprint("Download failed. Exiting with error code 1.")
        sys.exit(1) # Failure
