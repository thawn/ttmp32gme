# ttmp32gme
a tool to create tiptoi gme files from mp3 files. Also creates a printable sheet to play the music.

## Installation
Mac/Win: download the executables from the (https://github.com/thawn/ttmp32gme/releases)[releases page]. Put them somewhere and run them. Open localhost:10020 with a browser of your choice (except Internet Explorer). Printing was tested to work with Chrome and Firefox.

## required perl modules (for running ttmp32gme from source)
EV
AnyEvent::HTTPD
Path::Class
Cwd
File::Basename
File::Find
List::MoreUtils
PAR
Encode
Text::Template;
JSON::XS;
URI::Escape;
Getopt::Long;
Perl::Version;
DBI;
DBIx::MultiStatementDo;
Log::Message::Simple
Music::Tag::MP3
Music::Tag::OGG
Music::Tag::MusicBrainz
Music::Tag::Auto
MP3::Tag
Image::Info

## ToDo
* enable sorting of albums by artist/title/genre in library and on printing page
* write better documentation.
* convert mp3->ogg if desired (mainly for older pens with limited memory)
* handle more than 10 tracks for CD booklet (two column track layout)
* upload multiple albums at once
* add and remove music files from library page
* interface to use external ripping tools such as fre:ac
