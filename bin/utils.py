from pathlib import Path

import yaml


def make_dir_if_not_exists(dir_path: Path):
    if not dir_path.exists():
        dir_path.mkdir(parents=True)


def path_to_str(path: Path):
    return str(path.absolute().as_posix())


def path_to_str_local(path: Path):
    return str(path.as_posix())


def read_pipeline_config(config_path: Path):
    with open(config_path, "r") as s:
        config = yaml.safe_load(s)
    return config


def save_pipeline_config(config: dict, out_path: Path):
    with open(out_path, "w") as s:
        yaml.safe_dump(config, s)
