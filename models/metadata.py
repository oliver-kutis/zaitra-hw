import json
from dataclasses import dataclass, asdict
from typing import List, Dict
from dataclasses import field
import geopandas as gpd


class TileMetadata:
    def __init__(self, subscene, mask):
        self.subscene = subscene
        self.mask = mask

    def _to_dict(self, subscene_tile, mask_tile):
        """ Convert metadata to a python dictionary """
        metadata = {
            "id": subscene_tile["id"],
            "image_filename": f"{subscene_tile['id']}.tif",
            "mask_filename": f"{mask_tile['id']}.tif",
            "product_id": self.subscene._get_product_id(),
            "original_coords": subscene_tile["original_coords"],
            "geospatial_bounds": subscene_tile["geospatial_bounds"],
            "cloud_coverage": mask_tile['cloud_coverage'],
        }
        return metadata

    def save(self, output_dir):
        """ Save metadata to a json file """
        for ix, subscene_tile in enumerate(self.subscene.tiles):
            mask_tile = self.mask.tiles[ix]
            metadata = self._to_dict(subscene_tile, mask_tile)
            filepath = f"{output_dir}/{metadata['id']}.json"
            with open(filepath, "w") as f:
                json.dump(metadata, f, indent=4)


@dataclass
class BandInfo:
    band_id: int
    name: str
    center_wavelength: float  # Wavelength in nm
    bandwidth: float          # Bandwidth in nm
    GSD: float                # Ground Sampling Distance in meters


@dataclass
class DatasetMetadata:
    class_mapping: Dict[int, str] = field(default_factory=lambda: {
        0: "CLEAR",
        1: "CLOUD",
        2: "CLOUD_SHADOW"
    })
    bands: List[BandInfo] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

    def save(self, output_path: str):
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def from_shapefile(cls, shapefile_path):
        """Extract band metadata from a shapefile."""
        gdf = gpd.read_file(shapefile_path)

        # Check if band metadata is stored as attributes
        if "Band_ID" not in gdf.columns:
            raise ValueError("Shapefile does not contain band metadata!")

        bands = []
        for _, row in gdf.iterrows():
            bands.append(BandInfo(
                band_id=int(row["Band_ID"]),
                name=row["Band_Name"],
                center_wavelength=float(row["Wavelength_nm"]),
                bandwidth=float(row["Bandwidth_nm"]),
                GSD=float(row["GSD_m"])
            ))

        return cls(bands=bands)
