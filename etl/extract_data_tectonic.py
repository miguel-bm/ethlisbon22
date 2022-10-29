from src.data_extraction.compound import CompoundDataExtractor
from src.utils import get_cronos_web3_client
from src.protocols_data import CompoundProtocolReference

if __name__ == "__main__":
    web3_client = get_cronos_web3_client()
    network = "CRO"
    protocol_info = CompoundProtocolReference.from_json_reference("tectonic", network)

    extractor = CompoundDataExtractor(
        w3=web3_client,
        protocol_info=protocol_info,
        network=network,
    )
    extractor.extract_data(save_to="data/users/tectonic_data.json")
