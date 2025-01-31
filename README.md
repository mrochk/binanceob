# Binance Order-Book

Minimal Python project allowing one to run a Binance order-book locally. This project simply follows the Binance API recommendations that you can find [here](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams#how-to-manage-a-local-order-book-correctly).

The primary goal of this project is to collect order-book data that could be used for financial modelling projects. The data is collected while the program is running, and is written as JSON on interrupt (Ctrl-C).

The collected data is stored in a MongoDB database, one collection per symbol. 

*Note that the highest frequency at which Binance allows us to update the status is 100ms, which might not be suitable for HFT.*

**Usage Examples:**
TODO