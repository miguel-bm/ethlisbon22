import json
from pathlib import Path
from typing import Dict, List, Optional

import eth_abi
from src.abis import ABIS
from src.addresses import MULTICALL_ADDRESSES
from src.borrower import Borrower
from src.protocols_data import CompoundProtocolReference
from src.token_prices import get_eth_price, get_token_price
from web3 import Web3
from web3.eth import Contract


class CompoundDataExtractor:
    def __init__(
        self,
        w3: Web3,
        protocol_info: CompoundProtocolReference,
        network: str,
    ):
        self.w3 = w3
        self.network = network
        self.protocol_info = protocol_info

        self.ceth_addresses = protocol_info.ceth_addresses
        self.non_borrowable_markets = protocol_info.non_borrowable_markets
        self.non_supplyable_markets = protocol_info.non_supplyable_markets
        self.deploy_block = protocol_info.deploy_block
        self.block_step_in_init = protocol_info.block_step_in_init
        self.multicall_size = protocol_info.multicall_size

        self.comptroller: Contract = w3.eth.contract(
            abi=ABIS.comptroller, address=protocol_info.comptroller_address
        )
        self.multicall: Contract = w3.eth.contract(
            abi=ABIS.multicall, address=MULTICALL_ADDRESSES[network]
        )

    def _get_market_addresses(self) -> List[str]:
        markets: List[str] = self.comptroller.functions["getAllMarkets"]().call()
        return [self.w3.toChecksumAddress(address) for address in markets]

    def _get_market_token_price(self, market_address: str) -> float:
        ctoken: Contract = self.w3.eth.contract(abi=ABIS.cToken, address=market_address)

        if market_address in self.ceth_addresses:
            symbol, price = get_eth_price(self.network)
            balance = self.w3.eth.get_balance(market_address)
        else:
            underlying: str = ctoken.functions["underlying"]().call()
            symbol, price = get_token_price(self.network, underlying, self.w3)
            token: Contract = self.w3.eth.contract(abi=ABIS.cToken, address=underlying)
            balance = token.functions["balanceOf"](market_address).call()

        # TODO: if price == 0, get fallback price
        return price

    def extract_data(self, save_to: str, users_limit: Optional[int] = None):
        # Get markets token prices
        markets = self._get_market_addresses()
        prices = {m: self._get_market_token_price(m) for m in markets}

        # Get all users
        user_addresses = self._get_all_user_addresses(users_limit)

        # Get user data
        user_data = self._get_users_data(markets, user_addresses, self.multicall_size)

        # Export user data
        user_data_json = {k: v.get_markets_values(prices) for k, v in user_data.items()}
        with Path(save_to).open("w") as f:
            json.dump(user_data_json, f)

    def _get_all_user_addresses(self, limit: Optional[int] = None) -> List[str]:
        current_block = self.w3.eth.get_block_number() - 10
        user_addresses = []
        print(f"Current block is: {current_block}")
        print(f"Deploy block is: {self.deploy_block}")
        for block in range(self.deploy_block, current_block, self.block_step_in_init):
            print(f"Collect users at block {block}")
            end_block = (
                current_block
                if (block + self.block_step_in_init > current_block)
                else block + self.block_step_in_init
            )
            events: List[dict] = (
                self.comptroller.events["MarketEntered"]
                .createFilter(fromBlock=block, toBlock=end_block)
                .get_all_entries()
            )
            for event in events:
                account: Optional[str] = event.get("args", {}).get("account", None)
                if account is not None:
                    account = self.w3.toChecksumAddress(account)
                    if account not in user_addresses:
                        user_addresses.append(account)

                if limit is not None:
                    if len(user_addresses) >= limit:
                        return user_addresses[:limit]

        return user_addresses

    def _get_users_data(
        self, markets: List[str], user_addresses: List[str], batch_size: int
    ):
        user_data: Dict[str, Borrower] = {}
        for i in range(0, len(user_addresses), batch_size):
            print(f"Updating users info: {i} / {len(user_addresses)}")
            batch_addresses = user_addresses[i : i + batch_size]
            batch_users_data = self._get_users_data_batch(markets, batch_addresses)
            user_data.update(batch_users_data)

        return user_data

    def _get_users_data_batch(
        self, markets: list[str], user_addresses: List[str]
    ) -> Dict[str, Borrower]:
        asset_in_calls = [
            {
                "target": self.comptroller.address,
                "callData": self.comptroller.encodeABI(
                    fn_name="getAssetsIn", args=[address]
                ),
            }
            for address in user_addresses
        ]

        asset_in_result = self.multicall.functions["tryAggregate"](
            False, asset_in_calls
        ).call()
        ctoken = self.w3.eth.contract(abi=ABIS.cToken)

        collateral_balance_calls = []
        borrow_balance_calls = []

        for user_address in user_addresses:
            for market in markets:
                collateral_balance_calls.append(
                    {
                        "target": market,
                        "callData": (
                            ctoken.encodeABI(
                                fn_name="balanceOfUnderlying", args=[user_address]
                            )
                            if market not in self.non_supplyable_markets
                            else ctoken.encodeABI(
                                fn_name="balanceOf", args=[user_address]
                            )
                        ),
                    }
                )
                borrow_balance_calls.append(
                    {
                        "target": market,
                        "callData": (
                            ctoken.encodeABI(
                                fn_name="borrowBalanceStored", args=[user_address]
                            )
                            if market not in self.non_borrowable_markets
                            else ctoken.encodeABI(
                                fn_name="balanceOf", args=[user_address]
                            )
                        ),
                    }
                )

        collateral_balance_results = self.multicall.functions["tryAggregate"](
            False, collateral_balance_calls
        ).call()
        borrow_balance_results = self.multicall.functions["tryAggregate"](
            False, borrow_balance_calls
        ).call()

        user_index = 0
        global_index = 0
        users_data = {}
        for user_address in user_addresses:
            success = True
            success = success and asset_in_result[user_index][0]
            asset_in: Optional[str] = (
                eth_abi.decode_single("(address[])", asset_in_result[user_index][1])[0]
                if success
                else None
            )
            if asset_in is not None:
                asset_in = [self.w3.toChecksumAddress(a) for a in asset_in]
            user_index += 1

            borrow_balances = {}
            collateral_balances = {}

            for market in markets:
                success = success and collateral_balance_results[global_index][0]
                success = success and borrow_balance_results[global_index][0]
                collateral_balance = (
                    eth_abi.decode_single(
                        "(uint256)", collateral_balance_results[global_index][1]
                    )[0]
                    if success
                    else None
                )
                borrow_balance = (
                    eth_abi.decode_single(
                        "(uint256)", borrow_balance_results[global_index][1]
                    )[0]
                    if success
                    else None
                )

                collateral_balances[market] = collateral_balance
                borrow_balances[market] = borrow_balance

                global_index += 1

            user_data = Borrower(
                user_address,
                asset_in,
                borrow_balances,
                collateral_balances,
            )
            users_data[user_address] = user_data

        return users_data
