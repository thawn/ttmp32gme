# ttmp32gme
a platform independent tool (inspired by the [windows tool ttaudio](https://github.com/sidiandi/ttaudio) ) to create tiptoi gme files from mp3 files. Also creates a printable sheet to play the music.

## Features
* convert music/audiobook albums from mp3 to gme format playable with the tiptoi pen using [tttool](http://tttool.entropia.de/).
* automatic generation of control sheets that allow to control playback of music/audiobook.
* flexible print layouts for various applications (see [screenshots](#screenshots) below).
* Printing was tested to work with Chrome and Firefox on Mac Os and Microsoft Edge on Windows 10 (Chrome and Firefox do not print with high enough resolution on Win 10).
* automatic readout of id3 tags to get album and track info (including embedded cover images).
* add cover images for nicer print layout.
* copy gme files to tiptoi if tiptoi is connected.

## Installation
* Mac/Win: download the executables from the [releases page](https://github.com/thawn/ttmp32gme/releases). Put them somewhere and run them. Open localhost:10020 with a browser of your choice (except Internet Explorer).
* linux: run the perl sources (see [instructions](#required-perl-modules-for-running-ttmp32gme-from-source) below)

## Usage
### 1. Add mp3 files
Add one or more mp3 files on the "Upload" page. Only add one
album at a time.

### 2. Configure and create gme files</h4>
On the "Library" page, you can configure and create gme
files. Mp3 tag data of recently uploaded files will automatically be used to
pre-populate the artist, album title and track info.

### 3. Print the control page(s)
Once you choose to print one or more album from the library,
a new page will open that displays the albums and their tracks from the gme
files that you selected for printing.

You can customize the the print layout by clicking on "<span
class="glyphicon glyphicon-cog"></span> Configure print layout".

You can choose one of the three presets:

list
: A list layout that includes all album details.

tiles
: A tiled layout that includes only minimal album details and general controls that work with all albums.

CD booklet
: A layout that is optimized for printing CD booklets.

Alternatively, you can manually choose which parts (cover image, album
information, album control buttons, track list) to display, how many columns
should be used and how large each album should be when printed.</p>

You can also configure here which resolution should be used (in DPI) for
printing (start with the maximum resolution your printer can handle). And how
many pixels (in x and y direction) each dot of the OID code should use. Start
with a value of 2 (<a href="https://en.wikipedia.org/wiki/Nyquist%E2%80%93Shannon_sampling_theorem">read
this if you want to know why</a>). If you have problems with not recognized oid
codes, first try to increase the number of pixels to 3 or 4 and then try to
change the resolution setting.

### 4. Copy the gme files onto the tiptoi pen</h4>
Connect the tiptoi pen to your computer. If you do not see the button "Copy
selected to TipToi", reload the library page. Now select
the desired albums and click on "Copy selected to TipToi". Wait till the
operation completes and a message appears that tells you that it is safe to
disconnect the pen from the computer.

## Screenshots
### Print as detailed list
![list](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_list.jpg)

### Print as tiles (fits many albums on one page)
![tiles](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_tiles.jpg)

### Print as CD booklet (fits into standard CD cases)
![booklet](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_cd-booklet.jpg)

### Print configuration
![config](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_print-config.png)


## required perl modules (for running ttmp32gme from source)
run `cpan -i` (or the equivalent tool from your distro such as g-cpan for gentoo) followed by the following
modules (some modules required the `-f` flag to install on my Mac OS system):
 
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
* automatic download of cover images
* enable separate printing of oid codes/text and cover images
* handle more than 10 tracks for CD booklet (two column track layout)
* upload multiple albums at once from the upload page
* add and remove music files from library page
* interface to use external CD ripping tools such as fre:ac
* Run on a real webserver so that users can generate their gme files online (thanks to Joachim for the idea).
