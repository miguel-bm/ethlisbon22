# Accumulated Debt Curve

This project aims to measure the accumulated DeFi lending market risks accross multiple chains and markets.

Liquidations are essential to the health of a DeFi lending protocol. However, the debts they cover can result in a downwards pressure over the price of the underlying assets, causing market slippages and even liquidation cascades.

We can monitor the accumulated debts accross these DeFi lending markets to see where new liquidations would trigger. Moreover, we can apply an slippage model in order to check how these liquidations would further impact the market, and even cause liquidation cascades.

## Description

### Data extraction

These are ETLs that extract on-chain borrower data from multiple DeFi lending protocols.

How to run:

#### Python-based jobs

 * Install the requirements with `pipenv install`
 * Run any specific job by running its script. E.g. `pipenv run python etl/extract_data_compound.py`
 
#### Node-based jobs

 * Install the requirements with `npm install`
 * Run with `npm start`

### Accumulated liquidations curve calculation

This is a Python script that takes the output from the data extraction jobs and aggregates it to the ecosystem-wide accumulated liquidations curve. Additionally, it applies a slippage model in order to estimate the price slippage caused by the liquidations at each point of the curve.

For the scope of the Hackahton, this has been done for loans collateralised with ETH or ETH-pegged assets. Separate curves could be calculted for other collateral assets using the same procedure.

How to run:

 * Install the requirements with `pipenv install`
 * Run the transform job with `pipevn run python etl/apply_model.py`

### API

This is the API used by the Risk Management oracle.

How to run:

 * Run locally with `docker-compose up`
