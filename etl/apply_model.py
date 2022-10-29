import pandas as pd
import json
import numpy as np
from collections import OrderedDict

TOTAL_MAKETS_PATH = "additional_data/total_markets_coingecko.csv"
ETHEREUM_COMPOUND_PATH = "data/users/compound_data.json"

RATIO_COMPOUND_INDUSTRY = 0.1
LIQUIDATION_THESHOLD = 1


def get_slippage_dollars(sale_amount: float, market_size: float):
    return 1 / (1 + 2 * sale_amount / market_size)


def get_total_market_size() -> float:
    df = pd.read_csv(TOTAL_MAKETS_PATH)
    df["2% Depth"] = pd.to_numeric(
        df["2% Depth"].str.replace(",", "").str.replace("$", "")
    )
    df["-2% Depth"] = pd.to_numeric(
        df["-2% Depth"].str.replace(",", "").str.replace("$", "")
    )

    df["up_depth"] = df["2% Depth"].apply(lambda x: x * 0.98 * 100)
    df["down_depth"] = df["-2% Depth"].apply(lambda x: x * 1.02 * 100)
    df["virtual_total_market"] = (df["up_depth"] + df["down_depth"]) / 2

    return df[df["Pair"].str.contains("/US")]["virtual_total_market"].sum()


def impact_lower_price(price_change):

    eth_compound = json.load(open("additional_data/ethereum_compound.json"))
    users_with_markets = [
        i for i in eth_compound["users"] if len(i["markets"]) > 0
    ]  # clean empty users

    m_status = json.load(open("additional_data/compmound_markets_status.json"))
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
        ~df_collaterals.collateral.isin(["DAI", "USDC", "USDT", "TUSD"])
    ]
    df_collaterals_ns.value = df_collaterals_ns.value / df_collaterals_ns.value.sum()

    ratio_eth = df_collaterals_ns[df_collaterals_ns.collateral == "ETH"].values[0][1]

    # discount stablecoins
    stable_coins_markets = [
        "0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643",
        "0x39AA39c021dfbaE8faC545936693aC917d5E7563",
        "0xf650C3d88D12dB855b8bf7D11Be6C55A4e07dCC9",
        "0x12392F67bdf24faE0AF363c24aC620a2f67DAd86",
    ]

    def get_stable_coins(x):
        return np.sum(
            [
                i["collateral"]
                for i in x["markets"]
                if i["market"] in stable_coins_markets
            ]
        )

    users_with_markets_and_stable_collat = [
        {**user_data, **{"stable_collateral": get_stable_coins(user_data)}}
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

    def get_liquidation_percentage(x, y):
        return y / x

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
    ]

    df_users = pd.DataFrame(users_with_markets_and_stable_collat_with_liquidation)
    df_users["eth_collateral"] = df_users["collateral"] - df_users["stable_collateral"]
    df_users = df_users[
        (df_users.eth_collateral > 0) & (df_users.netValue > 0)
    ].sort_values("liquidation_perc", ascending=False)

    df_users["total_liquidation"] = (
        df_users["eth_collateral"].cumsum() * ratio_eth
    )  # the amount of ETH that will be liquidated and sold is 80% of the collateral
    df_users["price_change"] = 1 - df_users["liquidation_perc"]

    df_users["liquidation_slippage"] = get_slippage_dollars(
        df_users["total_liquidation"] / RATIO_COMPOUND_INDUSTRY, total_market
    )  # tenemos que añadir la proporcion de esto del mercado
    df_users["price_after_slippage"] = (
        df_users["liquidation_perc"] * df_users["liquidation_slippage"]
    )

    market_effects = {
        "price_change": df_users[df_users.price_change > price_change]["price_change"]
        .head(1)
        .values[0],
        "total_liquidation": df_users[df_users.price_change > price_change][
            "total_liquidation"
        ]
        .head(1)
        .values[0],
        "liquidation_slippage": df_users[df_users.price_change > price_change][
            "liquidation_slippage"
        ]
        .head(1)
        .values[0],  # this is the multiplier of the price
    }

    return market_effects


def main():
    total_market_size = get_total_market_size()


if __name__ == "__main__":
    main()
