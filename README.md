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
  * **Python (Recommended)**:
     * Install Python 3.11 or higher
     * Clone this repository: `git clone https://github.com/thawn/ttmp32gme.git && cd ttmp32gme`
     * Install dependencies: `pip install -e .`
     * Install [tttool](https://github.com/entropia/tip-toi-reveng#installation)
     * Run: `ttmp32gme` or `python -m ttmp32gme.ttmp32gme`
     * Open http://localhost:10020 in your browser
  * docker (also recommended):
     * Using the provided installer: download (right click and save as...) [install.sh](https://raw.githubusercontent.com/thawn/ttmp32gme/master/build/docker/install.sh) and [ttmp32gme](https://raw.githubusercontent.com/thawn/ttmp32gme/master/build/docker/ttmp32gme) into the same directory on our computer. 
       Run `sudo bash install.sh` in a terminal in the same directory where you saved the files. 
       Afterwards, you can start ttmp32gme with `ttmp32gme start` and stop it with `ttmp32gme stop`. 
       If your tiptoi is mounted but not recognized, you can add the tiptoi path to the start command: `ttmp32gme start /path/to/tiptoi`
     * Using docker directly: There is [a docker image on the docker hub](https://hub.docker.com/r/thawn/ttmp32gme). 
       Open the port to the ttmp32gme web interface by adding `--publish 8080:8080` to your `docker run` command. 
       You can specify where the library should be stored by adding `--volume ~/.ttmp32gme:/var/lib/ttmp32gme`. 
       Also, you can make a mounted tiptoi accessible by adding `--volume /tiptoi/mount/point:/mnt/tiptoi`. 
       
       A complete docker run command could look like this: `docker run -d --rm --publish 8080:8080 --volume ~/.ttmp32gme:/var/lib/ttmp32gme --volume /media/${USER}/tiptoi:/mnt/tiptoi --name ttmp32gme thawn/ttmp32gme:latest`
    
       Alternatively you can use [docker compose](https://docs.docker.com/compose/) and startup ttmp32gme with `docker-compse up` using the [docker-compose.yml](https://raw.githubusercontent.com/thawn/ttmp32gme/master/docker-compose.yml).

## Command Line Options

When running ttmp32gme from the command line, you can customize its behavior with the following options:

```bash
ttmp32gme [OPTIONS]
```

### Available Options

* `--port PORT`, `-p PORT`: Specify the server port (default: 10020)
* `--host HOST`: Specify the server host (default: 127.0.0.1)
* `--database DATABASE`: Path to custom database file (default: ~/.ttmp32gme/config.sqlite)
* `--library LIBRARY`: Path to custom library directory (default: ~/.ttmp32gme/library)
* `--debug`, `-d`: Enable debug mode
* `--version`, `-v`: Show version information

### Examples

Start server on a different port:
```bash
ttmp32gme --port 8080
```

Use custom database and library paths (useful for testing or multiple instances):
```bash
ttmp32gme --database /path/to/custom.sqlite --library /path/to/custom/library
```

Run on all network interfaces:
```bash
ttmp32gme --host 0.0.0.0 --port 8080
```

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

### Python Backend (Recommended)

ttmp32gme now includes a Python backend as an alternative to the Perl implementation.

#### Requirements

- Python 3.11 or higher
- tttool (see installation instructions below)
- Optional: ffmpeg (for OGG format support)
- Optional: wkhtmltopdf 0.13.x (for PDF generation on Linux)

#### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/thawn/ttmp32gme.git
   cd ttmp32gme
   ```

2. Install Python dependencies (recommended: use [uv](https://github.com/astral-sh/uv)):
   ```bash
   # Using uv (recommended - faster)
   uv pip install -e .
   
   # Or using pip
   pip install -e .
   ```

3. Install tttool following the [tttool installation instructions](https://github.com/entropia/tip-toi-reveng#installation)

4. Optional: Install ffmpeg for OGG support:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # On macOS
   brew install ffmpeg
   ```

#### Running ttmp32gme (Python)

```bash
# Run with default settings (localhost:10020)
python -m ttmp32gme.ttmp32gme

# Or use the entry point
ttmp32gme

# Run with custom port
ttmp32gme --port 8080

# Run with custom host
ttmp32gme --host 0.0.0.0 --port 8080

# Show help
ttmp32gme --help
```

Now you should be able to access the ttmp32gme user interface at http://localhost:10020 using your web browser.

## Web Links
* [tttool home page](http://tttool.entropia.de/)
* [tttool manual](https://tttool.readthedocs.io/de/latest/)
* [ttaudio](https://github.com/sidiandi/ttaudio/)
* [scienceblogs.de article on astrodicticum-simplex](http://scienceblogs.de/astrodicticum-simplex/2018/03/15/die-sternengeschichten-als-hoerbuch-auf-dem-tiptoi-stift/)
* [Caschys Blog](https://stadt-bremerhaven.de/tiptoi-stift-eigene-hoerspiele-und-musik-mit-ttmp32gme/)
* [It Dad](https://it-dad.de/2019/01/24/eigene-tiptoi-hoerbuecher-und-alben/)
* [TipToi Fahrzeugerkundung der Kinderfeuerwehr](https://www.ffrh.de/tiptoi-projekt/)


## Testing

ttmp32gme includes tests for the web frontend to ensure code quality and reliability.

### Running JavaScript Tests

JavaScript tests are written using Jest and test the utility functions in `print.js`.

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run tests with coverage report
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Running Python Tests

Python integration tests verify that the web pages and assets load correctly.

```bash
# Install test dependencies
pip install -e .

# Run tests
pytest tests/ -v

# Run tests with HTML report
pytest tests/ -v --html=report.html --self-contained-html
```

### Continuous Integration

All tests run automatically on GitHub Actions for pull requests and pushes to main branches:
- **JavaScript tests**: Run on Node.js 18.x and 20.x
- **Python tests**: Run on Python 3.11, 3.12, and 3.13


## Web Links
* [tttool home page](http://tttool.entropia.de/)
* [tttool manual](https://tttool.readthedocs.io/de/latest/)
* [ttaudio](https://github.com/sidiandi/ttaudio/)
* [scienceblogs.de article on astrodicticum-simplex](http://scienceblogs.de/astrodicticum-simplex/2018/03/15/die-sternengeschichten-als-hoerbuch-auf-dem-tiptoi-stift/)
* [Caschys Blog](https://stadt-bremerhaven.de/tiptoi-stift-eigene-hoerspiele-und-musik-mit-ttmp32gme/)
* [It Dad](https://it-dad.de/2019/01/24/eigene-tiptoi-hoerbuecher-und-alben/)
* [TipToi Fahrzeugerkundung der Kinderfeuerwehr](https://www.ffrh.de/tiptoi-projekt/)


## ToDo

* add a download button to the web frontend that allows downloading the gme files if they were created
  * add a corresponding end-to-end test that first creates the gme and then downloads it
* change the docker setup in build/docker/ to work with the new python backend
  * base image: ignore ttmp32gme-deps, it is for the old perl setup. Instead use a modern, slim python container
  * set up the dependencies like it is done in .github/workflows/e2e-tests.yml but without the selenium testing dependencies (chrome and chromedriver)
  * take into account these pull requests for the perl installation: 
    * https://github.com/thawn/ttmp32gme/pull/70
    * https://github.com/thawn/ttmp32gme/pull/68
  * test the docker container if possible
* add pre-commit hooks that run code linter (ruff) and formatter (black)
* add sphinx documentation
  * auto-generate API documentation from docstrings in the code
  * thoroughly analyze README.md, the frontend help page and the entire code then write the documentation in a docs/ folder using markdown files
  * after you are done update the copilot-instructions.md file to reflect the current status of the project
* make sure upload supports .ogg files
* integrate ~~wkhtml2pdf~~ pdf creation by selenium + browser into frontend (via the save PDF button that is already on the print page) make sure the PDFs created by the browser version used work for OID printing (ideally PNG images are not changed in the PDF)
* save last selected albums in the browsers local storage
* import/migrate library from one computer to another - can already be done manually, needs documentation. GUI for this will not be done.




### Maybe later
* add and remove music files from library page
* automatic splitting of audio files as described [here.](https://stackoverflow.com/questions/36074224/how-to-split-video-or-audio-by-silent-parts)
* automatic download of cover images
* enable separate printing of oid codes/text and cover images
* run on a real webserver so that users can generate their gme files online (thanks to Joachim for the idea).
* per-track images
