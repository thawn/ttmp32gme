FROM perl

COPY --from=johannesfritsch/tttool /usr/local/bin/tttool /usr/local/bin

RUN apt-get update && apt-get install -y \
    libc6-dev \
    libxml2-dev \
    zlib1g-dev 

RUN cpan -T -i \
    EV \
    AnyEvent::HTTPD \
    Path::Class \
    Cwd \
    File::Basename \
    File::Find \
    List::MoreUtils \
    PAR \
    Encode \
    Text::Template \
    JSON::XS \
    URI::Escape \
    Getopt::Long \
    Perl::Version \
    DBI \
    DBIx::MultiStatementDo \
    Log::Message::Simple \
    Music::Tag::MP3 \
    Music::Tag::OGG \
    Music::Tag::MusicBrainz \
    Music::Tag::Auto \
    MP3::Tag \
    Image::Info \
    WebService::MusicBrainz::Artist \
    Locale::Country \
    Locale::Codes
    
WORKDIR /ttmp32gme
COPY . .
ENV APPDATA=/var/lib/
RUN mkdir config ${APPDATA}/ttmp32gme /mnt/tiptoi
RUN echo "/dev/disk/by-label/tiptoi /mnt/tiptoi vfat umask=0777,auto,flush 0 1" >> /etc/fstab
WORKDIR /ttmp32gme/src

EXPOSE 8080

CMD [ "perl", "ttmp32gme.pl", "--debug", "--host=0.0.0.0", "--port=8080", "--configdir=/ttmp32gme/config" ]
# HEALTHCHECK --interval=5m --timeout=3s \
  # CMD curl -f http://localhost:8080/ || exit 1