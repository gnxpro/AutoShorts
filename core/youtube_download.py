import os
import subprocess
import re
import sys
import shutil
from urllib.parse import urlparse, parse_qs


class YouTubeDownloadError(Exception):
    pass


def find_yt_dlp():
    """
    Find yt-dlp executable in various locations.
    
    Search order:
    1. venv/Scripts/yt-dlp.exe (Windows) or venv/bin/yt-dlp (Unix)
    2. sys.executable directory (Python interpreter directory)
    3. System PATH
    4. Current working directory
    
    Returns:
        str: Path to yt-dlp executable
        
    Raises:
        YouTubeDownloadError: If yt-dlp is not found
    """
    
    # Possible names for yt-dlp executable
    exe_names = ["yt-dlp.exe", "yt-dlp"] if sys.platform == "win32" else ["yt-dlp"]
    
    # Possible locations to search
    search_paths = []
    
    # 1. venv Scripts/bin directory
    python_dir = os.path.dirname(sys.executable)
    search_paths.append(python_dir)
    
    # 2. venv parent directory (in case we're in a venv)
    venv_parent = os.path.dirname(python_dir)
    if sys.platform == "win32":
        search_paths.append(os.path.join(venv_parent, "Scripts"))
    else:
        search_paths.append(os.path.join(venv_parent, "bin"))
    
    # 3. Current working directory
    search_paths.append(os.getcwd())
    
    # Search in all paths
    for path in search_paths:
        for exe_name in exe_names:
            full_path = os.path.join(path, exe_name)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return full_path
    
    # 4. Try to find in system PATH using shutil.which
    for exe_name in exe_names:
        which_result = shutil.which(exe_name)
        if which_result:
            return which_result
    
    # If still not found, raise error with helpful message
    raise YouTubeDownloadError(
        f"yt-dlp executable not found. Please install it using: pip install yt-dlp\n"
        f"Searched in: {', '.join(search_paths)}"
    )


def clean_youtube_url(url: str) -> str:
    """
    Clean YouTube URL to avoid playlist and other parameters.
    
    Converts various YouTube URL formats to standard youtu.be format.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if "v" in query:
        vid = query["v"][0]
        return f"https://youtu.be/{vid}"

    if parsed.netloc in ("youtu.be",):
        return f"https://youtu.be{parsed.path}"

    return url


def download_youtube(
    url: str,
    output_dir: str,
    cookies: str = None,
    progress_callback=None,
    download_subtitle=True
):
    """
    Download video from YouTube using yt-dlp.
    
    Args:
        url (str): YouTube video URL
        output_dir (str): Directory to save downloaded video
        cookies (str): Path to cookies file (optional)
        progress_callback (callable): Callback function for progress updates
        download_subtitle (bool): Whether to download subtitles
        
    Returns:
        str: Path to downloaded video file
        
    Raises:
        YouTubeDownloadError: If download fails
    """
    
    os.makedirs(output_dir, exist_ok=True)

    # Clean URL to avoid playlist / radio params
    url = clean_youtube_url(url)

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    # Find yt-dlp executable
    try:
        yt_dlp_path = find_yt_dlp()
    except YouTubeDownloadError as e:
        raise YouTubeDownloadError(str(e))

    # Build command
    cmd = [yt_dlp_path]

    # Note: Removed --cookies-from-browser due to Chrome access issues
    # If you need cookies, provide a cookies.txt file instead

    # Download subtitles if requested
    if download_subtitle:
        cmd += ["--write-subs", "--sub-format", "vtt"]

    # Add format and output template
    cmd += [
        "-f", "best[height<=720]",
        "-o", output_template,
        url
    ]

    # Execute download
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except Exception as e:
        raise YouTubeDownloadError(f"Failed to start yt-dlp process: {e}")

    percent_pattern = re.compile(r"(\d{1,3}\.\d+)%")
    downloaded_file = None
    output_lines = []

    try:
        for line in process.stdout:
            line = line.strip()
            output_lines.append(line)

            # Parse progress
            if "[download]" in line and "%" in line:
                match = percent_pattern.search(line)
                if match and progress_callback:
                    try:
                        progress_callback(float(match.group(1)) / 100)
                    except Exception:
                        pass

            # Detect final filename
            if "Destination:" in line:
                downloaded_file = line.split("Destination:")[-1].strip()

        process.wait()
    except Exception as e:
        raise YouTubeDownloadError(f"Error reading yt-dlp output: {e}")

    # Check if download was successful
    if process.returncode != 0:
        error_msg = "\n".join(output_lines[-10:]) if output_lines else "Unknown error"
        raise YouTubeDownloadError(f"yt-dlp CLI download failed with return code {process.returncode}.\nError: {error_msg}")

    # Fallback: find file if destination wasn't detected
    if not downloaded_file:
        files = os.listdir(output_dir)
        if files:
            # Sort to pick most recent
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(output_dir, f)),
                reverse=True
            )
            downloaded_file = os.path.join(output_dir, files[0])
        else:
            raise YouTubeDownloadError("Downloaded file not found in output directory.")

    # Verify file exists
    if not os.path.exists(downloaded_file):
        raise YouTubeDownloadError(f"Downloaded file not found: {downloaded_file}")

    return downloaded_file


# Example usage for testing
if __name__ == "__main__":
    print("Testing yt-dlp finder...")
    try:
        yt_dlp = find_yt_dlp()
        print(f"Found yt-dlp at: {yt_dlp}")
    except YouTubeDownloadError as e:
        print(f"Error: {e}")
