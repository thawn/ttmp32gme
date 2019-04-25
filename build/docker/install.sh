#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker must be installed and in your path. Please refer to your packet manager or https://docs.docker.com/install/ for how to install docker.  Aborting."; exit 1; }

chmod a+x ttmp32gme
target=/usr/local/bin

if [ -d "$target" ] && [[ :$PATH: == *:"${target}":* ]]; then
	cp ttmp32gme "$target"
else
	cp ttmp32gme /usr/bin
fi
echo "Successfully installed ttmp32gme."