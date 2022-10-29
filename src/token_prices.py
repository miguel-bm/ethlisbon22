import json
from time import sleep
from typing import Dict, List, Optional, Tuple

import requests


def request_get_with_retry(url: str, retries: int = 10) -> requests.Response:
    for _ in range(retries):
        response = requests.get(url)
        if response.status_code == 429:
            continue
        else:
            sleep(0.5)
            break
    return response


def get_token_price(token: str) -> Tuple[str, float, int]:
    coingecko_symbol = coingecko[token]
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coingecko_symbol}&vs_currencies=usd"
    response = request_get_with_retry(url)
    if response.status_code != 200:
        url = f"https://min-api.cryptocompare.com/data/price?fsym={token}&tsyms=USD"
        response = request_get_with_retry(url)
        if response.status_code != 200:
            return token, 0.0
        return token, response.json()["USD"]
    api_price = response.json()[coingecko_symbol]["usd"]
    return token, api_price, 0


def get_chainlink_price(feed_address: str, web3: Web3) -> float:
    feed: Contract = web3.eth.contract(
        abi=price_addresses["chainlinkAbi"], address=feed_address
    )
    answer = feed.functions["latestAnswer"]().call()
    decimals = feed.functions["decimals"]().call()
    factor = 10 ** (18 - decimals)
    return web3.from_wei(answer * factor, "ether")


def get_special_fetcher(
    network: str, address: str
) -> Optional[Callable[[str, str], float]]:
    # Placeholder
    return None


def fetch_price(network: str, address: str) -> float:
    if special_fetcher := get_special_fetcher(network, address):
        return special_fetcher(network, address)
    elif network == "ETH":
        url = f"https://pricing-prod.krystal.team/v1/market?addresses={address.lower()}&chain=ethereum@1&sparkline=false"
        response = requests.get(url)
        if response.status_code == 200:
            market_data = response.json()["marketData"]
            if len(market_data) > 0:
                return market_data[0]["price"] or 0.0

    url = f"https://api.coingecko.com/api/v3/simple/token_price/{coingecko[network]}?contract_addresses={address}&vs_currencies=USD"
    response = requests.get(url)
    if response.status_code != 200 or len(response.json()) == 0:
        return 0.0
    return response.json()[network]["usd"]


def get_price(network: str, address: str, web3: Web3) -> Tuple[str, float, int]:
    token: Contract = web3.eth.contract(
        abi=price_addresses["erc20Abi"], address=address
    )
    decimal = token.functions["decimals"]().call()
    try:
        symbol = (
            token.functions["symbol"]().call()
            if "symbol" in token.functions
            else "unknown"
        )
    except:
        symbol = "unknown"
        print(f"Error fetching symbol for {network} {address}")

    api_price = fetch_price(network, address)

    if api_price == 0.0 and network == "ETH":
        # TODO use zappier
        pass

    return symbol, api_price, decimal

    if decimal > 18:
        normalizer = decimal - 18
        price = web3.to_wei(api_price, "ether") / (10**normalizer)
    else:
        normalizer = 18 - decimal
        price = web3.to_wei(api_price, "ether") * (10**normalizer)

    return symbol, price / 1e18
