#!venv/bin/python
# How It Works:
#     It scans all audio files in the folder tree.
#     Extracts existing album art and converts it to:
#         Baseline JPEG (no progressive encoding).
#         Max 512px size while preserving aspect ratio.
#     Updates the file with the new album art.

# Notes:
#     MP3, FLAC, and M4A are supported.
#     WAV files are skipped since they don’t have standard embedded album art.
#     Quality is set to 85 to balance file size and quality.

import os
import sys
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4Cover
from PIL import Image
import io
import ffmpeg


# Supported audio extensions
AUDIO_EXTENSIONS = {".flac", ".m4a", ".mp3", ".wav"}

# Max size for artwork
MAX_SIZE = 512

def get_image_dimensions_format_and_progressive(image_data):
    """Extract image dimensions, format, and check if JPEG is progressive."""
    with Image.open(io.BytesIO(image_data)) as img:
        is_progressive = "progressive" in img.info
        return img.size, img.format, is_progressive

def process_image(image_data):
    """Convert image to baseline JPEG and resize if needed"""
    (width, height), img_format, is_progressive = get_image_dimensions_format_and_progressive(image_data)
    
    if max(width, height) <= MAX_SIZE and img_format == "JPEG" and not is_progressive:
        print(" OK!")
        return image_data  # Skip processing if already within limits and baseline JPEG
    
    with Image.open(io.BytesIO(image_data)) as img:
        img = img.convert("RGB")
        img.thumbnail((MAX_SIZE, MAX_SIZE))
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, progressive=False)
        print(" Converted.")
        return output.getvalue()

def process_audio_file(filepath):
    """Process an audio file and update album art if necessary"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".mp3":
        audio = MP3(filepath, ID3=ID3)
        if audio.tags and "APIC:" in audio.tags:
            apic = audio.tags["APIC:"]
            new_art = process_image(apic.data)
            if new_art != apic.data:
                audio.tags["APIC:"] = APIC(
                    encoding=3, mime="image/jpeg", type=3, desc="Cover", data=new_art
                )
                audio.save()
        else:
            print(" No album art.")
    elif ext == ".flac":
        audio = FLAC(filepath)
        if audio.pictures:
            new_art = process_image(audio.pictures[0].data)
            if new_art != audio.pictures[0].data:
                audio.pictures[0].data = new_art
                audio.pictures[0].mime = "image/jpeg"
                audio.save()
        else:
            print(" No album art.")
    elif ext == ".m4a":
        audio = MP4(filepath)
        if "covr" in audio.tags:
            new_art = process_image(audio.tags["covr"][0])
            if new_art != audio.tags["covr"][0]:
                audio.tags["covr"] = [MP4Cover(new_art, imageformat=MP4Cover.FORMAT_JPEG)]
                audio.save()
        else:
            print(" No album art.")
    elif ext == ".wav":
        print(f" Skipping WAV file (no standard embedded artwork support)")

def process_folder(root_folder):
    """Recursively process all audio files in a folder"""
    print("Checking album art:")
    for root, _, files in os.walk(root_folder):
        for file in files:
            if os.path.splitext(file)[1].lower() in AUDIO_EXTENSIONS:
                print(f"- {file}...", end='', flush=True)
                filepath = os.path.join(root, file)
                process_audio_file(filepath)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        music_folder = sys.argv[1]
    else:
        music_folder = input("Enter the music folder path: ").strip()
    
    if not os.path.isdir(music_folder):
        print("Error: Provided path is not a valid directory.")
        sys.exit(1)
    
    process_folder(music_folder)
