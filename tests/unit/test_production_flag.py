"""Tests for dev flag and production server behavior."""

import subprocess
import time


def _start_server_and_capture_output(args, timeout=5, wait_for_warning=False):
    """Helper to start server, wait for output, and terminate.

    Args:
        args: Command line arguments for the server
        timeout: Seconds to wait before terminating
        wait_for_warning: If True, wait longer for Flask warning message

    Returns:
        str: Combined stdout and stderr output
    """
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server to start - check output for readiness
    start_time = time.time()
    output_lines = []
    server_ready = False
    warning_found = False

    while time.time() - start_time < timeout:
        line = proc.stdout.readline()
        if line:
            output_lines.append(line)
            # Server is ready when we see "Serving" or "Running"
            if "Serving" in line or "Running" in line:
                server_ready = True
            # Check for warning if requested
            if wait_for_warning and "WARNING" in line:
                warning_found = True
                break
        # If server is ready and we're not waiting for warning, we can break
        if server_ready and not wait_for_warning:
            break
        time.sleep(0.1)

    # Wait a bit more to capture any additional output (especially warnings)
    if server_ready and wait_for_warning and not warning_found:
        # Give Flask more time to emit its warning
        additional_wait = 2.0
        end_wait = time.time() + additional_wait
        while time.time() < end_wait:
            line = proc.stdout.readline()
            if line:
                output_lines.append(line)
                if "WARNING" in line:
                    warning_found = True
                    break
            time.sleep(0.1)

    # Terminate and get remaining output
    proc.terminate()
    remaining_output, _ = proc.communicate(timeout=5)
    if remaining_output:
        output_lines.append(remaining_output)

    return "".join(output_lines)


class TestDevFlag:
    """Test --dev flag and production server default behavior."""

    def test_default_uses_production_server(self):
        """Test that production server is used by default (no --dev flag)."""
        args = [
            "python",
            "-m",
            "ttmp32gme.ttmp32gme",
            "--host=127.0.0.1",
            "--port=10030",
            "--no-browser",
            "-v",
        ]
        output = _start_server_and_capture_output(args)

        # Check that production server is used
        assert (
            "Starting production server" in output or "Serving on" in output
        ), "Should use Waitress by default"
        # Check that no development server warning is present
        assert (
            "WARNING: This is a development server" not in output
        ), "Production server should not show warning"

    def test_dev_flag_shows_warning(self):
        """Test that dev server shows warning when --dev flag is used."""
        args = [
            "python",
            "-m",
            "ttmp32gme.ttmp32gme",
            "--host=127.0.0.1",
            "--port=10031",
            "--no-browser",
            "--dev",
            "-v",
        ]
        output = _start_server_and_capture_output(
            args, timeout=7, wait_for_warning=True
        )

        # Check for development server warning
        assert (
            "WARNING: This is a development server" in output
        ), "Dev server should show warning with --dev flag"
        assert "werkzeug" in output.lower(), "Warning should come from werkzeug"
        assert (
            "Starting Flask development server" in output
        ), "Should indicate Flask dev server"

    def test_dev_flag_in_help(self):
        """Test that --dev flag appears in help."""
        result = subprocess.run(
            ["python", "-m", "ttmp32gme.ttmp32gme", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, "Help should succeed"
        assert "--dev" in result.stdout, "Help should mention --dev flag"
        assert (
            "development server" in result.stdout.lower()
        ), "Help should explain dev flag"
