A docker image for ttmp32gme.

Set the environment variable `HOST=0.0.0.0` to make ttmp32gme accessible to other computers in your network.

```
docker run -d \
	--rm \
	--publish 8080:8080 \
	--volume ${ttmp32gmeStorage}:/var/lib/ttmp32gme \
	--volume </path/to/tiptoi:/mnt/tiptoi \
	-env HOST=127.0.0.1 \
	-env PORT=8080 \
	--name ttmp32gme \
	thawn/ttmp32gme:latest
```
