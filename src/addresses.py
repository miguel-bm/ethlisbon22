from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict

ADDRESSES_PATH = Path("data/addresses.json")

with ADDRESSES_PATH.open("r") as f:
    addresses_data: dict = json.load(f)

MULTICALL_ADDRESSES = addresses_data["multicallAddress"]
