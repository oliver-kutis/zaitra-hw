from rasterio.transform import from_origin
import rasterio
from csv import DictReader
import os
import os
import numpy as np


class BaseImage:
    "Base class for images"

    def __init__(self, input_dir: str, filename: str):
        self.input_dir = input_dir
        self.filename = filename
        self.image = np.load(f"{self.input_dir}/{self.filename}")

    def _get_image_id(self) -> str:
        """Extract the subscene id from the filename"""
        return self.filename.split(".")[0]

    def _pad_image(self):
        """ Pad image to make it divisible by the tile size """

        h, w, _ = self.image.shape
        pad_h = (self.tile_size[0] - (h %
                 self.tile_size[0])) % self.tile_size[0]
        pad_w = (self.tile_size[1] - (w %
                 self.tile_size[1])) % self.tile_size[1]

        # Zero-padding
        padded_image = np.pad(self.image,
                              ((0, pad_h), (0, pad_w), (0, 0)),
                              mode='constant', constant_values=0)

        return padded_image, (pad_h, pad_w)

    def _generate_tile_id(self, coords):
        """ Generate a unique tile id from its original image / mask coordinates 
        Args:
        tile_coords (dict): dictionary with the following keys:
            - row_start
            - row_end
            - col_start
            - col_end

        Returns:
        str: a unique tile id in the format 
            TL_RS{row_start_ix}_RE{row_end_ix}_CS{col_start_ix}_CE{col_end_ix}


        """
        return (
            f"{self.id}"
            + f"_TL_RS{coords['row_start']}"
            + f"_RE{coords['row_end']}"
            + f"_CS{coords['col_start']}"
            + f"_CE{coords['col_end']}"
        )

    def _tile_image(self):
        """ Split the padded image into non-overlapping tiles """
        image, (padding) = self._pad_image()

        pad_h, pad_w = padding
        orig_h, orig_w = image.shape[0] - pad_h, image.shape[1] - pad_w

        # Tiling
        tiles = []
        for i in range(0, image.shape[0], self.tile_size[0]):
            for j in range(0, image.shape[1], self.tile_size[1]):
                tile = image[i:i+self.tile_size[0], j:j+self.tile_size[1], :]
                # tiles.append(tile)

                # Calculate coordinates in original (non-padded) image space
                coords = {
                    "row_start": max(0, i),
                    "row_end": min(orig_h, i + self.tile_size[0]),
                    "col_start": max(0, j),
                    "col_end": min(orig_w, j + self.tile_size[1]),
                    "is_padded": (i + self.tile_size[0] > orig_h) or (j + self.tile_size[1] > orig_w)
                }

                tile = {
                    "id": self._generate_tile_id(coords),
                    "tile": tile,
                    "coords": coords
                }

                tiles.append(tile)

        return tiles

    def _generate_tile_ouput_path(self, output_dir, tile_id, extension):
        """ Generate the output path for a tile """
        return f"{output_dir}/{tile_id}.{extension}"


class Subscene(BaseImage):
    def __init__(self, subscene_dir, subscene_filename, classif_tags_filepath: str, tile_size: tuple[int] = (512, 512)):
        super().__init__(subscene_dir, subscene_filename)
        self.classif_tags_filepath = classif_tags_filepath
        self.tile_size = tile_size
        self.id = self._get_image_id()
        self.tiles = self._tile_image()
        self.classif_data = self._get_classif_data()

        # self.metadata = {
        #     "id": self._get_product_id(),
        #     "filename": self.filename,
        #     "classif_data": self._get_classif_data()
        # }

    def _extract_class_tags(self) -> list[dict]:
        """ Extract class tags from a CSV to list of dictionaries 

        Args:
        class_tags_file (str): path to the CSV file

        Returns:
        list: list of dictionaries with the content of the CSV file
        """

        with open(self.classif_tags_filepath, "r") as f:
            reader = DictReader(f)
            return list(reader)

    def _get_classif_data(self):
        """ Extract classification data from the CSV file """
        classif_tags = self._extract_class_tags()
        # search for the subscene id in the filename
        subscene_id = self._get_image_id()
        # filter the classification data for the subscene id
        return list(filter(lambda x: x["scene"] == subscene_id, classif_tags))[0]

    def _get_product_id(self):
        """ Extract the product id from the classification data """
        return self._get_classif_data()["scene"]

    def save_subscene_tiles(self, output_dir: str, out_dtype: type = np.uint16, pixel_size: tuple[int, int] = (10, 10), crs: str = "EPSG:4326"):
        """ Save the subscene tiles to a Cloud Optimized GeoTIFF """
        # Create ouput dir if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        for t in self.tiles:
            tile = t["tile"].astype(out_dtype)
            tile_id = t["id"]
            tile_coords = t["coords"]

            # TODO: Not sure if it's correctly handled here
            row_start = tile_coords['row_start'] * pixel_size[0]
            col_start = tile_coords['col_start'] * pixel_size[1]

            transform = from_origin(
                north=row_start,
                west=col_start,
                ysize=pixel_size[0],
                xsize=pixel_size[1],
            )

            h, w, c = tile.shape
            output_path = self._generate_tile_ouput_path(
                output_dir, tile_id, "tif")
            self.tiles
            # print(f"Saving tile to {output_path}")

            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=h,
                width=w,
                count=c,
                dtype=tile.dtype,
                crs=crs,
                transform=transform,
                tiled=True,
            ) as dataset:
                for i in range(c):
                    band = tile[:, :, i]
                    dataset.write_band(i+1, band)


class Mask(BaseImage):
    def __init__(self, mask_dir: str, mask_filename: str, tile_size: tuple[int, int] = (512, 512)):
        super().__init__(mask_dir, mask_filename)
        self.tile_size = tile_size
        self.id = self._get_image_id()
        self.tiles = self._tile_image()
        # self.metadata = {
        #     "id": self._get_image_id(),
        #     "filename": mask_filename,
        # }

    def save_mask(self, output_dir: str, out_dtype: type = np.uint8):
        """ Save the mask tiles to disk """
        # Create ouput dir if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        for ix, tile in enumerate(self.tiles):
            tile_id = tile["id"]
            tile_mask = tile["tile"]
            self.tiles[ix]['cloud_coverage'] = self._calculate_cloud_coverage(
                tile_mask)

            output_path = self._generate_tile_ouput_path(
                output_dir, tile_id, "npy")

            np.save(output_path, tile_mask.astype(out_dtype))

    def _calculate_cloud_coverage(self, mask) -> None:
        """
        Calculate cloud coverage percentage from one-hot encoded mask

        Args:
            mask: NumPy array of shape (H,W,3) with one-hot encoding
                [CLEAR, CLOUD, CLOUD_SHADOW]

        Returns:
            float: Proportion of cloud coverage (0-1)
        """

        # Get only the CLOUD channel (index 1)
        cloud_mask = mask[:, :, 1]

        # Calculate percentage
        total_pixels = cloud_mask.size
        cloud_pixels = np.sum(cloud_mask)
        cloud_percentage = (cloud_pixels / total_pixels)

        return float(cloud_percentage)
