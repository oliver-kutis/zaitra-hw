import numpy as np
import rasterio
from typing import List, Dict, Optional, Any, Tuple


def load_tile(
        tile_path: str, orig_coords: Optional[Dict[str, Any]] = None,
        dtype: type = np.uint16, bands: List[int] = None
) -> np.ndarray:
    """
    Load image from a tile

    Args:
        tile_path: Path to the tile
        orig_coords: Original coordinates of the tile in the subscene
        dtype: Data type of the image
        bands: List of bands to load
    Returns:
        Image as numpy array
    """
    img, _ = load_tile_tif(tile_path, bands)

    if orig_coords:
        img = img[:orig_coords['row_end']-orig_coords['row_start'],
                  :orig_coords['col_end']-orig_coords['col_start'],
                  :
                  ]

    img = img.astype(dtype)

    return img


def load_tile_tif(
    tile_path: str,
    bands: List[int] = None
) -> Tuple[np.ndarray, rasterio.profiles.Profile]:
    """
    Load image with geospatial information

    Args:
        tile_path: Path to the tile
        bands: List of bands to load

    Returns:
        Tuple of image and rasterio profile

    """
    with rasterio.open(tile_path, 'r') as img:
        profile = img.profile
        img = img.read(bands)
        img = np.moveaxis(img, 0, -1)
        return img, profile
