import json


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
            "original_coords": subscene_tile["coords"],
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
