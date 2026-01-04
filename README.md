# ttmp32gme

Cross-platform tool to convert MP3/audio files into TipToi GME files playable on the TipToi pen. Generates printable control sheets with OID codes for music/audiobook playback control.

Inspired by the Windows tool [ttaudio](https://github.com/sidiandi/ttaudio), powered by [tttool](http://tttool.entropia.de/).

## Features

* Convert MP3/OGG to TipToi GME format
* Auto-generate printable control sheets with OID codes
* Flexible print layouts (list, tiles, CD booklet)
* Auto-extract ID3 tags and cover images
* Direct copy to TipToi pen when connected
* Cross-platform: Windows, macOS, Linux

## Quick Start

**Windows/macOS**: Download executable from [releases](https://github.com/thawn/ttmp32gme/releases), run, open http://localhost:10020

**Linux** (Python):
```bash
git clone https://github.com/thawn/ttmp32gme.git && cd ttmp32gme
uv pip install -e .  # Recommended; or: pip install -e .
ttmp32gme  # Opens at http://localhost:10020
```

**Podman** (docker alternative):
```bash
podman run -d --rm --publish 8080:8080 \
  --volume ~/.ttmp32gme:/var/lib/ttmp32gme \
  --name ttmp32gme thawn/ttmp32gme:latest
```

See [Installation Guide](https://thawn.github.io/ttmp32gme/installation.html) for detailed instructions and options.

## Basic Usage

1. **Upload**: Add MP3/OGG files (one album at a time)
2. **Configure**: Edit album info, select OID number, choose player mode
3. **Create GME**: Generate TipToi-compatible files
4. **Print**: Print control sheets with OID codes
5. **Copy**: Transfer GME files to connected TipToi pen

See [Usage Guide](https://thawn.github.io/ttmp32gme/usage.html) for detailed instructions.

## Command Line

```bash
ttmp32gme --port 8080              # Custom port
ttmp32gme --host 0.0.0.0           # Network access
ttmp32gme --library /path/to/lib   # Custom library
ttmp32gme -v                       # Increase verbosity (-v for INFO, -vv for DEBUG)
ttmp32gme --version                # Show version
ttmp32gme --help                   # Show all options
```

## Print Troubleshooting

**OID codes not recognized?**
1. Print at 100% scale (critical!)
2. Use 1200 DPI or higher
3. Test with [OID table](https://cloud.githubusercontent.com/assets/1308449/26282853/beefeec2-3e19-11e7-8413-86a26bb1b1b5.png)
4. If test fails: printer issue (try different printer/paper)
5. If test works: increase pixels per dot (3-4) in print config

See [Print Configuration](https://thawn.github.io/ttmp32gme/print-configuration.html) and [Troubleshooting](https://thawn.github.io/ttmp32gme/troubleshooting.html) for detailed help.

## Screenshots

### Print Layouts

**List**: Full details, 1-2 albums per page  
![list](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_list.jpg)

**Tiles**: Compact grid, many albums per page  
![tiles](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_tiles.jpg)

**CD Booklet**: Fits standard CD cases  
![booklet](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_cd-booklet.jpg)

**Print Configuration**  
![config](https://github.com/thawn/ttmp32gme/blob/master/src/assets/images/Screen_Shot_print-config.png)

## Documentation

[Comprehensive documentation available here](https://thawn.github.io/ttmp32gme/).

* [Getting Started](https://thawn.github.io/ttmp32gme/getting-started.html) - Quick introduction
* [Installation](https://thawn.github.io/ttmp32gme/installation.html) - Platform-specific instructions
* [Usage Guide](https://thawn.github.io/ttmp32gme/usage.html) - Complete feature guide
* [Print Configuration](https://thawn.github.io/ttmp32gme/print-configuration.html) - Print setup and troubleshooting
* [Troubleshooting](https://thawn.github.io/ttmp32gme/troubleshooting.html) - Common problems and solutions
* [Development](https://thawn.github.io/ttmp32gme/development.html) - Architecture and contribution guide
* [API Reference](https://thawn.github.io/ttmp32gme/api/index.html) - API documentation

Build documentation locally:
```bash
uv pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
# Or: pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
cd docs/ && make html
# Open docs/_build/html/index.html
```

## Resources

* [tttool](http://tttool.entropia.de/) - TipToi tool and manual
* [ttaudio](https://github.com/sidiandi/ttaudio/) - Windows alternative
* [TipToi Printing Guide](https://github.com/entropia/tip-toi-reveng/wiki/Printing)

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# All tests (includes E2E with Selenium)
pytest tests/ -v

# With coverage
pytest --cov=ttmp32gme
```

See [Development Guide](https://thawn.github.io/ttmp32gme/development.html) for details.

## Contributing

Contributions welcome! See [Contributing Guide](https://thawn.github.io/ttmp32gme/contributing.html) for workflow and guidelines.

## License

See [LICENSE](LICENSE) file.
