import os
import sys
import statistics
from pydub import AudioSegment
from mutagen import File
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4
from mutagen.flac import FLAC, Picture

def get_median_loudness(directory, audio_extensions=('.mp3', '.flac')):
    """
    Calculates the median loudness of all audio files in the directory (recursively).
    :param directory: The root directory to search for audio files.
    :param audio_extensions: A tuple containing allowed audio file extensions.
    :return: The median dBFS loudness of all audio files.
    """
    print("Checking median loudness", end='', flush=True)
    dBFS_values = []

    # Walk through the directory recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(audio_extensions):
                file_path = os.path.join(root, file)
                # Load the audio file
                audio = AudioSegment.from_file(file_path)
                # Add its dBFS value to the list
                dBFS_values.append(audio.dBFS)
                print('.', end='', flush=True)
    
    if not dBFS_values:
        raise ValueError("No audio files found in the specified directory.")
    
    print(f" Done.")

    # Return the median loudness (dBFS)
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

def normalize_volume(directory, target_dBFS=None, tolerance_dB=2.5, audio_extensions=('.mp3', '.flac')):
    """
    Normalizes the volume of all music files in the directory to the calculated average loudness or a given target.
    :param directory: The root directory to search for audio files.
    :param target_dBFS: The target loudness in dBFS. If None, uses the average loudness from the directory.
    :param tolerance_dB: Tolerance in dB to skip files that are close to the target loudness.
    :param audio_extensions: A tuple containing allowed audio file extensions.
    """
    # If no target dBFS is provided, calculate the average loudness
    if target_dBFS is None:
        target_dBFS = get_median_loudness(directory, audio_extensions)
        print(f"Median loudness of files: {target_dBFS} dBFS")

    # Walk through the directory recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(audio_extensions):
                file_path = os.path.join(root, file)
                album_art = extract_album_art(file_path)
                tags = extract_tags(file_path)
                audio = AudioSegment.from_file(file_path)
                current_dBFS = audio.dBFS
                print(f"- {file} (dbfs={round(current_dBFS,3)})... ", end='', flush=True)

                # Calculate the difference between current and target loudness
                if abs(current_dBFS - target_dBFS) <= tolerance_dB:
                    print(f"OK!")
                    continue  # Skip files that are within the tolerance range
                
                # Calculate the change needed to normalize the audio to the target dBFS
                change_in_dB = target_dBFS - current_dBFS
                adjusted_audio = audio + change_in_dB
                
                # Get the file extension and format it accordingly
                file_extension = os.path.splitext(file)[1].lower()
                format_ = file_extension[1:]  # Remove the dot (e.g., 'mp3' from '.mp3')

                # Export the adjusted audio file, keeping the original format and quality
                adjusted_audio.export(file_path, format=format_)
                print(f"Normalized.")

                # Write the album art and tags back to the file, if extracted earlier
                if album_art or tags:
                    write_album_art_and_tags(file_path, album_art, tags)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        music_folder = sys.argv[1]
    else:
        music_folder = input("Enter the music folder path: ").strip()
    
    if not os.path.isdir(music_folder):
        print("Error: Provided path is not a valid directory.")
        sys.exit(1)

    normalize_volume(music_folder)
