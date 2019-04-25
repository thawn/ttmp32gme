FROM thawn/ttmp32gme-deps
    
WORKDIR /ttmp32gme
COPY src .
ENV APPDATA=/var/lib/
RUN mkdir config ${APPDATA}/ttmp32gme /mnt/tiptoi

EXPOSE 8080

CMD perl ttmp32gme.pl --debug --host=0.0.0.0 --port=8080 --configdir=/ttmp32gme/config
# HEALTHCHECK --interval=5m --timeout=3s \
  # CMD curl -f http://localhost:8080/ || exit 1