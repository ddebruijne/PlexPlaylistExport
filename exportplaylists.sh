#!/bin/bash

scriptFilePath=$(realpath "$0")
scriptDirectory=$(dirname "$scriptFilePath")

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "No input provided. please pass in the plex token."
    exit 1
fi

token=$1
playlistfolder="/run/media/danny/KINGSTON/Playlists/" # need trailing /
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
        --replace-with-dir ".." \
        --fs-music-root "/run/user/1000/gvfs/smb-share:server=192.168.103.7,share=media/Music" \
        --out-dir "$playlistfolder" 
done

## NOTE the commented stuff is only here for some folks.
## Beet renames files, so it wasnt useful for me :( 
## ill stick to copying as much of the library over as I can.

## dumb rename, ascii-ify didnt work very well for me
# old_ext="m3u8"
# new_ext="m3u"
# for file in "out"/*."$old_ext"; do
#     [ -e "$file" ] || continue
#     new_file="${file%.$old_ext}.$new_ext"
#     cp "$file" "$new_file"
#     echo "Copied: '$file' -> '$new_file'"
# done

echo "Job's done!"

## Export
# exportMusicDir="Lidarr"
# mkdir -p $exportMusicDir
# for file in "out"/*."$new_ext"; do
#     [ -e "$file" ] || continue
#     beet move -e -d $scriptDirectory/$exportMusicDir playlist:"$file"
# done
