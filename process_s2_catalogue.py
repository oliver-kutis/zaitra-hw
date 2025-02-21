import glob
import os
from dotenv import load_dotenv
from s2_processor.processor import Subscene, Mask
from s2_processor.metadata import TileMetadata, DatasetMetadata

# Load env variables
load_dotenv()
# Inputs
INPUT_SUBSCENE_DIR = os.getenv("INPUT_SUBSCENE_DIR")
INPUT_MASK_DIR = os.getenv("INPUT_MASK_DIR")
INPUT_CLASSIF_TAGS = os.getenv("INPUT_CLASSIF_TAGS")
SHAPEFILE_DIR = os.getenv("SHAPEFILE_DIR")
TILE_SIZE = (int(os.getenv("TILE_SIZE_X")), int(os.getenv("TILE_SIZE_Y")))
print(TILE_SIZE)
FIRST_N = int(os.getenv("FIRST_N"))
# Outputs
OUTPUT_SUBSCENE_DIR = os.getenv("OUTPUT_SUBSCENE_DIR")
OUTPUT_MASKS_DIR = os.getenv("OUTPUT_MASKS_DIR")
OUTPUT_METADATA_SUBSCENES_DIR = os.getenv("OUTPUT_METADATA_SUBSCENES_DIR")
OUTPUT_METADATA_DIR = os.getenv("OUTPUT_METADATA_DIR")


# Get the files
subscenes = glob.glob(f"{INPUT_SUBSCENE_DIR}/*.npy")[:FIRST_N]
masks = glob.glob(f"{INPUT_MASK_DIR}/*.npy")[:FIRST_N]

# Create dataset-level metadata
dataset_metadata = DatasetMetadata()
dataset_metadata.save(OUTPUT_METADATA_DIR)

# Process each subscene and mask
for subscene_path, mask_path in zip(subscenes, masks):
    subscene_f = os.path.basename(subscene_path)
    mask_f = os.path.basename(mask_path)
    # Create subscene and mask objects
    subscene = Subscene(
        INPUT_SUBSCENE_DIR,
        subscene_f,
        INPUT_CLASSIF_TAGS,
        shapefile_dir=SHAPEFILE_DIR,
        tile_size=TILE_SIZE)
    mask = Mask(INPUT_MASK_DIR, mask_f, TILE_SIZE)

    # Save tranformed tiles
    subscene.save_subscene_tiles_geo(OUTPUT_SUBSCENE_DIR)
    mask.save_mask(OUTPUT_MASKS_DIR)

    # Generate tile-metadata on subscene level
    metadata = TileMetadata(subscene, mask)
    metadata.save(OUTPUT_METADATA_SUBSCENES_DIR)
