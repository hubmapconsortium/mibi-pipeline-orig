import argparse
import shutil
from pathlib import Path
from typing import Dict

from bundle_images import bundle_imgs_in_region
from utils import make_dir_if_not_exists, read_pipeline_config


def collect_segm_masks(data_dir: Path, listing: dict, out_dir: Path):
    img_name_template = "reg{region:03d}_mask.ome.tiff"
    dir_name_template = "region_{region:03d}"
    for region, channels in listing.items():
        out_reg_dir = out_dir / dir_name_template.format(region=region)
        make_dir_if_not_exists(out_reg_dir)
        src = (
            data_dir
            / dir_name_template.format(region=region)
            / img_name_template.format(region=region)
        )
        dst = out_reg_dir / img_name_template.format(region=region)
        shutil.copy(src, dst)
        print("region:", region, "| src:", src, "| dst:", dst)


def collect_expr(data_dir: Path, listing: Dict[int, Dict[str, str]], out_dir: Path):
    out_name_template = "reg{region:03d}_expr.ome.tiff"
    out_dir_name_template = "region_{region:03d}"

    for region in listing:
        channel_map = listing[region]
        out_reg_dir = out_dir / out_dir_name_template.format(region=region)
        make_dir_if_not_exists(out_reg_dir)
        out_path = out_reg_dir / out_name_template.format(region=region)
        bundle_imgs_in_region(data_dir, channel_map, out_path)


def main(data_dir: Path, mask_dir: Path, pipeline_config_path: Path):
    pipeline_config = read_pipeline_config(pipeline_config_path)
    listing = pipeline_config["dataset_map_all_channels"]

    out_dir = Path("/output/pipeline_output")
    mask_out_dir = out_dir / "mask"
    expr_out_dir = out_dir / "expr"
    make_dir_if_not_exists(mask_out_dir)
    make_dir_if_not_exists(expr_out_dir)

    print("collecting segmentation masks")
    collect_segm_masks(mask_dir, listing, mask_out_dir)
    print("collecting expressions")
    collect_expr(data_dir, listing, expr_out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=Path, help="path to directory with images")
    parser.add_argument(
        "--mask_dir", type=Path, help="path to directory with segmentation masks"
    )
    parser.add_argument(
        "--pipeline_config", type=Path, help="path to region map file YAML"
    )
    args = parser.parse_args()

    main(args.data_dir, args.mask_dir, args.pipeline_config)
