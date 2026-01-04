"""Tests for production flag and Waitress integration."""

import subprocess
import time


class TestProductionFlag:
    """Test --production flag and Waitress server."""

    def test_dev_server_shows_warning(self):
        """Test that dev server shows warning in verbose mode."""
        # Start dev server (without --production)
        proc = subprocess.Popen(
            [
                "python",
                "-m",
                "ttmp32gme.ttmp32gme",
                "--host=127.0.0.1",
                "--port=10030",
                "--no-browser",
                "-v",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Wait for server to start and capture initial output
        time.sleep(3)
        proc.terminate()
        output, _ = proc.communicate(timeout=5)

        # Check for development server warning
        assert (
            "WARNING: This is a development server" in output
        ), "Dev server should show warning"
        assert "werkzeug" in output.lower(), "Warning should come from werkzeug"

    def test_production_server_no_warning(self):
        """Test that production server does not show warning."""
        # Start production server (with --production)
        proc = subprocess.Popen(
            [
                "python",
                "-m",
                "ttmp32gme.ttmp32gme",
                "--host=127.0.0.1",
                "--port=10031",
                "--no-browser",
                "--production",
                "-v",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Wait for server to start and capture initial output
        time.sleep(3)
        proc.terminate()
        output, _ = proc.communicate(timeout=5)

        # Check that no development server warning is present
        assert (
            "WARNING: This is a development server" not in output
        ), "Production server should not show warning"
        # Check that Waitress is running
        assert (
            "Starting production server" in output or "Serving on" in output
        ), "Should use Waitress"

    def test_production_flag_in_help(self):
        """Test that --production flag appears in help."""
        result = subprocess.run(
            ["python", "-m", "ttmp32gme.ttmp32gme", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, "Help should succeed"
        assert "--production" in result.stdout, "Help should mention --production flag"
        assert (
            "wsgi server" in result.stdout.lower()
        ), "Help should explain production flag"
