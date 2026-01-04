"""Unit tests for build.file_handler module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from ttmp32gme.build.file_handler import (
    cleanup_filename,
    clear_album,
    delete_gme_tiptoi,
    get_default_library_path,
    get_executable_path,
    get_gmes_already_on_tiptoi,
    get_local_storage,
    make_new_album_dir,
    make_temp_album_dir,
    move_to_album,
    open_browser,
    remove_album,
    remove_temp_dir,
)


class TestFileHandler:
    """Test file handler utilities."""

    def test_get_local_storage(self):
        """Test getting local storage directory."""
        storage = get_local_storage()
        assert isinstance(storage, Path)
        assert storage.exists()

    def test_get_default_library_path(self):
        """Test getting default library path."""
        library = get_default_library_path()
        assert isinstance(library, Path)
        assert library.exists()
        assert library.name == "library"

    def test_make_temp_album_dir(self):
        """Test creating temporary album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            album_dir = make_temp_album_dir(1, library_path)

            assert album_dir.exists()
            assert album_dir.is_dir()
            assert "temp" in str(album_dir)
            assert "1" in str(album_dir)

    def test_make_new_album_dir(self):
        """Test creating new album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)
            album_dir = make_new_album_dir("Test Album", library_path)

            assert album_dir.exists()
            assert album_dir.is_dir()
            assert "Test Album" in album_dir.name or "Test_Album" in album_dir.name

    def test_make_new_album_dir_unique(self):
        """Test that duplicate album names get unique directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            library_path = Path(tmpdir)

            # Create first album
            album_dir1 = make_new_album_dir("Test Album", library_path)
            assert album_dir1.exists()

            # Create second album with same name
            album_dir2 = make_new_album_dir("Test Album", library_path)
            assert album_dir2.exists()

            # Should be different directories
            assert album_dir1 != album_dir2

    def test_cleanup_filename(self):
        """Test filename cleaning."""
        # Test with invalid characters
        assert cleanup_filename("test<file>name") == "test_file_name"
        assert cleanup_filename("test:file|name") == "test_file_name"
        assert cleanup_filename("normal_filename.mp3") == "normal_filename.mp3"
        assert cleanup_filename("Test<>File") == "Test__File"
        assert cleanup_filename("Normal_File.mp3") == "Normal_File.mp3"
        assert cleanup_filename("File:With|Invalid?Chars") == "File_With_Invalid_Chars"

    def test_get_executable_path_python(self):
        """Test finding Python executable (should always exist)."""
        python_path = get_executable_path("python3")
        # Python should be found in PATH
        assert python_path is not None or get_executable_path("python") is not None

    def test_get_executable_path_nonexistent(self):
        """Test with non-existent executable."""
        result = get_executable_path("nonexistent_executable_12345")
        assert result is None

    @patch("ttmp32gme.build.file_handler.platform.system")
    @patch("ttmp32gme.build.file_handler.os.environ")
    @patch("ttmp32gme.build.file_handler.os.access")
    @patch("ttmp32gme.build.file_handler.shutil.which")
    def test_get_executable_path_chrome_windows_program_files(
        self, mock_which, mock_access, mock_environ, mock_system
    ):
        """Test finding Chrome in Windows Program Files."""
        mock_system.return_value = "Windows"
        mock_which.return_value = None  # Not in PATH
        mock_access.return_value = True  # File is executable

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake Chrome executable in Program Files
            chrome_dir = Path(tmpdir) / "Google" / "Chrome" / "Application"
            chrome_dir.mkdir(parents=True)
            chrome_exe = chrome_dir / "chrome.exe"
            chrome_exe.write_text("fake chrome")

            # Mock environment to point to our temp directory
            mock_environ.get.side_effect = lambda key, default: {
                "ProgramFiles": str(tmpdir),
                "ProgramFiles(x86)": "C:\\Program Files (x86)",
                "LocalAppData": "C:\\Users\\TestUser\\AppData\\Local",
            }.get(key, default)

            result = get_executable_path("chrome")

            # Should find chrome.exe in Program Files
            assert result is not None
            assert "chrome.exe" in result
            assert str(chrome_exe) == result

    @patch("ttmp32gme.build.file_handler.platform.system")
    @patch("ttmp32gme.build.file_handler.os.environ")
    @patch("ttmp32gme.build.file_handler.os.access")
    @patch("ttmp32gme.build.file_handler.shutil.which")
    def test_get_executable_path_chromium_windows_localappdata(
        self, mock_which, mock_access, mock_environ, mock_system
    ):
        """Test finding Chromium in Windows LocalAppData."""
        mock_system.return_value = "Windows"
        mock_which.return_value = None  # Not in PATH
        mock_access.return_value = True  # File is executable

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake Chromium executable in LocalAppData
            chromium_dir = Path(tmpdir) / "Chromium" / "Application"
            chromium_dir.mkdir(parents=True)
            chromium_exe = chromium_dir / "chrome.exe"
            chromium_exe.write_text("fake chromium")

            # Mock environment to point to our temp directory
            mock_environ.get.side_effect = lambda key, default: {
                "ProgramFiles": "C:\\Program Files",
                "ProgramFiles(x86)": "C:\\Program Files (x86)",
                "LocalAppData": str(tmpdir),
            }.get(key, default)

            result = get_executable_path("chromium")

            # Should find chromium.exe in LocalAppData
            assert result is not None
            assert "chrome.exe" in result
            assert str(chromium_exe) == result

    @patch("ttmp32gme.build.file_handler.platform.system")
    @patch("ttmp32gme.build.file_handler.os.environ")
    @patch("ttmp32gme.build.file_handler.os.access")
    @patch("ttmp32gme.build.file_handler.shutil.which")
    def test_get_executable_path_google_chrome_windows_localappdata(
        self, mock_which, mock_access, mock_environ, mock_system
    ):
        """Test finding Chrome in Windows LocalAppData (per-user install)."""
        mock_system.return_value = "Windows"
        mock_which.return_value = None  # Not in PATH
        mock_access.return_value = True  # File is executable

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake Chrome executable in LocalAppData
            chrome_dir = Path(tmpdir) / "Google" / "Chrome" / "Application"
            chrome_dir.mkdir(parents=True)
            chrome_exe = chrome_dir / "chrome.exe"
            chrome_exe.write_text("fake chrome")

            # Mock environment to point to our temp directory
            mock_environ.get.side_effect = lambda key, default: {
                "ProgramFiles": "C:\\Program Files",
                "ProgramFiles(x86)": "C:\\Program Files (x86)",
                "LocalAppData": str(tmpdir),
            }.get(key, default)

            result = get_executable_path("google-chrome")

            # Should find chrome.exe in LocalAppData
            assert result is not None
            assert "chrome.exe" in result
            assert str(chrome_exe) == result

    @patch("ttmp32gme.build.file_handler.platform.system")
    @patch("ttmp32gme.build.file_handler.shutil.which")
    def test_get_executable_path_windows_uses_which(self, mock_which, mock_system):
        """Test that Windows still uses shutil.which for executables in PATH."""
        mock_system.return_value = "Windows"
        mock_which.return_value = "C:\\Windows\\System32\\cmd.exe"

        result = get_executable_path("cmd")

        # Should find cmd using shutil.which before checking common paths
        assert result == "C:\\Windows\\System32\\cmd.exe"
        mock_which.assert_called_once_with("cmd")

    def test_move_to_album(self):
        """Test moving files from temp to album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / "temp"
            album_dir = Path(tmpdir) / "album"

            temp_dir.mkdir()
            album_dir.mkdir()

            # Create some files in temp dir
            (temp_dir / "file1.txt").write_text("content1")
            (temp_dir / "file2.txt").write_text("content2")

            result = move_to_album(temp_dir, album_dir)

            assert result is True
            assert (album_dir / "file1.txt").exists()
            assert (album_dir / "file2.txt").exists()
            # Temp dir still exists but should be empty
            assert temp_dir.exists()
            assert len(list(temp_dir.iterdir())) == 0

    def test_remove_temp_dir(self):
        """Test removing temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / "temp_test"
            temp_dir.mkdir()

            (temp_dir / "file.txt").write_text("test")

            result = remove_temp_dir(temp_dir)

            assert result is True
            assert not temp_dir.exists()

    def test_remove_temp_dir_nonexistent(self):
        """Test removing non-existent directory."""
        result = remove_temp_dir(Path("/nonexistent/path"))
        assert result is False

    def test_clear_album(self):
        """Test clearing album directory contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            album_dir = Path(tmpdir) / "album"
            album_dir.mkdir()

            # Create some files
            (album_dir / "file1.txt").write_text("content")
            (album_dir / "file2.txt").write_text("content")

            result = clear_album(album_dir)

            assert result is True
            assert album_dir.exists()  # Directory still exists
            assert len(list(album_dir.iterdir())) == 0  # But is empty

    def test_remove_album(self):
        """Test removing album directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            album_dir = Path(tmpdir) / "album_to_remove"
            album_dir.mkdir()

            (album_dir / "file.txt").write_text("content")

            result = remove_album(album_dir)

            assert result is True
            assert not album_dir.exists()

    @patch("ttmp32gme.build.file_handler.get_tiptoi_dir")
    def test_get_gmes_already_on_tiptoi(self, mock_get_tiptoi):
        """Test getting list of GMEs on TipToi."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tiptoi_dir = Path(tmpdir)
            mock_get_tiptoi.return_value = tiptoi_dir

            # Create some GME files
            (tiptoi_dir / "album1.gme").write_bytes(b"fake gme")
            (tiptoi_dir / "album2.gme").write_bytes(b"fake gme")
            (tiptoi_dir / "readme.txt").write_text("not a gme")

            result = get_gmes_already_on_tiptoi()

            assert len(result) == 2
            assert "album1.gme" in result
            assert "album2.gme" in result
            assert "readme.txt" not in result

    @patch("ttmp32gme.build.file_handler.get_tiptoi_dir")
    def test_get_gmes_no_tiptoi(self, mock_get_tiptoi):
        """Test getting GMEs when TipToi not found."""
        mock_get_tiptoi.return_value = None

        result = get_gmes_already_on_tiptoi()

        assert result == []

    @patch("ttmp32gme.build.file_handler.get_tiptoi_dir")
    def test_delete_gme_tiptoi_success(self, mock_get_tiptoi):
        """Test deleting GME from TipToi."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tiptoi_dir = Path(tmpdir)
            mock_get_tiptoi.return_value = tiptoi_dir

            gme_file = tiptoi_dir / "album.gme"
            gme_file.write_bytes(b"fake gme")

            result = delete_gme_tiptoi("album.gme")

            assert result is True
            assert not gme_file.exists()

    @patch("ttmp32gme.build.file_handler.get_tiptoi_dir")
    def test_delete_gme_tiptoi_not_found(self, mock_get_tiptoi):
        """Test deleting GME when TipToi not found."""
        mock_get_tiptoi.return_value = None

        result = delete_gme_tiptoi("album.gme")

        assert result is False

    @patch("ttmp32gme.build.file_handler.platform.system")
    @patch("ttmp32gme.build.file_handler.os.access")
    @patch("ttmp32gme.build.file_handler.shutil.which")
    @patch("ttmp32gme.build.file_handler.Path.home")
    def test_get_executable_path_chrome_macos_user_applications(
        self, mock_home, mock_which, mock_access, mock_system
    ):
        """Test finding Chrome in macOS ~/Applications directory."""
        mock_system.return_value = "Darwin"
        mock_which.return_value = None  # Not in PATH
        mock_access.return_value = True  # File is executable

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home.return_value = Path(tmpdir)

            # Create fake Chrome.app structure in ~/Applications
            chrome_app = (
                Path(tmpdir)
                / "Applications"
                / "Google Chrome.app"
                / "Contents"
                / "MacOS"
            )
            chrome_app.mkdir(parents=True)
            chrome_exe = chrome_app / "Google Chrome"
            chrome_exe.write_text("fake chrome")
            # Make it executable
            chrome_exe.chmod(0o755)

            result = get_executable_path("google-chrome")

            # Should find Chrome in ~/Applications
            assert result is not None
            assert "Google Chrome" in result
            assert str(chrome_exe) == result

    @patch("ttmp32gme.build.file_handler.platform.system")
    @patch("ttmp32gme.build.file_handler.os.access")
    @patch("ttmp32gme.build.file_handler.shutil.which")
    @patch("ttmp32gme.build.file_handler.Path.home")
    def test_get_executable_path_chromium_macos_user_applications(
        self, mock_home, mock_which, mock_access, mock_system
    ):
        """Test finding Chromium in macOS ~/Applications directory."""
        mock_system.return_value = "Darwin"
        mock_which.return_value = None  # Not in PATH
        mock_access.return_value = True  # File is executable

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_home.return_value = Path(tmpdir)

            # Create fake Chromium.app structure in ~/Applications
            chromium_app = (
                Path(tmpdir) / "Applications" / "Chromium.app" / "Contents" / "MacOS"
            )
            chromium_app.mkdir(parents=True)
            chromium_exe = chromium_app / "Chromium"
            chromium_exe.write_text("fake chromium")
            # Make it executable
            chromium_exe.chmod(0o755)

            result = get_executable_path("chromium")

            # Should find Chromium in ~/Applications
            assert result is not None
            assert "Chromium" in result
            assert str(chromium_exe) == result

    @patch("ttmp32gme.build.file_handler.subprocess.run")
    @patch("ttmp32gme.build.file_handler.platform.system")
    def test_open_browser_linux(self, mock_system, mock_run):
        """Test opening browser on Linux."""
        mock_system.return_value = "Linux"

        result = open_browser("localhost", 8080)

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "xdg-open" in args
        assert "http://localhost:8080/" in args

    @patch("ttmp32gme.build.file_handler.subprocess.run")
    @patch("ttmp32gme.build.file_handler.platform.system")
    def test_open_browser_failure(self, mock_system, mock_run):
        """Test browser opening failure."""
        mock_system.return_value = "Linux"
        mock_run.side_effect = Exception("Failed")

        result = open_browser("localhost", 8080)

        assert result is False
