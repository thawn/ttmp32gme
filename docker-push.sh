#!/bin/bash
docker tag ttmp32gme thawn/ttmp32gme
docker push thawn/ttmp32gme
echo "now create a version tag and push that one:"
echo "docker tag ttmp32gme thawn/ttmp32gme:version-1.0.1"
echo "docker push thawn/ttmp32gme:version-1.0.1"
