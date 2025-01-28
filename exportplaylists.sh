#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "No input provided. please pass in the plex token."
    exit 1
fi

token=$1
playlistfolder="/run/user/1000/gvfs/smb-share:server=192.168.103.7,share=media/Music/Playlists"
playlists=( # Maybe replace this with a --list, save to file, then read all playlist for uber automatic export
    "Persona"
    "Final Fantasy XIV and XVI"
    "Songe"
    "NieR"
    "prime weeb shit"
    "Monster Hunter"
    "The Best OSTs"
)

# parse all plists
for item in "${playlists[@]}"; do
    echo "Parsing $item"
    ./PlexPlaylistExport.py --host http://plex.jn --token $token \
        --playlist "$item" \
        --plex-music-root="/media/Music" \
        --replace-with-dir ".."
done

# dumb rename, ascii-ify didnt work very well for me
old_ext="m3u8"
new_ext="m3u"
for file in "out"/*."$old_ext"; do
    [ -e "$file" ] || continue
    new_file="${file%.$old_ext}.$new_ext"
    mv "$file" "$new_file"
    echo "Renamed: '$file' -> '$new_file'"
done

echo "Copying playlists to $playlistfolder"
cp out/* $playlistfolder/
