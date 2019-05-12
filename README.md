# ttmp32gme
a platform independent tool (inspired by the [windows tool ttaudio](https://github.com/sidiandi/ttaudio) ) to create tiptoi gme files from mp3 files. Also creates a printable sheet to play the music.

## Features
* convert music/audiobook albums from mp3 to gme format playable with the tiptoi pen using [tttool](http://tttool.entropia.de/).
* automatic generation of control sheets that allow to control playback of music/audiobook.
* flexible print layouts for various applications (see [screenshots](#screenshots) below).
* Printing was tested to work with Chrome and Firefox on Mac Os and Microsoft Edge on Windows 10 (Chrome and Firefox do not print with high enough resolution on Win 10, Opera seems to work occasionally).
* Creation of printable PDFs on Windows systems.
* automatic readout of id3 tags to get album and track info (including embedded cover images).
* add cover images for nicer print layout.
* copy gme files to tiptoi if tiptoi is connected.

## Installation
* Mac/Win: download the executables from the [releases page](https://github.com/thawn/ttmp32gme/releases). Put them somewhere and run them. Open localhost:10020 with a browser of your choice (except Internet Explorer).
* linux: 
  * docker (recommended):
     * Using the provided installer: download (right click and save as...) [install.sh](https://raw.githubusercontent.com/thawn/ttmp32gme/master/build/docker/install.sh) and [ttmp32gme](https://raw.githubusercontent.com/thawn/ttmp32gme/master/build/docker/ttmp32gme) into the same directory on our computer. Run `sudo bash install.sh` in a terminal in the same directory where you saved the files. Afterwards, you can start ttmp32gme with `ttmp32gme start` and stop it with `ttmp32gme stop`. If your tiptoi is mounted but not recognized, you can add the tiptoi path to the start command: `ttmp32gme start /path/to/tiptoi`
     * Using docker directly: There is [a docker image on the docker hub](https://cloud.docker.com/repository/docker/thawn/ttmp32gme). Open the port to the ttmp32gme web interface by adding `--publish 8080:8080` to your `docker run` command. You can specify where the library should be stored by adding `--volume ~/.ttmp32gme:/var/lib/ttmp32gme`. Also, you can make a mounted tiptoi accessible by adding `--volume /tiptoi/mount/point:/mnt/tiptoi`. A complete docker run command could look like this: `docker run -d --rm --publish 8080:8080 --volume ~/.ttmp32gme:/var/lib/ttmp32gme --volume /media/${USER}/tiptoi:/mnt/tiptoi --name ttmp32gme thawn/ttmp32gme:latest`
  * native: run the perl sources (see [instructions](#required-libraries-and-perl-modules-for-running-ttmp32gme-from-source) below)

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

#### If the pen does not recognize the printed pages

It is a known (and sad) fact that the oid codes do not work with all printers. This is because the oid codes are very fine detailed patterns and need to be reproduced exactly by the printer. Many printers simply do not have a good enough resolution or their drivers mess around with the patterns during image processing. In the latter case, this can sometimes be circumvented by playing around with the print settings but sometimes, it simply does not work.

* Make sure to print at 100% scale. Do not use the "autoscaling" or "fit to paper" settings in your print dialog. 
* print in 1200dpi if possible, sometimes 600dpi seem to work, too
* play around with the quality settings, resolution, contrast
* use different paper
* try black-and-white versus color prints
* Try to set your print driver to Graphic/Image mode (some drivers mess up the oid patterns in text mode).
* If your driver does not have such a setting, try to convert the PDF to a 1200 dpi png and print that. 

Before [reporting any problem with the pen not recognizing printed pages](https://github.com/thawn/ttmp32gme/issues/11), please read the wiki page on printer support for tttool:
https://github.com/entropia/tip-toi-reveng/wiki/Printing

If possible, please try to print the oid table you can download below:

[oid-table](https://cloud.githubusercontent.com/assets/1308449/26282853/beefeec2-3e19-11e7-8413-86a26bb1b1b5.png) (borrowed from tttool).

When you point the pen at any of the patterns, it should say something like "Bitte installieren Sie erst die Audiodatei für dieses Produkt" or "Bitte berühre erst das Anschaltzeichen für dieses Produkt". Then at least the pen recognized that these are oid codes. If the pen does nothing, this likely means that your issue is unrelated to the software but is a problem with the printer.

If you still think it is a software issue, please report exactly (step by step) what you were doing and what (if any) messages the pen is saying, otherwise I cannot help you.

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


## Required libraries and perl modules (for running ttmp32gme from source)

### Required libraries
ttmp32gme requires the following libraries to run"
`libc6`, `libxml2`, `zlib`
on a debian (-based) system (including Ubuntu), you can install these by running:
`sudo apt-get install libc6-dev libxml2-dev zlib1g-dev`.

If you want to use the ogg format, you need `ffmpeg`:
`sudo apt-get install ffmpeg`.


On linux systems, pdfs can be created using wkhtmltopdf if version 0.13.x is found on the path (i.e. in /usr/local/bin or /usr/bin).

You also need to [install tttool](https://github.com/entropia/tip-toi-reveng#installation) and copy/link the resulting binary into your path.

### Required perl modules
Run `cpan -i` (or the equivalent tool from your distro such as g-cpan for gentoo) followed by the following
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
Text::Template
JSON::XS
URI::Escape
Getopt::Long
Perl::Version
DBI
DBIx::MultiStatementDo
Log::Message::Simple
Music::Tag::MP3
Music::Tag::OGG
Music::Tag::MusicBrainz
Music::Tag::Auto
MP3::Tag
Image::Info

### Running ttmp32gme from source

Once you have all the required perl modules installed, check out the git repository into a directory of your choice:
`git clone https://github.com/thawn/ttmp32gme.git`.

Then run the main ttmp32gme perl script:
`cd ttmp32gme/src`
`perl ttmp32gme.pl`.

Now you should be able to access the ttmp32gme user interface (http://localhost:10020) using your web browser.

### Build requirements (for building mac and windows binaries)

For building from source, you also need:

pp

## Web Links
* [tttool home page](http://tttool.entropia.de/)
* [tttool manual](https://tttool.readthedocs.io/de/latest/)
* [ttaudio](https://github.com/sidiandi/ttaudio/)
* [scienceblogs.de article on astrodicticum-simplex](http://scienceblogs.de/astrodicticum-simplex/2018/03/15/die-sternengeschichten-als-hoerbuch-auf-dem-tiptoi-stift/)
* [Caschys Blog](https://stadt-bremerhaven.de/tiptoi-stift-eigene-hoerspiele-und-musik-mit-ttmp32gme/)
* [It Dad](https://it-dad.de/2019/01/24/eigene-tiptoi-hoerbuecher-und-alben/)


## ToDo
* handle more than 10 tracks for CD booklet (two column track layout)
* upload multiple albums at once from the upload page
* add and remove music files from library page
* make library path configurable (already possible with docker by re-configuring the library volume)
* add a config option and/or a control button to stop playing after each song/repeat one song/repeat all songs. [Issue #24](https://github.com/thawn/ttmp32gme/issues/24)

### Maybe later
* automatic splitting of audio files as described [here.](https://stackoverflow.com/questions/36074224/how-to-split-video-or-audio-by-silent-parts)
* automatic download of cover images
* enable separate printing of oid codes/text and cover images
* interface to use external CD ripping tools such as fre:ac
* run on a real webserver so that users can generate their gme files online (thanks to Joachim for the idea).
* integrate wkhtml2pdf into docker image for linux
