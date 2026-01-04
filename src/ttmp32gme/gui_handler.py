"""GUI status window for macOS application."""

import logging
import platform
import sys
import threading
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


class ServerStatusWindow:
    """A simple status window for displaying server information and shutdown control.

    This window is primarily used on macOS where .app bundles don't show console windows.
    It provides users with:
    - Server status information (URL, port)
    - A button to open the browser
    - A button to stop the server
    - Automatic shutdown when the window is closed
    """

    def __init__(self, host: str, port: int, shutdown_callback: Callable[[], None]):
        """Initialize the status window.

        Args:
            host: Server host address
            port: Server port number
            shutdown_callback: Function to call when server should be shut down
        """
        self.host = host
        self.port = port
        self.shutdown_callback = shutdown_callback
        self.root: Optional[tk.Tk] = None
        self.is_running = False
        self.logs_window: Optional[tk.Toplevel] = None
        self.logs_text: Optional[tk.Text] = None

    def create_window(self) -> None:
        """Create and configure the tkinter window."""
        self.root = tk.Tk()
        self.root.title("ttmp32gme Server")
        self.root.geometry("400x250")
        self.root.resizable(False, False)

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="wens")

        # Title label
        title_label = ttk.Label(
            main_frame, text="TipToi MP3 GME Converter", font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Server status section
        status_label = ttk.Label(
            main_frame, text="Server is running", font=("Helvetica", 12)
        )
        status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # URL display
        url = f"http://{self.host}:{self.port}/"
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=2, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=(0, 5))
        url_entry = ttk.Entry(url_frame, width=30)
        url_entry.insert(0, url)
        url_entry.config(state="readonly")
        url_entry.grid(row=0, column=1)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        # Open Browser button
        open_button = ttk.Button(
            button_frame, text="Open Browser", command=self.open_browser
        )
        open_button.grid(row=0, column=0, padx=(0, 5))

        # Show Logs button
        logs_button = ttk.Button(button_frame, text="Show Logs", command=self.show_logs)
        logs_button.grid(row=0, column=1, padx=(0, 5))

        # Stop Server button
        stop_button = ttk.Button(
            button_frame, text="Stop Server", command=self.on_close
        )
        stop_button.grid(row=0, column=2)

        # Info label at the bottom
        info_label = ttk.Label(
            main_frame,
            text="Close this window to stop the server",
            font=("Helvetica", 9),
            foreground="gray",
        )
        info_label.grid(row=4, column=0, columnspan=2, pady=(20, 0))

    def open_browser(self) -> None:
        """Open the default web browser to the application URL."""
        from ttmp32gme.build.file_handler import open_browser

        open_browser(self.host, self.port)

    def show_logs(self) -> None:
        """Open a window showing server logs."""
        if self.logs_window and tk.Toplevel.winfo_exists(self.logs_window):
            # Window already exists, just raise it
            self.logs_window.lift()
            self.logs_window.focus_force()
            return

        # Create logs window
        self.logs_window = tk.Toplevel(self.root)
        self.logs_window.title("Server Logs")
        self.logs_window.geometry("700x500")

        # Create frame for logs
        logs_frame = ttk.Frame(self.logs_window, padding="10")
        logs_frame.grid(row=0, column=0, sticky="nsew")
        self.logs_window.grid_rowconfigure(0, weight=1)
        self.logs_window.grid_columnconfigure(0, weight=1)

        # Create scrolled text widget for logs
        logs_text_frame = ttk.Frame(logs_frame)
        logs_text_frame.grid(row=0, column=0, sticky="nsew")
        logs_frame.grid_rowconfigure(0, weight=1)
        logs_frame.grid_columnconfigure(0, weight=1)

        # Text widget with scrollbar
        scrollbar = ttk.Scrollbar(logs_text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.logs_text = tk.Text(
            logs_text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
            bg="white",
            fg="black",
        )
        self.logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.logs_text.yview)

        # Buttons frame at bottom
        button_frame = ttk.Frame(logs_frame)
        button_frame.grid(row=1, column=0, pady=(10, 0))

        # Refresh button
        refresh_button = ttk.Button(
            button_frame, text="Refresh", command=self.refresh_logs
        )
        refresh_button.pack(side=tk.LEFT, padx=(0, 5))

        # Clear button
        clear_button = ttk.Button(
            button_frame, text="Clear", command=self.clear_logs_display
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 5))

        # Close button
        close_button = ttk.Button(
            button_frame, text="Close", command=self.logs_window.destroy
        )
        close_button.pack(side=tk.LEFT)

        # Load initial logs
        self.refresh_logs()

    def refresh_logs(self) -> None:
        """Refresh the logs display with latest logs from the server."""
        if not self.logs_text:
            return

        try:
            # Import here to avoid circular imports
            import json
            import urllib.request

            # Fetch logs from the server
            url = f"http://{self.host}:{self.port}/logs?lines=500"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("success"):
                    logs = data.get("logs", [])

                    # Clear current content
                    self.logs_text.delete("1.0", tk.END)

                    # Insert logs
                    if logs:
                        self.logs_text.insert("1.0", "\n".join(logs))
                        # Scroll to bottom
                        self.logs_text.see(tk.END)
                    else:
                        self.logs_text.insert("1.0", "No logs available yet.")
        except Exception as e:
            if self.logs_text:
                self.logs_text.delete("1.0", tk.END)
                self.logs_text.insert("1.0", f"Error fetching logs: {e}")

    def clear_logs_display(self) -> None:
        """Clear the logs display."""
        if self.logs_text:
            self.logs_text.delete("1.0", tk.END)
            self.logs_text.insert("1.0", "Logs cleared. Click Refresh to reload.")

    def on_close(self) -> None:
        """Handle window close event and shut down the server."""
        logger.info("Shutting down server from GUI...")
        self.is_running = False
        if self.root:
            self.root.quit()
            self.root.destroy()
        # Call the shutdown callback to stop the server
        self.shutdown_callback()

    def run(self) -> None:
        """Start the GUI main loop."""
        self.is_running = True
        self.create_window()
        if self.root:
            self.root.mainloop()


def should_use_gui() -> bool:
    """Determine if the GUI window should be used.

    Returns True if:
    - Running on macOS
    - Running from PyInstaller bundle
    - Not in development mode

    Returns:
        True if GUI should be used, False otherwise
    """
    return platform.system() == "Darwin" and getattr(sys, "frozen", False)


def run_server_with_gui(app: "Flask", host: str, port: int) -> None:
    """Run the Flask server in a background thread with GUI control.

    Args:
        app: Flask application instance
        host: Server host address
        port: Server port number
    """
    try:
        from waitress import serve  # type: ignore

        logger.info(f"Starting server on {host}:{port} in background thread")

        # Run waitress server (blocking call)
        # The daemon thread will be terminated when the main process exits
        serve(
            app,
            host=host,
            port=port,
            threads=8,
            channel_timeout=120,
            connection_limit=100,
        )
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server thread stopped")


def start_gui_server(
    app: "Flask", host: str, port: int, auto_open_browser: bool = True
) -> None:
    """Start the server with a GUI control window.

    This is the main entry point for running the application with GUI support.

    Args:
        app: Flask application instance
        host: Server host address
        port: Server port number
        auto_open_browser: Whether to automatically open the browser on start
    """

    def shutdown_callback():
        """Callback to shut down the server."""
        logger.info("Shutdown callback triggered")
        # Exit the process to ensure clean shutdown
        import os

        os._exit(0)

    # Start server in background thread
    server_thread = threading.Thread(
        target=run_server_with_gui, args=(app, host, port), daemon=True
    )
    server_thread.start()

    # Wait for server to start with health check
    import time
    import urllib.request

    max_retries = 10
    for i in range(max_retries):
        try:
            urllib.request.urlopen(f"http://{host}:{port}/", timeout=1)
            logger.info("Server ready")
            break
        except Exception:
            if i == max_retries - 1:
                logger.warning("Server may not be ready yet, continuing anyway")
            time.sleep(0.3)

    # Create and run GUI window
    status_window = ServerStatusWindow(host, port, shutdown_callback)

    # Auto-open browser if requested
    if auto_open_browser:
        status_window.open_browser()

    # Run GUI (blocking call)
    status_window.run()

    # Clean exit after GUI closes
    logger.info("Application shutdown complete")
