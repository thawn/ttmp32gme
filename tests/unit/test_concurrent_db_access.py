"""Test concurrent database access to verify thread-safety fixes."""

import concurrent.futures
import tempfile
from pathlib import Path

import pytest

from ttmp32gme.db_handler import DBHandler


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DBHandler(str(db_path))
        db.initialize()
        yield db
        db.close()


def test_concurrent_config_reads(temp_db):
    """Test concurrent reads from config table."""

    def read_config():
        """Read configuration value multiple times."""
        results = []
        for _ in range(10):
            value = temp_db.get_config_value("version")
            results.append(value)
        return results

    # Execute multiple concurrent reads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(read_config) for _ in range(10)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    # Verify all reads succeeded and returned the expected value
    for result_list in results:
        assert len(result_list) == 10
        for value in result_list:
            assert value == "2.0.0"


def test_concurrent_fetchone_operations(temp_db):
    """Test concurrent fetchone operations."""

    def fetch_config_param(param):
        """Fetch a single config parameter."""
        results = []
        for _ in range(5):
            value = temp_db.get_config_value(param)
            results.append(value)
        return results

    # Execute concurrent reads of different parameters
    params = ["host", "port", "version", "open_browser", "tt_dpi"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_config_param, param) for param in params]
        results = {param: future.result() for param, future in zip(params, futures)}

    # Verify results
    assert all(v == "127.0.0.1" for v in results["host"])
    assert all(v == "10020" for v in results["port"])
    assert all(v == "2.0.0" for v in results["version"])


def test_concurrent_fetchall_operations(temp_db):
    """Test concurrent fetchall operations."""

    def fetch_all_config():
        """Fetch all config parameters."""
        results = []
        for _ in range(5):
            config = temp_db.get_config()
            results.append(len(config))
        return results

    # Execute concurrent reads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_all_config) for _ in range(10)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    # Verify all reads succeeded
    for result_list in results:
        assert len(result_list) == 5
        # Should have multiple config entries
        for count in result_list:
            assert count > 10


def test_concurrent_mixed_operations(temp_db):
    """Test mixed read operations happening concurrently."""

    def mixed_operations():
        """Perform a mix of different database operations."""
        results = []
        for i in range(5):
            # Alternate between different types of operations
            if i % 3 == 0:
                value = temp_db.get_config_value("version")
                results.append(("config_value", value))
            elif i % 3 == 1:
                config = temp_db.get_config()
                results.append(("config", len(config)))
            else:
                # Query script_codes table
                rows = temp_db.fetchall("SELECT * FROM script_codes LIMIT 5")
                results.append(("script_codes", len(rows)))
        return results

    # Execute concurrent mixed operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(mixed_operations) for _ in range(10)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    # Verify all operations completed successfully
    assert len(results) == 10
    for result_list in results:
        assert len(result_list) == 5


def test_concurrent_insert_and_read(temp_db):
    """Test concurrent inserts and reads to simulate real-world scenario."""

    # Insert some test albums first
    def insert_album(oid):
        """Insert a test album."""
        album_data = {
            "oid": oid,
            "album_title": f"Test Album {oid}",
            "album_artist": f"Test Artist {oid}",
            "num_tracks": 5,
            "path": f"/tmp/test_{oid}",
        }
        temp_db.write_to_database("gme_library", album_data)

    def read_albums():
        """Read all albums."""
        results = []
        for _ in range(3):
            rows = temp_db.fetchall("SELECT * FROM gme_library")
            results.append(len(rows))
        return results

    # First, insert albums concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        insert_futures = [
            executor.submit(insert_album, oid) for oid in range(1000, 1020)
        ]
        # Wait for inserts to complete
        for future in concurrent.futures.as_completed(insert_futures):
            future.result()

    # Then, read concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        read_futures = [executor.submit(read_albums) for _ in range(10)]
        results = [
            future.result() for future in concurrent.futures.as_completed(read_futures)
        ]

    # Verify reads succeeded
    for result_list in results:
        assert len(result_list) == 3
        # Should have 20 albums
        for count in result_list:
            assert count == 20


def test_get_oid_cache_concurrent(temp_db):
    """Test concurrent calls to get_oid_cache() which triggered the original issue."""

    # Set library path first
    temp_db.update_table_entry(
        "config", "param=?", ["library_path"], {"value": "/tmp/test_library"}
    )

    def get_cache_path():
        """Get OID cache path multiple times."""
        results = []
        for _ in range(10):
            cache_path = temp_db.get_oid_cache()
            results.append(str(cache_path))
        return results

    # Execute concurrent calls that originally caused the error
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(get_cache_path) for _ in range(20)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    # Verify all calls succeeded and returned the same path
    expected_path = "/tmp/test_library/.oid_cache"
    for result_list in results:
        assert len(result_list) == 10
        for path in result_list:
            assert path == expected_path
