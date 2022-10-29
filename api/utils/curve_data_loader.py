import json
from pathlib import Path
from typing import Optional


def load_curve_data(asset: str) -> Optional[dict]:
    data_path = Path(f"data/cached_curves/{asset.lower()}.json")
    if not data_path.exists():
        return None
    with data_path.open("r") as f:
        data = json.load(f)
    return data
