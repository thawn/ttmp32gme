"""Unit tests for OID images download functionality."""

import io
import zipfile
from unittest.mock import patch

from PIL import Image


def test_download_oid_images_route_empty_cache(tmp_path):
    """Test download route returns 404 when no OID images exist."""
    from ttmp32gme.ttmp32gme import app

    # Mock get_oid_cache to return empty temp directory
    with patch("ttmp32gme.db_handler.DBHandler.get_oid_cache") as mock_get_oid_cache:
        empty_cache = tmp_path / "empty_oid_cache"
        empty_cache.mkdir()
        mock_get_oid_cache.return_value = empty_cache

        # Test the endpoint
        with app.test_client() as client:
            response = client.get("/download_oid_images")
            assert response.status_code == 404
            assert b"No OID images available" in response.data


def test_download_oid_images_route_with_images(tmp_path):
    """Test download route returns ZIP file when OID images exist."""
    from ttmp32gme.ttmp32gme import app

    # Create temp OID cache with test images
    test_cache = tmp_path / "test_oid_cache"
    test_cache.mkdir()

    # Create 3 test PNG files
    test_files = []
    for i in range(3):
        img = Image.new("RGB", (50, 50), color=(i * 80, 0, 0))
        img_path = test_cache / f"test-oid-{i}-10-1200-2.png"
        img.save(img_path, "PNG")
        test_files.append(img_path)

    # Mock get_oid_cache to return our test cache
    with patch("ttmp32gme.db_handler.DBHandler.get_oid_cache") as mock_get_oid_cache:
        mock_get_oid_cache.return_value = test_cache

        # Test the endpoint
        with app.test_client() as client:
            response = client.get("/download_oid_images")
            assert response.status_code == 200
            assert response.mimetype == "application/zip"

            # Verify ZIP contents
            zip_content = io.BytesIO(response.data)
            with zipfile.ZipFile(zip_content, "r") as zipf:
                file_list = zipf.namelist()
                assert len(file_list) == 3
                assert all(f.endswith(".png") for f in file_list)

                # Verify we have all expected files
                expected_names = {f.name for f in test_files}
                actual_names = set(file_list)
                assert expected_names == actual_names


def test_download_oid_images_route_filters_non_png(tmp_path):
    """Test download route only includes PNG files."""
    from ttmp32gme.ttmp32gme import app

    # Create temp OID cache with mixed files
    test_cache = tmp_path / "test_oid_cache"
    test_cache.mkdir()

    # Create PNG files
    for i in range(2):
        img = Image.new("RGB", (50, 50), color="red")
        img_path = test_cache / f"oid-{i}.png"
        img.save(img_path, "PNG")

    # Create non-PNG files (should be ignored)
    (test_cache / "readme.txt").write_text("test")
    (test_cache / "config.yaml").write_text("test: true")

    # Mock get_oid_cache
    with patch("ttmp32gme.db_handler.DBHandler.get_oid_cache") as mock_get_oid_cache:
        mock_get_oid_cache.return_value = test_cache

        # Test the endpoint
        with app.test_client() as client:
            response = client.get("/download_oid_images")
            assert response.status_code == 200

            # Verify only PNG files are in ZIP
            zip_content = io.BytesIO(response.data)
            with zipfile.ZipFile(zip_content, "r") as zipf:
                file_list = zipf.namelist()
                assert len(file_list) == 2
                assert all(f.endswith(".png") for f in file_list)
                assert "readme.txt" not in file_list
                assert "config.yaml" not in file_list
