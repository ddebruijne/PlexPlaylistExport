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
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4Cover
from mutagen.oggvorbis import OggVorbis
from PIL import Image
import io

# Supported audio extensions
AUDIO_EXTENSIONS = {".flac", ".m4a", ".mp3", ".wav"}

# Max size for artwork
MAX_SIZE = 512

def process_image(image_data):
    """Convert image to baseline JPEG and resize if needed"""
    with Image.open(io.BytesIO(image_data)) as img:
        # Convert to RGB (in case of PNG/transparency)
        img = img.convert("RGB")
        
        # Resize maintaining aspect ratio
        max_dim = max(img.size)
        if max_dim > MAX_SIZE:
            img.thumbnail((MAX_SIZE, MAX_SIZE))

        # Save as baseline JPEG
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, progressive=False)
        return output.getvalue()

def process_audio_file(filepath):
    """Process an audio file and update album art if necessary"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".mp3":
        audio = MP3(filepath, ID3=ID3)
        if audio.tags and "APIC:" in audio.tags:
            apic = audio.tags["APIC:"]
            new_art = process_image(apic.data)
            audio.tags["APIC:"] = APIC(
                encoding=3, mime="image/jpeg", type=3, desc="Cover", data=new_art
            )
            audio.save()
    elif ext == ".flac":
        audio = FLAC(filepath)
        if audio.pictures:
            new_art = process_image(audio.pictures[0].data)
            audio.pictures[0].data = new_art
            audio.pictures[0].mime = "image/jpeg"
            audio.save()
    elif ext == ".m4a":
        audio = MP4(filepath)
        if "covr" in audio.tags:
            new_art = process_image(audio.tags["covr"][0])
            audio.tags["covr"] = [MP4Cover(new_art, imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
    elif ext == ".wav":
        print(f"Skipping WAV file (no standard embedded artwork support): {filepath}")

def process_folder(root_folder):
    """Recursively process all audio files in a folder"""
    for root, _, files in os.walk(root_folder):
        for file in files:
            if os.path.splitext(file)[1].lower() in AUDIO_EXTENSIONS:
                filepath = os.path.join(root, file)
                print(f"Processing: {filepath}")
                process_audio_file(filepath)

# Set your folder path
music_folder = "out/"
process_folder(music_folder)
