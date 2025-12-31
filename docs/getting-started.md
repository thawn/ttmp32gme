# Getting Started

This guide will help you get started with ttmp32gme quickly.

## Overview

ttmp32gme is a tool that converts MP3/audio files into TipToi GME (for Ravensburger tiptoi®) files. The process involves four main steps:

1. Upload MP3/audio files
2. Configure album information
3. Generate GME files
4. Print control sheets and copy to TipToi pen

## Prerequisites

Before using ttmp32gme, you'll need:

* A TipToi pen
* MP3 or OGG audio files (music or audiobooks)
* A printer capable of at least 600 DPI (1200 DPI recommended)
* [tttool](https://github.com/entropia/tip-toi-reveng) installed on your system

## Basic Workflow

### 1. Add Audio Files

Navigate to the "Upload" page and add your MP3 files:

* Upload one album at a time
* Optionally add a cover image (JPEG or PNG)
* The system will automatically extract ID3 tag information

**Note**: Only upload files for a single album in one session to keep your library organized.

### 2. Configure Album Information

On the "Library" page:

* Review the automatically extracted album and track information
* Edit artist name, album title, or track titles if needed
* Choose player mode (music or audiobook)
* Select an OID (Object Identification) number for the album

The OID is a unique identifier (between 1-999) that links your printed control sheet to the GME file.

### 3. Generate GME Files

Once your album is configured:

1. Click the "Create GME" button
2. Wait for the conversion process to complete
3. The GME file will be created and stored in your library

The GME file contains the compressed audio and control scripts for the TipToi pen.

### 4. Print Control Sheets

Select albums to print from the library:

1. Choose one or more albums using checkboxes
2. Click "Print Selected"
3. A new page opens with printable control sheets
4. Configure print layout (see [Print Configuration](print-configuration.md) for details)
5. Print at 100% scale, no auto-scaling
6. Use highest quality settings (1200 DPI recommended)

### 5. Copy to TipToi Pen

Connect your TipToi pen to your computer:

1. The system will automatically detect the pen
2. Select albums in the library
3. Click "Copy selected to TipToi"
4. Wait for the operation to complete
5. Safely disconnect the pen when prompted

## Next Steps

* Learn more about [installation options](installation.md)
* Explore [print configuration options](print-configuration.md)
* Read the [troubleshooting guide](troubleshooting.md) if you encounter issues
* Check out the [usage guide](usage.md) for detailed instructions

## Quick Tips

* **Album Organization**: Keep albums organized by uploading one album at a time
* **Cover Images**: Album covers make printed sheets more attractive and easier to identify
* **OID Numbers**: Keep track of which OID numbers you've used to avoid conflicts
* **Print Quality**: Higher DPI produces more reliable OID code recognition
* **Test First**: Print a test page before printing many albums
