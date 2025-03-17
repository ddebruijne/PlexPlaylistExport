#!/bin/bash
# example usage: ./exportplaylits.sh TOKEN DISKNAME
# TOKEN: comes from plex, if you view details on an item, then xml, the last param in the url is the token
# DISKNAME: name of the mounted volume.

set -e
SECONDS=0  # Start the timer

scriptFilePath=$(realpath "$0")
scriptDirectory=$(dirname "$scriptFilePath")

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "No plex token provided. Usage: ./exportplaylits.sh TOKEN DISKNAME"
    exit 1
fi
token=$1

if [ -z "$2" ]; then
    playlistfolder="$scriptDirectory/out/Playlists/"
else
    playlistfolder="/run/media/$USER/$2/Playlists/" # need trailing /
fi

playlists=(
    "Persona"
    "Final Fantasy XIV and XVI"
    "City Pop"
    "Songe"
    "NieR"
    "prime weeb shit"
    "Monster Hunter"
    "The anti-weeb"
    "All Time Favorites v2"
    "Neerlandsch"
    "Z_AlbumDownloader"
)

fsMusicRoot="/run/user/1000/gvfs/smb-share:server=192.168.103.7,share=media/Music/Lidarr"
if [ ! -d "$fsMusicRoot" ]; then
    echo "Error: Folder '$fsMusicRoot' does not exist."
    exit 1
fi

source venv/bin/activate

# parse all plists
total_playlists=${#playlists[@]}
counter=1
for item in "${playlists[@]}"; do
    echo "[$counter/$total_playlists] Parsing $item"
    python3 PlexPlaylistExport.py --host http://plex.jn --token $token \
        --playlist "$item" \
        --plex-music-root="/media/Music/Lidarr" \
        --replace-with-dir "../Music" \
        --fs-music-root "$fsMusicRoot" \
        --out-dir "$playlistfolder" 
    echo " "
    ((counter++))
done

python3 ParseAlbumArt.py "$playlistfolder../Music"
echo ""
python3 Normalize.py "$playlistfolder../Music"
echo "Jobs done! Took $SECONDS seconds."
