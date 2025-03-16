import os
import sys
import statistics
import concurrent.futures
from pydub import AudioSegment
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4
from mutagen.flac import FLAC, Picture

def process_loudness(file_path):
    """Helper function to get dBFS of a single file."""
    try:
        audio = AudioSegment.from_file(file_path)
        print('.', end='', flush=True)
        return audio.dBFS
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def get_median_loudness(directory, audio_extensions=('.mp3', '.flac')):
    """
    Calculates the median loudness of all audio files in the directory (recursively) using multithreading.
    """
    print("Checking median loudness", end='', flush=True)
    dBFS_values = []

    # Collect all files
    files = []
    for root, _, file_list in os.walk(directory):
        for file in file_list:
            if file.lower().endswith(audio_extensions):
                files.append(os.path.join(root, file))

    if not files:
        raise ValueError("No audio files found in the specified directory.")

    # Process files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = executor.map(process_loudness, files)

    # Gather results and filter out any None values
    dBFS_values = [r for r in results if r is not None]
    
    if not dBFS_values:
        raise ValueError("No valid audio files found or processed.")

    print(f" Done.")

    return statistics.median(dBFS_values)

def extract_album_art(file_path):
    audio_file = File(file_path, easy=False)
    if isinstance(audio_file, ID3) and "APIC:" in audio_file:
        return audio_file["APIC:"].data
    elif isinstance(audio_file, MP4) and "covr" in audio_file:
        return audio_file["covr"][0]
    elif isinstance(audio_file, FLAC):
        for picture in audio_file.pictures:
            if picture.type == 3:
                return picture.data
    return None

def extract_tags(file_path):
    audio_file = File(file_path, easy=False)
    return audio_file.tags if audio_file.tags else None

def write_album_art_and_tags(file_path, album_art, tags):
    audio_file = File(file_path, easy=False)
    if audio_file.tags is None:
        audio_file.add_tags()
    if album_art:
        if isinstance(audio_file, ID3):
            audio_file.tags["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=album_art)
        elif isinstance(audio_file, MP4):
            audio_file.tags["covr"] = [album_art]
        elif isinstance(audio_file, FLAC):
            picture = Picture()
            picture.data = album_art
            picture.type = 3
            picture.mime = "image/jpeg"
            audio_file.clear_pictures()
            audio_file.add_picture(picture)
    for key, value in tags.items():
        audio_file.tags[key] = value
    audio_file.save()


def process_normalization(file_path, target_dBFS, tolerance_dB):
    """Processes a single file: extracts metadata, normalizes volume, and restores metadata."""
    try:
        album_art = extract_album_art(file_path)
        tags = extract_tags(file_path)
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

        # Restore metadata
        if album_art or tags:
            write_album_art_and_tags(file_path, album_art, tags)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def normalize_volume(directory, target_dBFS=None, tolerance_dB=2.0, audio_extensions=('.mp3', '.flac')):
    """
    Normalizes the volume of all audio files in the directory using multithreading.
    """
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(lambda f: process_normalization(f, target_dBFS, tolerance_dB), files)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        music_folder = sys.argv[1]
    else:
        music_folder = input("Enter the music folder path: ").strip()
    
    if not os.path.isdir(music_folder):
        print("Error: Provided path is not a valid directory.")
        sys.exit(1)

    normalize_volume(music_folder)
