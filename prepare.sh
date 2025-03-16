#!/bin/bash
mkdir venv
python -m venv venv
source venv/bin/activate
pip install plexapi
pip install unidecode
pip install mutagen
pip install pillow
pip install ffmpeg-python
pip install ffmpeg
pip install pydub
pip install audioop-lts
