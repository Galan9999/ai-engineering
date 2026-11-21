from pathlib import Path
from typing import Any

import yaml


class DataFileError(ValueError):
    pass


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise DataFileError(f"{path.name}: se esperaba un mapa YAML")
    return data
