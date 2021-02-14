#!/bin/bash
#Public domain, Author: Thomas Bleher
set -e

if [ $# -ne 1 ]
then
    echo "Usage: process <mp3-file>" >&2
    echo "" >&2
    echo "Takes a podcast, makes the title the album and splits it into 2min chunks" >&2
    echo "requires mp3splt and id3v2 to be installed" >&2
    exit 1
fi

FILE=$1
BASE=$(basename "$FILE" .mp3)
# Extract v2 title from the file
TITLE=$(id3v2 -l "$FILE" | sed -nE 's/^(TIT2 \([^)]*\)): (.*)/\2/p')

TMPFILE=$(mktemp)
cp "$FILE" "$TMPFILE"
id3v2 -A "$TITLE" "$TMPFILE"
mp3splt -a -t 2.00 -o "$BASE-@n" -d "$BASE" "$TMPFILE"
rm "$TMPFILE"