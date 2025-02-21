import os
import json
from typing import Dict, Any
from .processor import Subscene, Mask


class TileMetadata:
    def __init__(self, subscene: Subscene, mask: Mask):
        """
        Initialize TileMetadata with subscene and mask.

        Args:
            subscene: Subscene object containing subscene data.
            mask: Mask object containing mask data.
        """
        self.subscene = subscene
        self.mask = mask

    def _to_dict(
        self, subscene_tile: Dict[str, Any], mask_tile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert metadata to a python dictionary.

        Args:
            subscene_tile: Dictionary containing subscene tile data.
            mask_tile: Dictionary containing mask tile data.

        Returns:
            Dictionary containing combined metadata.
        """
        metadata = {
            "id": subscene_tile["id"],
            "image_filename": f"{subscene_tile['id']}.tif",
            "mask_filename": f"{mask_tile['id']}.npy",
            "product_id": self.subscene._get_product_id(),
            "original_coords": subscene_tile["original_coords"],
            "geospatial_bounds": subscene_tile["geospatial_bounds"],
            "cloud_coverage": mask_tile['cloud_coverage'],
        }
        return metadata

    def save(self, output_dir: str) -> None:
        """
        Save metadata to a json file.

        Args:
            output_dir: Directory to save the metadata file.
        """
        # Create ouput dir if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        subscene_md = {
            "id": self.subscene.id,
            "product_id": self.subscene._get_product_id(),
            "classification_tags": self.subscene.classif_data,
            "tiles": []
        }
        filepath = os.path.join(output_dir, f"{self.subscene.id}.json")
        for ix, subscene_tile in enumerate(self.subscene.tiles):
            mask_tile = self.mask.tiles[ix]
            metadata = self._to_dict(subscene_tile, mask_tile)
            subscene_md['tiles'].append(metadata)

            # filepath = f"{output_dir}/{metadata['id']}.json"
            # with open(filepath, "w") as f:
            #     json.dump(metadata, f, indent=4)

        with open(filepath, "w") as f:
            json.dump(subscene_md, f, indent=4)


class BandInfo:
    def __init__(self, band_id, name, center_wavelength, bandwidth, GSD):
        """
        Stores information about a spectral band.

        Args:
            band_id (str): Band identifier.
            name (str): Band name.
            center_wavelength (float): Wavelength in nm.
            bandwidth (float): Bandwidth in nm.
            GSD (float): Ground Sampling Distance in meters.
        """
        self.band_id = band_id
        self.name = name
        self.center_wavelength = center_wavelength
        self.bandwidth = bandwidth
        self.GSD = GSD

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert BandInfo to a dictionary.

        Returns:
            Dictionary representation of BandInfo.
        """
        return {
            "band_id": self.band_id,
            "name": self.name,
            "center_wavelength": self.center_wavelength,
            "bandwidth": self.bandwidth,
            "GSD": self.GSD
        }


class DatasetMetadata:
    """
    Sources:
    - https://www.earthdata.nasa.gov/data/instruments/sentinel-2-msi
    - https://hatarilabs.com/ih-en/how-many-spectral-bands-have-the-sentinel-2-images
    """
    S2A_BANDS = [
        BandInfo("B01", "Coastal aerosol", 442.7, 20, 60),
        BandInfo("B02", "Blue", 492.7, 65, 10),
        BandInfo("B03", "Green", 559.8, 35, 10),
        BandInfo("B04", "Red", 664.6, 30, 10),
        BandInfo("B05", "Vegetation Red Edge", 704.1, 14, 20),
        BandInfo("B06", "Vegetation Red Edge", 740.5, 14, 20),
        BandInfo("B07", "Vegetation Red Edge", 782.8, 19, 20),
        BandInfo("B08", "NIR", 832.8, 105, 10),
        BandInfo("B08A", "Vegetation Red Edge", 864.7, 21, 20),
        BandInfo("B09", "Water vapour", 945.1, 19, 60),
        BandInfo("B10", "SWIR - Cirrus", 1373.5, 29, 60),
        BandInfo("B11", "SWIR", 1613.7, 90, 20),
        BandInfo("B12", "SWIR", 2202.4, 174, 20)
    ]

    S2B_BANDS = [
        BandInfo("B01", "Coastal aerosol", 442.3, 20, 60),
        BandInfo("B02", "Blue", 492.3, 65, 10),
        BandInfo("B03", "Green", 558.9, 35, 10),
        BandInfo("B04", "Red", 664.9, 31, 10),
        BandInfo("B05", "Vegetation Red Edge", 703.8, 15, 20),
        BandInfo("B06", "Vegetation Red Edge", 739.1, 13, 20),
        BandInfo("B07", "Vegetation Red Edge", 779.7, 19, 20),
        BandInfo("B08", "NIR", 832.9, 104, 10),
        BandInfo("B08A", "Vegetation Red Edge", 864.0, 21, 20),
        BandInfo("B09", "Water vapour", 943.2, 20, 60),
        BandInfo("B10", "SWIR - Cirrus", 1376.9, 29, 60),
        BandInfo("B11", "SWIR", 1610.4, 94, 20),
        BandInfo("B12", "SWIR", 2185.7, 184, 20)
    ]

    def __init__(self):
        """
        Class to store / save metadata for the Sentinel-2 dataset.
        """
        self.class_mapping = {
            0: "CLEAR",
            1: "CLOUD",
            2: "CLOUD_SHADOW"
        }

    def to_dict(self, sensor: str) -> Dict[str, Any]:
        """
        Convert metadata to a dictionary for a specific sensor (S2A or S2B).

        Args:
            sensor: Sensor type ('S2A' or 'S2B').

        Returns:
            Dictionary containing metadata for the specified sensor.

        Raises:
            ValueError: If the sensor type is invalid.
        """
        if sensor == "S2A":
            bands = self.S2A_BANDS
        elif sensor == "S2B":
            bands = self.S2B_BANDS
        else:
            raise ValueError(
                f"Invalid sensor type '{sensor}'. Choose 'S2A' or 'S2B'.")

        return {
            "bands": [band.to_dict() for band in bands]
        }

    def save(self, output_dir: str) -> None:
        """
        Save metadata for both S2A and S2B simultaneously.

        Args:
            output_dir: Directory to save the metadata file.
        """
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, "dataset_metadata.json")

        metadata = {
            "sensors": {},
            "class_mapping": self.class_mapping,
        }
        for sensor in ["S2A", "S2B"]:
            sensor_metadata = self.to_dict(sensor)
            metadata["sensors"][sensor] = sensor_metadata

        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=4)


# # Example usage:
# metadata = DatasetMetadata()
# metadata.save_both("output")
