from setuptools import setup, find_packages


def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


setup(
    name="sentinel-2-cloud-mask-preprocessor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24",
        "rasterio>=1.4",
        "geopandas>=1.0",
        "python-dotenv>=1.0"
    ],
    # entry_points={
    #     "console_scripts": [
    #         # Define command-line scripts here
    #     ],
    # },
    author="Oliver Kutiš",
    author_email="analytika.oliver.kutis@gmail.com",
    description="A package for preprocessing Sentinel-2 "
    + "Cloud Mask dataset for ML training.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/oliver-kutis/zaitra-hw",
    python_requires=">=3.6",
)
