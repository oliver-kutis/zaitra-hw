
# 1. Basics
This package is designed so that it pre-processes Senitnel-2 Cloud Mask Catalogue [(link)](https://zenodo.org/records/4172871)
data for future Machine Learning purposes.

---
**Table of contents:**
* [1. Basics](#1-basics)
* [2. Data](#2-data)
* [3. The package](#3-the-package)
    * [3.1 `processor.py`](#31-processorpy)
    * [3.2 `metadata.py`](#32-metadatapy)
---

## 1.1 Requirements
The package runs only on python >= 3.9

## 1.2 Installing the package
The package is currently available only on github. To install it run:
```bash
pip install git+https://github.com/oliver-kutis/zaitra-hw.git@0.1.0
```

## 1.3 Improrting the package
```python
# Import metadata classes
from s2_process.metadata import TileMetadata, DatasetMetadata
```

## 1.4. Example usage

You can find example script in `process_s2_catalogue.py`. To make the usage simpler, 
you can simply configure `.env` file as you can see in this repository where you
provide the necessary variables. 

> _The `FIRST_N` variable is important - you can test the package only on small sample of subscenes without waiting too long._

You can also test the outputs of the package by using the provided `tests/test.py` script. The tests should run only after you've processed some data. Thankfully, the script uses the same enviroment variables so you can simply run:
```bash 
python -m unittest discover -s <test-script-dir>
```


# 2. Data
Data was taken directly from the above linked website. To download it, run following
command in the terminal:
```bash
wget -O s2-data.zip https://zenodo.org/api/records/4172871/files-archive
```
In thix example, data is saved to s2-data.zip in current directory. 
You should of course unzip the data as well by running: `unzip s2-data.zip`. 

Create directory where you want to store the data. For me it would be equivalent to
running `mkdir -p ./data/raw` in my project directory.

Then navigate to the output dir with `cd s2-data` and unzip the contents:
```bash 
for file in *.zip; do
    unzip "$file" -d ../data/raw
done
```
You should also move the `classification_tags.csv` so run: 
```bash
mv classification_tags.csv ../data/raw
```

Now, your project structure could look something like this:
```
├── data
│   ├── raw
│       ├── alt_masks
│       ├── classification_tags.csv
│       ├── masks
│       ├── README.pdf
│       ├── shapefiles
│       ├── subscenes
│       └── thumbnails
├── s2-data.zip
```
You can safely delete the `s2-data.zip` if you want to.

# 3. The package 
Package consists only from 3 modules:
1. `processor.py` 
2. `metadata.py` 
3. `utils.py` 

> _The package assumes that the subscenes and masks are stored in `.npy` format._ 


## 3.1. `processor.py` 
This module contains classes which do the "heavy lifting" tasks. 
Specifically, it consists of 2 main classes: `Subscene` and `Mask`. Both classes are 
inherit methods from a common class called `BaseImage`. 
Below, we briefly examine the functionalities of the modules and classes. More in-depth
description can be found in the docstrings.

> _Saving files doesn't require you to create destination directories upfront if they don't exist._

### `BaseImage`
Contains common methods for loading `.npy` images, generating ids for tiles, 
image itself and most importantly for tiling and padding the images. 

Instance of each inheriting classes holds several attributes, such as:
* `tiles`: dictionary for storing tiles and their metadata
* `image`: the original image (`.npy` matrix)
* paths to the input data directories

> _Tiles IDs are generated based on their coordinates in the original subscene / mask and the ID of the subscene / mask._

### `Subscene`
This class contains additional logic for handling tiling and metadata generation 
of subscene data. 
The most important difference between subscenes and masks is that we can actually 
geo-reference the tiled data because we have the necessary shapefiles. 
We also compute tile's original coordinates within the subscene matrix. 

We use `rasterio` package to not only load the shapefiles (`.shp`) but to also save 
the data in geo-referenced format: GeoTiff (`.tif`). 

The subscene also contains classification metadata which are stored in `classif_data` 
dictionary. These data are obtained from the `classification_tags.csv` file. 

#### Usage:
In the example below, we provide the subscene class with the paths to source files.
The shapefile path can be omitted, in that case the resulting `.tif` is not geo-referenced.

```python
# class initialization
subscene = Subscene(
    subscene_dir="./data/raw/subscenes",
    subscene_filename="SUBSCENE_ID",
    classif_tags_filepath="./data/raw/classification_tags.csv",
    shapefile_dir="./data/raw/shapefiles/SUBSCENE_ID",
    tile_size=(<TILE_SIZE_X>, <TILE_SIZE_Y>)
)
# saving the tiles
subscene.save_subscene_tiles_geo(
    output_dir="./data/processed/subscenes",
    output_dtype=np.uint16
)
```
To later load the tiles, one could easily just use the `utils.py` module:
```python
img = load_tile(
    tile_path=<tile_path>, orig_coords=<metadata_coords>, dtype=np.uint16, bands=[1,2,3])
```
This example loads the tile image for RGB (or BGR to be specific) bands. With 
`np.uin16` dtype. The `orig_coords` argument is used to retrieve the data in same 
way as one would find them in the subscene. 

### `Mask` 
Masks are saved simply as tiled `.npy` files in the provided directory. The process is 
very similar to the subscene tiling process above. 
The mask class additionally calculates `cloud_coverage` for each tile. Cloud coverage is calculated as sum of `1s` for the `cloud` class map in the mask matrix (stored in 1st index of the 2nd-index dimension of the mask matrix) . 

We won't go into details on the usage and other specifics. You can find comprehensive
example in `process_s2_catalogue.py` file. 

## 3.2 `metadata.py` 
Classes in this module generate metadata for tiles and the entire dataset. 
Tiles' metadata are stored in `.json` files where each file is subscene-oriented with
tile metadata stored for each of the tiles in an array / list. 
This approach was taken because one typically searches for the subscene's data with
more ease. It would be less convinient to go from tiles to subscenes. For example, if one were 
to loop through all tiles, he would find references in X tiles related to only one subscene.

The metadata module contains 2 classes: `TileMetadata` and `DatasetMetadata`:
* `TileMetadata` is more complex and holds metadata subscene / mask 's tiles. 
* `DatasetMetadata` is simpler, as it only stores dataset-level metadata and can only 
be called once to generate them. 

> _For details on usage, refer to `process_s2_catalogue.py` example._

### `TileMetadata` 
The class accepts only two arguments upon initialization. The values for this arguments
are instances of `Subscene` and `Mask`. 
Both objects generate tiles and their metadata and this class is used mostly to formalize
them and save them in one piece. 

The metadata object is subscene based and contains:
- `id`: id of the subscene
- `product_id`: product id of the subscene (in this case it's the same)
- `classiciation_tags {}`: object with details from `classification_tags.csv`
- `tiles []`: array / list of tiles with:
    - `id`: tile id
    - `image_filename`: filename of the subscene tile
    - `mask_filename`: filename of the mask tile
    - `product_id`: the same as abovoe (subscene product id)
    - `original_coords {}`: object with original subscene coords
    - `geospatial_bound {}`: object with geospatial bounds
    - `cloud_coverage`: cloud coverage proportion (0-1) derived from mask tile


Below is an example of `S2A_MSIL1C_20180125T071151_N0206_R106_T41VPF_20180125T091423.json`:
```json
{
    "id": "SUBSCENE_ID",
    "product_id": "PRODUCT_ID",
    "classification_tags": {
        /*
            ...
        */
    },
    "tiles": [
        {
            "id": "TILE_ID",
            "image_filename": "SUBSCENE_TILE_FILENAME.tif",
            "mask_filename": "MASK_TILE_FILENAME.npy",
            "product_id": "PRODUCT_ID",
            "original_coords": {
                "row_start": 0,
                "row_end": 512,
                "col_start": 0,
                "col_end": 512,
                "is_padded": false
            },
            "geospatial_bounds": {
                "minx": 656760.0,
                "maxx": 668302.5440313112,
                "miny": 6586997.455968689,
                "maxy": 6598540.0
            },
            "cloud_coverage": 0.0
        },
        /*        
            ...
        */
    ]
```

### `DatasetMetadata` 
Dataset metadata is a simple object storing details about the sentinel-2 dataset.
Metadata are distinguished by the sensor id (S2A/B) because the bands contain minor differences. Each subscene's id contains the id of the sensor in the beginning and is therefore easy do derive the details for the bands for that subscene.

Specifically it stores:
- `class_mapping {}`: mapping of the classes for the masks which are stored in 3rd (2nd -index) dimension of the mask data. The classes are one-hot encoded and only one of them is `1` (`True`) at a time. This mapping refers to the list index (0th index refers to one-hot encoded value for `Clear`)
- `bands {}`: object containing details about the band
    - `band_id`: band id
    - `name`: band name
    - `center_wawelength`: wawelength in nm (nanometres)
    - `bandwith`: bandwith in nm (nanometres)
    - `GSD`: Ground Sampling Distance in m (metres)