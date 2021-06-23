import argparse
import shutil
from pathlib import Path
from typing import Dict, List

from utils import make_dir_if_not_exists, path_to_str_local, read_pipeline_config


def create_dirs_per_region(
    listing: Dict[int, Dict[str, Path]], out_dir: Path
) -> Dict[int, Path]:
    dirs_per_region = dict()
    dir_name_template = "region_{region:03d}"
    for region in listing:
        dir_path = out_dir / dir_name_template.format(region=region)
        make_dir_if_not_exists(dir_path)
        dirs_per_region[region] = dir_path
    return dirs_per_region


def change_vals_to_keys(input_dict: dict) -> dict:
    vals_to_keys = dict()
    for key, val in input_dict.items():
        vals_to_keys[val] = key
    return vals_to_keys


def copy_segm_channels_to_out_dirs(
    data_dir: Path,
    listing: Dict[int, Dict[str, str]],
    segmentation_channels: Dict[str, str],
    dirs_per_region: Dict[int, Path],
):

    new_name_template = "reg{region:03d}_{segm_ch_type}.tif"
    segm_channel_map = dict()
    segm_ch_index = change_vals_to_keys(segmentation_channels)
    for region, channels in listing.items():
        segm_channel_map[region] = dict()
        for ch_name, ch_path in channels.items():
            if ch_name in segm_ch_index.keys():
                segm_ch_type = segm_ch_index[ch_name]
                new_name = new_name_template.format(
                    region=region, segm_ch_type=segm_ch_type
                )

                src = data_dir / ch_path
                dst = dirs_per_region[region] / new_name
                shutil.copy(src, dst)
                print("region:", region, "| channel:", ch_name, "| new_location:", dst)


def main(data_dir: Path, pipeline_config_path: Path):
    pipeline_config = read_pipeline_config(pipeline_config_path)

    segm_ch_out_dir = Path("/output") / "segmentation_channels"
    make_dir_if_not_exists(segm_ch_out_dir)

    listing = pipeline_config["dataset_map_all_channels"]

    segm_ch = pipeline_config["segmentation_channels"]

    segm_ch_dirs_per_region = create_dirs_per_region(listing, segm_ch_out_dir)

    copy_segm_channels_to_out_dirs(data_dir, listing, segm_ch, segm_ch_dirs_per_region)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, help="path to the dataset directory")
    parser.add_argument(
        "--pipeline_config", type=Path, help="path to dataset metadata yaml"
    )
    args = parser.parse_args()

    main(args.data_dir, args.pipeline_config)
