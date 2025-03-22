import os
import sys
import json
import statistics
import concurrent.futures
from pydub import AudioSegment
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4
from mutagen.flac import FLAC, Picture

def get_loudness_cache_path(directory):
    return os.path.join(directory, "loudness_cache.json")

def load_loudness_cache(directory):
    cache_path = get_loudness_cache_path(directory)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass  # Ignore corrupt cache
    return {}

def save_loudness_cache(directory, cache):
    cache_path = get_loudness_cache_path(directory)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

def process_loudness(file_path, cache):
    """Helper function to get dBFS of a single file, using cache if available."""
    if file_path in cache:
        print(".", end='', flush=True)
        return cache[file_path]
    try:
        audio = AudioSegment.from_file(file_path)
        loudness = audio.dBFS
        cache[file_path] = loudness
        print(".", end='', flush=True)
        return loudness
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def get_median_loudness(directory, audio_extensions=(".mp3", ".flac")):
    """Calculates the median loudness of all audio files in the directory, using caching."""
    print("Checking median loudness", end="", flush=True)
    dBFS_values = []
    cache = load_loudness_cache(directory)

    # Collect all files
    files = []
    for root, _, file_list in os.walk(directory):
        for file in file_list:
            if file.lower().endswith(audio_extensions):
                files.append(os.path.join(root, file))

    if not files:
        raise ValueError("No audio files found in the specified directory.")

    # Process files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(lambda f: process_loudness(f, cache), files)

    # Gather results and filter out any None values
    dBFS_values = [r for r in results if r is not None]
    save_loudness_cache(directory, cache)

    if not dBFS_values:
        raise ValueError("No valid audio files found or processed.")

    print(f" Done.")
    return statistics.median(dBFS_values)

def process_normalization(file_path, target_dBFS, tolerance_dB, cache):
    """Processes a single file: extracts metadata, normalizes volume, and restores metadata."""
    try:
        audio = AudioSegment.from_file(file_path)
        current_dBFS = audio.dBFS

        # Skip files that are already within the tolerance range
        if abs(current_dBFS - target_dBFS) <= tolerance_dB:
            print(f"- {os.path.basename(file_path)} (dbfs={round(current_dBFS,3)})... OK!")
            return

        # Adjust loudness
        change_in_dB = target_dBFS - current_dBFS
        adjusted_audio = audio + change_in_dB

        # Get format from extension
        file_extension = os.path.splitext(file_path)[1].lower()
        format_ = file_extension[1:]  # Remove dot (e.g., 'mp3' from '.mp3')

        # Export modified file
        adjusted_audio.export(file_path, format=format_)
        print(f"- {os.path.basename(file_path)} (dbfs={round(current_dBFS,3)})... Normalized.")

        # Update cache
        cache[file_path] = target_dBFS
        save_loudness_cache(os.path.dirname(file_path), cache)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def normalize_volume(directory, target_dBFS=None, tolerance_dB=2.0, audio_extensions=(".mp3", ".flac")):
    """Normalizes the volume of all audio files in the directory using multithreading."""
    cache = load_loudness_cache(directory)

    if target_dBFS is None:
        target_dBFS = get_median_loudness(directory, audio_extensions)
        print(f"Median loudness of files: {target_dBFS} dBFS")

    # Collect all files
    files = []
    for root, _, file_list in os.walk(directory):
        for file in file_list:
            if file.lower().endswith(audio_extensions):
                files.append(os.path.join(root, file))

    # Process files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(lambda f: process_normalization(f, target_dBFS, tolerance_dB, cache), files)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        music_folder = sys.argv[1]
    else:
        music_folder = input("Enter the music folder path: ").strip()
    
    if not os.path.isdir(music_folder):
        print("Error: Provided path is not a valid directory.")
        sys.exit(1)

    normalize_volume(music_folder)
