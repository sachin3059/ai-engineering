import yfinance as yf
import json

def get_stock_price(ticker_symbol:str) -> str:
    """ Fetch the current price of a stock given its ticker symbol """
    try:
        stock = yf.Ticker(ticker_symbol)
        price = stock.fast_info["lastPrice"]
        currency = stock.fast_info["currency"]

        return json.dumps({
            "ticker": ticker_symbol.upper(),
            "price": price,
            "currency": currency
        })
    except Exception as e:
        print(f"Error fetching stock price for {ticker_symbol}: {e}")
        return json.dumps({
            "error": str(e)
        })

if __name__ == "__main__":
    ticker_symbol = "AAPL"
    price = get_stock_price(ticker_symbol)
    print(f"The current price of {ticker_symbol} is {price}")



