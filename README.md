# Binance Orderbook

Python project allowing one to run a Binance order book locally.

<img src="./ss.png" width="300" title="screenshot">

This project simply follows the Binance API recommendations that you can find [here](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#how-to-manage-a-local-order-book-correctly).

The primary goal of this project is to collect (relatively high frequency) order book data that could be used financial modelling projects.

*Note that the highest frequency at which Binance allows us to update the status of our order-book is 100ms, which might not be suitable for HFT.*

***

Usage for simply displaying the order book in your terminal (as in the screenshot):
```
python3 main.py symbol>
```

Example:
```
python3 main.py ETHUSDT
```

***

Usage for data collection: TODO
