#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "No input provided. please pass in the plex token."
    exit 1
fi

# Capture the input parameter
token=$1

./PlexPlaylistExport.py --host http://plex.jn --token $token \
    --playlist "Final Fantasy XIV and XVI" \
    --plex-music-root="/media/Music" \
    --replace-with-dir ".."

./PlexPlaylistExport.py --host http://plex.jn --token $token \
    --playlist "Persona" \
    --plex-music-root="/media/Music" \
    --replace-with-dir ".."
