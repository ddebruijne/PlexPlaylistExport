#!/bin/bash

scriptFilePath=$(realpath "$0")
scriptDirectory=$(dirname "$scriptFilePath")

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "No input provided. please pass in the plex token."
    exit 1
fi

token=$1
#playlistfolder="/run/media/danny/KINGSTON/Playlists/" # need trailing /
playlistfolder="out/Playlists/"
playlists=( # Maybe replace this with a --list, save to file, then read all playlist for uber automatic export
    "Persona"
    "Final Fantasy XIV and XVI"
    "Songe"
    "NieR"
    "prime weeb shit"
    "Monster Hunter"
    "The Best OSTs"
    "All Time Favorites v2"
    "Z_AlbumDownloader"
)

# parse all plists
for item in "${playlists[@]}"; do
    echo "Parsing $item"
    ./PlexPlaylistExport.py --host http://plex.jn --token $token \
        --playlist "$item" \
        --plex-music-root="/media/Music/Lidarr" \
        --replace-with-dir "../Music" \
        --fs-music-root "/run/user/1000/gvfs/smb-share:server=192.168.103.7,share=media/Music/Lidarr" \
        --out-dir "$playlistfolder" 
done

./ParseAlbumArt.py
echo "Job's done!"
