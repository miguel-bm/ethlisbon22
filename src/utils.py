from dotenv import load_dotenv
from os import getenv
from web3 import Web3, HTTPProvider


def get_web3_client(network: str) -> Web3:
    load_dotenv()
    api_key = getenv("INFURA_API_KEY")
    url = f"https://{network}.infura.io/v3/{api_key}"
    print(f"Connecting to {url}")
    client = Web3(HTTPProvider(url))
    assert client.isConnected(), "Web3 client is not connected"
    return client
