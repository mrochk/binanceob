# Binance Order-Book

Python project allowing one to run a Binance order-book locally in the terminal.

<img src="./ss.png" width="300" title="screenshot">

This project simply follows the Binance API recommendations that you can find [here](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#how-to-manage-a-local-order-book-correctly).

*Note that the highest frequency at which Binance allows us to update the status of our book is 100ms.*

***

Usage:
```
python3 main.py symbol>
```

Example:
```
python3 main.py ETHUSDT
```
