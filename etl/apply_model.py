import pandas as pd
import json
import numpy as np
from pathlib import Path
from collections import OrderedDict
from typing import Optional

TOTAL_MAKETS_PATH = Path("data/total_markets_coingecko.csv")
ETHEREUM_COMPOUND_PATH = Path("data/users/ethereum_compound.json")

RATIO_COMPOUND_INDUSTRY = 0.1
LIQUIDATION_THESHOLD = 1


STABLECOIN_MARKETS = [
    "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
    "0x39AA39c021dfbaE8faC545936693aC917d5E7563",
    "0xf650C3d88D12dB855b8bf7D11Be6C55A4e07dCC9",
    "0x12392F67bdf24faE0AF363c24aC620a2f67DAd86",
]
STABLECOIN_NAMES = ["DAI", "USDC", "USDT", "TUSD"]


def get_user_stablecoin_collateral(user_markets_data: dict) -> float:
    return np.sum(
        [
            markets_data["collateral"]
            for markets_data in user_markets_data["markets"]
            if markets_data["market"] in STABLECOIN_MARKETS
        ]
    )


def get_slippage_dollars(sale_amount: float, market_size: float):
    return 1 / (1 + 2 * sale_amount / market_size)


def get_total_market_size() -> float:
    df = pd.read_csv(TOTAL_MAKETS_PATH)

    df["2% Depth"] = pd.to_numeric(
        df["2% Depth"]
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
    )
    df["-2% Depth"] = pd.to_numeric(
        df["-2% Depth"]
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
    )

    df["up_depth"] = df["2% Depth"].apply(lambda x: x * 0.98 * 100)
    df["down_depth"] = df["-2% Depth"].apply(lambda x: x * 1.02 * 100)
    df["virtual_total_market"] = (df["up_depth"] + df["down_depth"]) / 2

    return df[df["Pair"].str.contains("/US")]["virtual_total_market"].sum()


def get_market_eth_ratio(eth_compound) -> float:

    # Clean empty users
    users_with_markets = [u for u in eth_compound["users"] if len(u["markets"]) > 0]

    m_status = json.load(open("data/markets/compmound_markets_status.json"))
    m_dict = dict(zip([i for i in m_status], [m_status[i]["symbol"] for i in m_status]))

    # get the ratio of collateral that ETH represents
    collaterals = []
    values = []
    for k in m_dict.keys():
        users_with_markets = [i for i in eth_compound["users"] if len(i["markets"]) > 0]
        collaterals.append(m_dict[k])
        values.append(
            np.sum(
                [
                    i["markets"][0]["collateral"]
                    for i in users_with_markets
                    if i["markets"][0]["market"] == k
                ]
            )
        )
    df_collaterals = pd.DataFrame({"collateral": collaterals, "value": values})
    df_collaterals_ns = df_collaterals[
        ~df_collaterals["collateral"].isin(STABLECOIN_NAMES)
    ]
    value = df_collaterals_ns.set_index("collateral")["value"]
    norm_value = value / value.sum()
    return norm_value["ETH"]


def main():
    total_market_size = get_total_market_size()

    with ETHEREUM_COMPOUND_PATH.open("r") as f:
        eth_compound = json.load(f)

    ratio_eth = get_market_eth_ratio(eth_compound)
    users_with_markets = [u for u in eth_compound["users"] if len(u["markets"]) > 0]

    users_with_markets_and_stable_collat = [
        {
            **user_data,
            **{"stable_collateral": get_user_stablecoin_collateral(user_data)},
        }
        for user_data in users_with_markets
    ]

    users_with_markets_and_stable_collat_with_liquidation = [
        {
            **user_data,
            **{
                "liquidation_value": (
                    user_data["debt"] - (user_data["stable_collateral"])
                )
                / LIQUIDATION_THESHOLD
            },
        }
        for user_data in users_with_markets_and_stable_collat
    ]

    users_with_markets_and_stable_collat_with_liquidation = [
        u
        for u in users_with_markets_and_stable_collat_with_liquidation
        if u["liquidation_value"] > 0
    ]

    def get_liquidation_percentage(x: float, y: float) -> Optional[float]:
        return y / x if x > 0 else None

    users_with_markets_and_stable_collat_with_liquidation = [
        {
            **user_data,
            **{
                "liquidation_perc": get_liquidation_percentage(
                    user_data["collateral"] - user_data["stable_collateral"],
                    user_data["liquidation_value"],
                )
            },
        }
        for user_data in users_with_markets_and_stable_collat_with_liquidation
        if (user_data["collateral"] - user_data["stable_collateral"] > 0)
    ]

    df_users = pd.DataFrame(users_with_markets_and_stable_collat_with_liquidation)
    df_users["eth_collateral"] = df_users["collateral"] - df_users["stable_collateral"]
    df_users = df_users[
        (df_users["eth_collateral"] > 0) & (df_users["netValue"] > 0)
    ].sort_values("liquidation_perc", ascending=False)

    df_users["total_liquidation"] = (
        df_users["eth_collateral"].cumsum() * ratio_eth
    )  # the amount of ETH that will be liquidated and sold is 80% of the collateral
    df_users["price_change"] = 1 - df_users["liquidation_perc"]

    df_users["liquidation_slippage"] = get_slippage_dollars(
        df_users["total_liquidation"] / RATIO_COMPOUND_INDUSTRY, total_market_size
    )  # tenemos que añadir la proporcion de esto del mercado
    df_users["price_after_slippage"] = (
        df_users["liquidation_perc"] * df_users["liquidation_slippage"]
    )
    # round price change to 4 decimals
    df_users["price_change"] = df_users["price_change"].apply(lambda x: round(x, 4))
    df_users = df_users.groupby("price_change").agg(
        total_liquidation=pd.NamedAgg(column="total_liquidation", aggfunc="max"),
        liquidation_slippage=pd.NamedAgg(column="liquidation_slippage", aggfunc="min"),
    )
    df_users.reset_index(inplace=True)

    df_users[["price_change", "total_liquidation", "liquidation_slippage"]].to_json(
        "data/cached_curves/eth.json",
        orient="records",
        indent=4,
        double_precision=4,
    )


if __name__ == "__main__":
    main()
