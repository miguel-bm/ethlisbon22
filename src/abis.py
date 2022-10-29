from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict

ABI_PATH = Path("data/abis.json")


@dataclass
class AbiCollection:
    erc20: list
    comptroller: list
    cToken: list
    multicall: list
    oneInchOracle: list
    compoundOracle: list


def get_abis() -> AbiCollection:
    with ABI_PATH.open("r") as f:
        abis_data: dict = json.load(f)
    abis_data = {k[:-3]: [v] for k, v in abis_data.items()}
    return AbiCollection(**abis_data)


ABIS = get_abis()
