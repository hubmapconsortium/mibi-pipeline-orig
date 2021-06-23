import argparse
import copy
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

import numpy as np
import tifffile as tif
from utils import path_to_str


def get_full_img_paths(input_channel_map: dict, data_dir: Path) -> Dict[str, Path]:
    ch_map = dict()
    for ch_name, ch_filename in input_channel_map.items():
        img_path = data_dir / ch_filename
        ch_map[ch_name] = img_path
    return ch_map


# --------- METADATA PROCESSING -----------


def get_image_dims(path: Path):
    with tif.TiffFile(path_to_str(path)) as TF:
        image_shape = list(TF.series[0].shape)
        image_dims = list(TF.series[0].axes)
    dims = ["Z", "Y", "X"]
    image_dimensions = dict()
    for d in dims:
        if d in image_dims:
            idx = image_dims.index(d)
            image_dimensions[d] = image_shape[idx]
        else:
            image_dimensions[d] = 1
    return image_dimensions


def get_ome_img_dims(channel_map: Dict[str, Path]) -> Dict[str, str]:
    channels_paths = list(channel_map.values())
    num_channels = len(channels_paths)
    first_channel_dims = get_image_dims(channels_paths[0])
    num_z_planes = (
        1 if first_channel_dims["Z"] == 1 else first_channel_dims["Z"] * num_channels
    )
    ome_img_dims = {
        "SizeT": str(1),
        "SizeZ": str(num_z_planes),
        "SizeC": str(num_channels),
        "SizeY": str(first_channel_dims["Y"]),
        "SizeX": str(first_channel_dims["X"]),
    }
    return ome_img_dims


def generate_channel_meta(channel_names: List[str], offset: int):
    channel_elements = []
    for i, channel_name in enumerate(channel_names):
        channel_attrib = {
            "ID": "Channel:0:" + str(offset + i),
            "Name": channel_name,
            "SamplesPerPixel": "1",
        }
        channel = ET.Element("Channel", channel_attrib)
        channel_elements.append(channel)
    return channel_elements


def generate_tiffdata_meta(ome_img_dims: Dict[str, str]):
    tiffdata_elements = []
    ifd = 0
    for t in range(0, int(ome_img_dims["SizeT"])):
        for c in range(0, int(ome_img_dims["SizeC"])):
            for z in range(0, int(ome_img_dims["SizeZ"])):
                tiffdata_attrib = {
                    "FirstT": str(t),
                    "FirstC": str(c),
                    "FirstZ": str(z),
                    "IFD": str(ifd),
                }
                tiffdata = ET.Element("TiffData", tiffdata_attrib)
                tiffdata_elements.append(tiffdata)
                ifd += 1
    return tiffdata_elements


def generate_default_pixel_attributes(image_path: Path) -> Dict[str, str]:
    with tif.TiffFile(path_to_str(image_path)) as TF:
        img_dtype = TF.series[0].dtype
    pixels_attrib = {
        "ID": "Pixels:0",
        "DimensionOrder": "XYZCT",
        "Interleaved": "false",
        "Type": img_dtype.name,
    }
    return pixels_attrib


def generate_ome_meta(
    channel_map: Dict[str, Path],
    ome_img_dims: Dict[str, str],
    pixels_attrib: Dict[str, str],
) -> str:
    proper_ome_attrib = {
        "xmlns": "http://www.openmicroscopy.org/Schemas/OME/2016-06",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://www.openmicroscopy.org/Schemas/OME/2016-06 http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd",
    }

    channel_names = list(channel_map.keys())
    ome_channels = generate_channel_meta(channel_names, offset=0)
    tiffdata_elements = generate_tiffdata_meta(ome_img_dims)

    ome_pixels_attrs = pixels_attrib.copy()
    ome_pixels_attrs.update(ome_img_dims)

    node_ome = ET.Element("OME", proper_ome_attrib)
    node_image = ET.Element("Image", {"ID": "Image:0", "Name": "default.tif"})
    node_pixels = ET.Element("Pixels", ome_pixels_attrs)

    for ch in ome_channels:
        node_pixels.append(ch)

    for td in tiffdata_elements:
        node_pixels.append(td)

    node_image.append(node_pixels)
    node_ome.append(node_image)

    xmlstr = ET.tostring(node_ome, encoding="utf-8", method="xml").decode("ascii")
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
    ome_meta = xml_declaration + xmlstr
    return ome_meta


# ------- IMAGE PROCESSING ------------


def save_img_list(input_path_list: List[Path], out_path: Path, ome_meta: str):
    img = tif.imread(path_to_str(input_path_list[0]))
    if len(img.shape) < 4:
        new_img_shape = (1, 1, img.shape[0], img.shape[1])
    else:
        new_img_shape = img.shape
    del img
    img_list = []
    for path in input_path_list:
        img = tif.imread(path_to_str(path))
        img_list.append(img.reshape(new_img_shape))
    img_stack = np.stack(img_list, axis=-4)
    del img_list
    with tif.TiffWriter(path_to_str(out_path), bigtiff=True) as TW:
        TW.write(
            img_stack, contiguous=True, photometric="minisblack", description=ome_meta
        )


def save_region(channel_map: Dict[str, Path], out_path: Path, ome_meta: str):
    ch_paths = list(channel_map.values())
    save_img_list(ch_paths, out_path, ome_meta)
    com_path = Path(os.path.commonpath(ch_paths))
    short_ch_paths = [str(ch_path.relative_to(com_path)) for ch_path in ch_paths]
    print("region dir:", com_path, "| src:", short_ch_paths, "| dst:", out_path)


def bundle_imgs_in_region(
    data_dir: Path, input_channel_map: Dict[str, str], out_path: Path
):
    print("Creating OME metadata")
    channel_map = get_full_img_paths(input_channel_map, data_dir)

    first_channel_name = list(channel_map.keys())[0]
    first_channel_path = channel_map[first_channel_name]

    pixels_attrib = generate_default_pixel_attributes(first_channel_path)
    ome_img_dims = get_ome_img_dims(channel_map)

    print("Processing images")
    ome_meta = generate_ome_meta(channel_map, ome_img_dims, pixels_attrib)
    save_region(channel_map, out_path, ome_meta)
