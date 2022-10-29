from dotenv import load_dotenv
from os import getenv
from web3 import Web3, HTTPProvider

load_dotenv()
INFURA_API_KEY = getenv("INFURA_API_KEY")
GETBLOCK_API_KEY = getenv("GETBLOCK_API_KEY")
CRONOS_API_KEY = getenv("CRONOS_API_KEY")


def get_ethereum_web3_client(network: str) -> Web3:
    url = f"https://{network}.infura.io/v3/{INFURA_API_KEY}"
    print(f"Connecting to {url}")
    client = Web3(HTTPProvider(url))
    assert client.isConnected(), "Web3 client is not connected"
    return client


def get_near_web3_client() -> Web3:
    load_dotenv()
    url = f"https://avalanche-mainnet.infura.io/v3/{INFURA_API_KEY}"
    print(f"Connecting to {url}")
    client = Web3(HTTPProvider(url))
    assert client.isConnected(), "Web3 client is not connected"
    return client


def get_avalanche_web3_client() -> Web3:
    load_dotenv()
    url = f"https://avalanche-mainnet.infura.io/v3/{INFURA_API_KEY}"
    print(f"Connecting to {url}")
    client = Web3(HTTPProvider(url))
    assert client.isConnected(), "Web3 client is not connected"
    return client


def get_cronos_web3_client() -> Web3:
    load_dotenv()
    url = f"https://mainnet.cronoslabs.com/v1/{CRONOS_API_KEY}"
    print(f"Connecting to {url}")
    client = Web3(HTTPProvider(url))
    assert client.isConnected(), "Web3 client is not connected"
    return client
