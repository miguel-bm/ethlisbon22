from src.data_extraction.compound import CompoundDataExtractor
from src.utils import get_ethereum_web3_client
from src.protocols_data import CompoundProtocolReference

if __name__ == "__main__":
    web3_client = get_ethereum_web3_client("mainnet")
    network = "ETH"
    protocol_info = CompoundProtocolReference.from_json_reference("compound", network)

    extractor = CompoundDataExtractor(
        w3=web3_client,
        protocol_info=protocol_info,
        network=network,
    )
    extractor.extract_data(save_to="data/users/compound_data.json")
