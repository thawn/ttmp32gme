#/bin/bash
ttmp32gmeStorage=~/.ttmp32gme
mkdir -p ${ttmp32gmeStorage}

docker run -d \
    --publish 8080:8080 \
    --volume ${ttmp32gmeStorage}:/var/lib/ttmp32gme \
    --device /dev/disk/by-label/tiptoi:/dev/disk/by-label/tiptoi \
    --security-opt apparmor:unconfined --cap-add SYS_ADMIN \
    --name ttmp32gme \
    fabian/ttmp32gme:latest