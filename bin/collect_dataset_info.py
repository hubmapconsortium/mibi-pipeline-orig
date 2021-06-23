import argparse
from pathlib import Path
from typing import Dict, List

import yaml
from dataset_path_arrangement import create_listing_for_each_region
from utils import make_dir_if_not_exists, path_to_str_local, save_pipeline_config


def read_meta(meta_path: Path) -> dict:
    with open(meta_path, "r") as s:
        meta = yaml.safe_load(s)
    return meta


def convert_all_paths_to_str(
    listing: Dict[int, Dict[str, Path]]
) -> Dict[int, Dict[str, str]]:
    all_ch_dirs = dict()
    for region, dir_path in listing.items():
        all_ch_dirs[region] = dict()
        for channel_name, ch_path in listing[region].items():
            all_ch_dirs[region][channel_name] = path_to_str_local(ch_path)
    return all_ch_dirs


def main(data_dir: Path, meta_path: Path):
    meta = read_meta(meta_path)
    segmentation_channels = meta["segmentation_channels"]

    listing = create_listing_for_each_region(data_dir)

    out_dir = Path("/output")
    make_dir_if_not_exists(out_dir)

    listing_str = convert_all_paths_to_str(listing)

    pipeline_config = dict()
    pipeline_config["segmentation_channels"] = segmentation_channels
    pipeline_config["dataset_map_all_channels"] = listing_str

    pipeline_config_path = out_dir / "pipeline_config.yaml"
    save_pipeline_config(pipeline_config, pipeline_config_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, help="path to the dataset directory")
    parser.add_argument("--meta_path", type=Path, help="path to dataset metadata yaml")
    args = parser.parse_args()

    main(args.data_dir, args.meta_path)
