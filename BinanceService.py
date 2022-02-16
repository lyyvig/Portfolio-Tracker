from binance import Client
from Aspects import log_error, singleton
from Entities import Account, Asset


class Prices():
    def __init__(self, client: Client) -> None:
        self.__prices = {}
        self.__client = client

    def update_prices(self):
        prices = self.__client.get_all_tickers()
        for price in prices:
            self.__prices[price["symbol"]] = price["price"]

    def get_price(self, symbol) -> float:
        if "USD" in symbol[:4] and "USD" in symbol[3:]:
            return 1
        return float(self.__prices[symbol])


def _purge_from_earn_data(asset):
    if("LD" == asset[:2]):
        return asset[2:]
    return asset



@singleton
class BinanceService():
    def __init__(self) -> None:
        self.__client = Client()
        self.prices = Prices(self.__client)
        self.prices.update_prices()

    @log_error("binance_service.txt")
    def get_balance(self, assets: list[Asset]) -> float:
        self.prices.update_prices()
        balance = 0
        for asset in assets:
            balance += asset.amount * \
                self.prices.get_price(asset.asset_name + "USDT")
        return balance

    @log_error("binance_service.txt")
    def get_assets(self, account: Account) -> list[Asset]:
        client = Client(account.api_key, account.api_secret)
        assets = []
        assets_dict = {}
        raw_assets = client.get_account()['balances']
        for raw_asset in raw_assets:
            # staked coins have LD in front this func deletes it
            asset_name = _purge_from_earn_data(raw_asset["asset"])
            amount = float(raw_asset["free"]) + float(raw_asset["locked"])
            # ignores coins worth less than 15$
            if (amount > 0 and amount * self.prices.get_price(asset_name + "USDT") > 15):
                if (asset_name in assets_dict):  # adds coins worth more than 15$ to another dict
                    assets_dict[asset_name] += amount
                else:
                    assets_dict[asset_name] = amount
        for asset in assets_dict:
            assets.append(Asset(asset_name=asset, amount=assets_dict[asset]))
        return assets

    @log_error("binance_service.txt")
    def set_buytime_worth(self, asset: Asset, account: Account):
        asset.discord_id = account.discord_id
        if("USD" in asset.asset_name):
            asset.buytime_worth = asset.amount
            return
        client = Client(account.api_key, account.api_secret)
        worth = 0
        order_history = client.get_my_trades(
            symbol=asset.asset_name + 'USDT')
        amount = asset.amount

        for i in range(len(order_history)-1, -1, -1):
            # if coin staked and earned even 1 day calculation of buy and sells brokes up so
            # if at the current stage of loop if amount is less than 15$ checks if
            # current trade suits up for the calculation if it does adds to variables and brakes the loop
            if (amount * self.prices.get_price(asset.asset_name+"USDT") < 15):
                if(abs(float(order_history[i]["qty"])-amount)/amount < 0.1):
                    worth += float(order_history[i]["quoteQty"])
                    amount -= float(order_history[i]["qty"])
                break

            if(order_history[i]["isBuyer"]):
                # adds to buytime worth of coin if trade is buyer
                worth += float(order_history[i]["quoteQty"])
                # substracts amount of coin
                amount -= float(order_history[i]["qty"])
            else:
                # opposite process of above
                worth -= float(order_history[i]["quoteQty"])
                amount += float(order_history[i]["qty"])
        if amount < 0:  # if somehow calculation process screwed it up sets buytime value to price of this moment
            asset.buytime_worth = asset.amount * \
                self.prices.get_price(asset.asset_name + "USDT")
        elif (amount != 0):  # if amount left after the process adds to buytime worth
            worth += amount * self.prices.get_price(asset.asset_name+"USDT")
        asset.buytime_worth = worth

    @log_error("binance_service.txt")
    def track_coin(self, asset_name, interval, min_change_percentage):
        kline = self.__client.get_klines(symbol = asset_name+"USDT", limit =2, interval = interval)
        kline = kline[0]
        change_percentage = (float(kline[4]) - float(kline[1]))/float(kline[1])*100
        if(abs(change_percentage) >= min_change_percentage):
            return {"asset": asset_name, "interval": interval, "change_percentage": change_percentage, "price": self.prices.get_price(asset_name+"USDT")}
        return None


