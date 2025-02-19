import numpy as np
from numpy.typing import NDArray


def verify_tile_coordinates(original_image: NDArray, tiles: list[NDArray], coords: list[dict]) -> bool:
    """
    Verify tile coordinates by comparing tile content with original image regions

    Args:
        original_image: Original input image
        tiles: List of extracted tiles
        coords: List of coordinate dictionaries

    Returns:
        bool: True if all tiles match their original regions
    """
    for idx, (tile, coord) in enumerate(zip(tiles, coords)):
        # Get region from original image
        original_region = original_image[
            coord['row_start']:coord['row_end'],
            coord['col_start']:coord['col_end'],
            :
        ]

        # Get corresponding region from tile (excluding padding)
        tile_region = tile[:coord['row_end']-coord['row_start'],
                           :coord['col_end']-coord['col_start'],
                           :]

        if not np.array_equal(original_region, tile_region):
            print(f"\nMismatch found for tile {idx}:")
            print(f"Coordinates: {coord}")
            print(f"Original region shape: {original_region.shape}")
            print(f"Tile region shape: {tile_region.shape}")

            if original_region.shape != tile_region.shape:
                print("Shape mismatch!")
            else:
                diff = np.where(original_region != tile_region)
                print(f"Number of differing elements: {len(diff[0])}")
            return False

    return True
