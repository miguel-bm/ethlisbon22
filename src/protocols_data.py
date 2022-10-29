from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import List, Optional
from web3 import Web3

PROTOCOL_REFERENCE_PATH = Path("data/protocol_reference.json")


@dataclass
class CompoundProtocolReference:
    comptroller_address: str
    ceth_address: str
    deploy_block: int
    block_step_in_init: int
    multicall_size: int
    ceth2_address: Optional[str] = None
    non_borrowable_markets: list = field(default_factory=list)
    non_supplyable_markets: list = field(default_factory=list)

    @property
    def ceth_addresses(self) -> List[str]:
        return [
            Web3.toChecksumAddress(a)
            for a in (self.ceth_address, self.ceth2_address)
            if a is not None
        ]

    @classmethod
    def from_dict(cls, data: dict) -> "CompoundProtocolReference":
        return cls(
            comptroller_address=Web3.toChecksumAddress(data["comptroller"]),
            ceth_address=Web3.toChecksumAddress(data["cETH"]),
            deploy_block=int(data["deployBlock"]),
            block_step_in_init=int(data["blockStepInInit"]),
            multicall_size=int(data["multicallSize"]),
            ceth2_address=Web3.toChecksumAddress(data["cETH2"])
            if "cETH2" in data
            else None,
            non_borrowable_markets=[
                Web3.toChecksumAddress(a)
                for a in data.get("nonBorrowableMarkets", list())
            ],
            non_supplyable_markets=[
                Web3.toChecksumAddress(a) for a in data.get("rektMarkets", list())
            ],
        )

    @classmethod
    def from_json_reference(
        cls, name: str, network: str
    ) -> "CompoundProtocolReference":
        with open(PROTOCOL_REFERENCE_PATH, "r") as f:
            data = json.load(f)
        return cls.from_dict(data[name][network])
