"""Helper script to download public domain test files for E2E testing."""

import urllib.request
from pathlib import Path

# Create fixtures directory
fixtures_dir = Path(__file__).parent
fixtures_dir.mkdir(exist_ok=True)

# Download small public domain audio files
test_files = {
    # Very short silent MP3 (public domain)
    'test_audio.mp3': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    # Small test image (placeholder)
    'test_cover.jpg': 'https://via.placeholder.com/300x300.jpg?text=Test+Cover',
}

print("Downloading test files for E2E testing...")
for filename, url in test_files.items():
    filepath = fixtures_dir / filename
    if not filepath.exists():
        try:
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"✓ Downloaded {filename}")
        except Exception as e:
            print(f"✗ Failed to download {filename}: {e}")
    else:
        print(f"✓ {filename} already exists")

print("\nTest files ready!")
