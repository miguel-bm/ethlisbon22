from typing import Dict, List, Optional

import eth_abi
from abis import ABIS
from src.borrower import Borrower
from src.protocols_data import CompoundProtocolReference
from web3 import Web3
from web3.eth import Contract
from src.addresses import MULTICALL_ADDRESSES


class CompoundDataExtractor:
    def __init__(
        self,
        w3: Web3,
        protocol_info: Dict[str, CompoundProtocolReference],
        network: str,
    ):
        self.w3 = w3
        self.network = network
        self.protocol_info = protocol_info
        protocol_network_info = self.protocol_info[network]

        self.ceth_addresses = protocol_network_info.ceth_addresses
        self.non_borrowable_markets = protocol_network_info.non_borrowable_markets
        self.non_supplyable_markets = protocol_network_info.non_supplyable_markets
        self.deploy_block = protocol_network_info.deploy_block
        self.block_step_in_init = protocol_network_info.block_step_in_init
        self.multicall_size = protocol_network_info.multicall_size

        self.comptroller: Contract = w3.eth.contract(
            abi=ABIS.comptroller, address=protocol_network_info.comptroller_address
        )
        self.multicall: Contract = w3.eth.contract(
            abi=ABIS.multicall, address=MULTICALL_ADDRESSES[network]
        )

        self.prices: Dict[str, int] = {}
        self.markets: List = []
        self.users: Dict[str, Borrower] = {}
        self.user_list: List = []

        self.tvl = 0
        self.total_borrows = 0

        self.output = {}

    def get_market_addresses(self) -> List[str]:
        markets: List[str] = self.comptroller.functions["getAllMarkets"]().call()
        return [self.w3.toChecksumAddress(address) for address in markets]

    def get_market_token_price(self, market_address: str) -> float:
        ctoken: Contract = self.w3.eth.contract(abi=ABIS.cToken, address=market_address)

        if market_address in self.ceth_addresses:
            symbol, price = get_token_price(self.network)
            balance = self.w3.eth.get_balance(market_address)
        else:
            underlying: str = ctoken.functions["underlying"]().call()
            symbol, price = get_price(self.network, underlying, self.w3)

            token: Contract = self.w3.eth.contract(abi=ABIS.cToken, address=underlying)
            balance = token.functions["balanceOf"](market_address).call()

        print(
            f"Symbol {symbol} ({underlying}) ; market {market_address} ; price {price} ; balance {balance}"
        )

        # TODO: if price == 0, get fallback price
        return price

    def initialize_prices(self):
        self.markets = self.get_market_addresses()
        self.prices = {m: self.get_market_token_price(m) for m in self.markets}

    def collect_all_users(self):
        current_block = self.w3.eth.get_block_number() - 10
        for block in range(self.deploy_block, current_block, self.block_step_in_init):
            print(f"collect users at block {block}")
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
                if account is None:
                    continue
                account = self.w3.toChecksumAddress(account)
                if account not in self.users:
                    self.user_list.append(account)

    def update_all_users(self):
        users = self.user_list
        batch_size = self.multicall_size
        for i in range(0, len(users), batch_size):
            print(f"update users {i} / {len(users)}")
            self.update_users_batch(users[i : i + batch_size])

    def update_users_batch(self, user_addresses: List[str]):
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
            for market in self.markets:
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

            for market in self.markets:
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
                not success,
            )
            self.users[user_address] = user_data
