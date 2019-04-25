FROM perl:slim

COPY --from=johannesfritsch/tttool /usr/local/bin/tttool /usr/local/bin

RUN apt-get update && apt-get install -y \
    gcc apt-utils \
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
COPY ../../src .
ENV APPDATA=/var/lib/ HOST=127.0.0.1 PORT=8080
RUN mkdir config ${APPDATA}/ttmp32gme /mnt/tiptoi

EXPOSE 8080

CMD [ "perl", "ttmp32gme.pl", "--debug", "--host=${HOST}", "--port=${PORT}", "--configdir=/ttmp32gme/config" ]
# HEALTHCHECK --interval=5m --timeout=3s \
  # CMD curl -f http://localhost:8080/ || exit 1