import numpy as np


def pad_image(image, tile_size=512):
    """ Pad image to make it divisible by the tile size """
    pad_x = (tile_size - image.shape[0] % tile_size) % tile_size
    pad_y = (tile_size - image.shape[1] % tile_size) % tile_size
    padded_image = np.pad(
        image, ((0, pad_x), (0, pad_y), (0, 0)), mode='constant')
    return padded_image


def tile_image(image, tile_size=512):
    """ Split the padded image into non-overlapping tiles """
    padded_image = pad_image(image, tile_size)
    tiles = [padded_image[x:x+tile_size, y:y+tile_size]
             for x in range(0, padded_image.shape[0], tile_size)
             for y in range(0, padded_image.shape[1], tile_size)]
    return tiles
