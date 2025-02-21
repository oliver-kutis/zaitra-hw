import os
import json
import glob
import numpy as np
import rasterio
import geopandas as gpd
import unittest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TestTileProcessing(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.TILE_SIZE = (int(os.getenv("TILE_SIZE_X")),
                         int(os.getenv("TILE_SIZE_Y")))
        cls.OUTPUT_SUBSCENE_DIR = os.getenv("OUTPUT_SUBSCENE_DIR")
        cls.OUTPUT_MASKS_DIR = os.getenv("OUTPUT_MASKS_DIR")
        cls.OUTPUT_METADATA_DIR = os.getenv("OUTPUT_METADATA_DIR")
        cls.SHAPEFILE_DIR = os.getenv("SHAPEFILE_DIR")
        cls.INPUT_SUBSCENE_DIR = os.getenv("INPUT_SUBSCENE_DIR")
        cls.OUTPUT_METADATA_SUBSCENES_DIR = os.getenv(
            "OUTPUT_METADATA_SUBSCENES_DIR")

    def test_generated_files(self):
        image_tiles = [f for f in os.listdir(
            self.OUTPUT_SUBSCENE_DIR) if f.endswith(".tif")]
        mask_tiles = [f for f in os.listdir(
            self.OUTPUT_MASKS_DIR) if f.endswith(".npy")]
        metadata_files = [f for f in os.listdir(
            self.OUTPUT_METADATA_DIR) if f.endswith(".json")]

        self.assertGreater(len(image_tiles), 0, "No image tiles saved.")
        self.assertGreater(len(mask_tiles), 0, "No mask tiles saved.")
        self.assertGreater(len(metadata_files), 0, "No metadata files saved.")
        self.assertEqual(len(image_tiles), len(mask_tiles),
                         "Mismatch between image and mask tiles!")

        print(
            f"Test 'test_generated_files': {len(image_tiles)} image tiles, "
            f"{len(mask_tiles)} mask tiles, {len(metadata_files)} metadata files."
        )

    def test_tile_dimensions(self):
        """
        Test if the generated tiles have the correct dimensions and number of bands.
        """
        tile_paths = glob.glob(f"{self.OUTPUT_SUBSCENE_DIR}/*.tif")
        passed = 0

        for tile_path in tile_paths:
            with rasterio.open(tile_path) as img:
                h, w = img.shape
                bands = img.count
                self.assertEqual(
                    (h, w), self.TILE_SIZE,
                    f"Incorrect tile size in {tile_path}: "
                    f"{h}x{w} instead of {self.TILE_SIZE}"
                )
                self.assertEqual(
                    bands,
                    13,
                    f"Incorrect number of bands in {tile_path}: {bands} instead of 13"
                )
                passed += 1

        print(
            f"Test 'test_tile_dimensions': {passed}/{len(tile_paths)} tiles passed."
        )

    def test_geospatial_coordinates(self):
        """
        Test if the generated tiles have the geospatial information.
        """
        tile_paths = glob.glob(f"{self.OUTPUT_SUBSCENE_DIR}/*.tif")
        passed = 0

        for tile_path in tile_paths:
            with rasterio.open(tile_path) as img:
                self.assertIsNotNone(img.crs, f"CRS missing in {tile_path}")
                self.assertIsNotNone(
                    img.transform, f"Transform missing in {tile_path}")
                passed += 1

        print(
            f"Test 'test_geospatial_coordinates': "
            f"{passed}/{len(tile_paths)} tiles passed."
        )

    def test_geospatial_bounds(self):
        """
        Test if the generated tiles are within the original subscene coordinates.
        """
        tile_paths = glob.glob(f"{self.OUTPUT_SUBSCENE_DIR}/*.tif")
        passed = 0

        for tile_path in tile_paths:
            shapefile_name = os.path.basename(tile_path).split("_TL")[0]
            shapefile_path = os.path.join(
                f"{self.SHAPEFILE_DIR}/{shapefile_name}/{shapefile_name}.shp")

            gdf = gpd.read_file(shapefile_path)

            with rasterio.open(tile_path) as img:
                minx, miny, maxx, maxy = img.bounds
                tile_top_left = gpd.GeoDataFrame(
                    geometry=gpd.points_from_xy([minx], [maxy]), crs=gdf.crs)

                is_inside = gdf.geometry.iloc[0].covers(
                    tile_top_left.geometry.iloc[0])
                if not is_inside:
                    is_inside = gdf.geometry.iloc[0].buffer(
                        1e-3).contains(tile_top_left.geometry.iloc[0])

                self.assertTrue(
                    is_inside, f"Tile {tile_path} is outside the original subscene!")
                passed += 1

        print(
            f"Test 'test_geospatial_bounds': {passed}/{len(tile_paths)} tiles passed."
        )

    def test_metadata_accuracy(self):
        """
        Test if the metadata files contain the correct tile ids.
        """
        metadata_files = glob.glob(
            f"{self.OUTPUT_METADATA_SUBSCENES_DIR}/*.json")
        passed = 0

        for metadata_path in metadata_files:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            for tile in metadata['tiles']:
                image_file = f"{self.OUTPUT_SUBSCENE_DIR}/{tile['id']}.tif"
                mask_file = f"{self.OUTPUT_MASKS_DIR}/{tile['id']}.npy"
                self.assertTrue(os.path.exists(image_file),
                                f"Missing image tile for {tile['id']}")
                self.assertTrue(os.path.exists(mask_file),
                                f"Missing mask tile for {tile['id']}")
                passed += 1

        print(
            "Test 'test_metadata_accuracy':"
            + f"{passed}/{len(metadata_files)} metadata files passed."
        )

    def test_cloud_coverage(self):
        """
        Test if the cloud coverage in the metadata files matches
        the actual cloud coverage in the mask.
        """
        mask_paths = glob.glob(f"{self.OUTPUT_MASKS_DIR}/*.npy")
        passed = 0

        for mask_path in mask_paths:
            mask = np.load(mask_path)
            mask_md_path = mask_path.split("_TL")[0] + ".npy"

            cloud_mask = mask[:, :, 1]
            cloud_coverage = np.sum(cloud_mask) / cloud_mask.size

            metadata_path = (
                f"{self.OUTPUT_METADATA_SUBSCENES_DIR}/"
                f"{os.path.basename(mask_md_path).replace('.npy', '.json')}"
            )
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                for tile in metadata['tiles']:
                    if tile['id'] == os.path.basename(mask_path).replace(".npy", ""):
                        self.assertAlmostEqual(
                            tile["cloud_coverage"],
                            cloud_coverage,
                            places=4, msg=f"Cloud coverage mismatch in {metadata_path}"
                        )
                        passed += 1

        print(
            f"Test 'test_cloud_coverage': {passed}/{len(mask_paths)} masks passed."
        )

    def test_tile_original_coordinates(self):
        """
        Test if the generated tiles have the
        correct original coordinates from the subscene.
        """
        metadata_files = glob.glob(
            f"{self.OUTPUT_METADATA_SUBSCENES_DIR}/*.json")
        errors = 0
        total_tiles = 0

        for metadata_path in metadata_files:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            subscene_id = metadata["id"]
            subscene_image = os.path.join(
                self.INPUT_SUBSCENE_DIR, f"{subscene_id}.npy")
            subscene = np.load(subscene_image).astype(np.uint16)

            for ix, tile in enumerate(metadata['tiles']):
                total_tiles += 1
                tile_id = tile["id"]
                original_coords = tile["original_coords"]

                row_start = original_coords["row_start"]
                row_end = original_coords["row_end"]
                col_start = original_coords["col_start"]
                col_end = original_coords["col_end"]

                with rasterio.open(f"{self.OUTPUT_SUBSCENE_DIR}/{tile_id}.tif") as img:
                    actual_tile = img.read().astype(np.uint16)
                    actual_tile = np.moveaxis(actual_tile, 0, -1)
                    actual_tile = actual_tile[:row_end - row_start,
                                              :col_end - col_start,
                                              :]

                subscene_tile_region = subscene[row_start:row_end,
                                                col_start:col_end, :]

                if not np.array_equal(subscene_tile_region, actual_tile):
                    errors += 1

                if not np.array_equal(subscene_tile_region.shape, actual_tile.shape):
                    errors += 1

        self.assertEqual(
            errors, 0, f"Found {errors} tiles with incorrect original coordinates!")
        print(
            "Test 'test_tile_original_coordinates':"
            + f"{total_tiles - errors}/{total_tiles} tiles passed."
        )


if __name__ == "__main__":
    unittest.main()
