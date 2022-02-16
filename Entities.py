

class Account():
    def __init__(self, id: int = 0, discord_id: str = "", api_key: str = "", api_secret: str = ""):
        self.id = id
        self.discord_id = discord_id
        self.api_key = api_key
        self.api_secret = api_secret


class Asset():
    def __init__(self, id=0, discord_id: str = "", asset_name: str = "", amount: float = 0, buytime_worth: float = 0, is_staked: int=0):
        self.id = id
        self.discord_id = discord_id
        self.asset_name = asset_name
        self.amount = amount
        self.buytime_worth = buytime_worth
        self.is_staked = is_staked

    def in_list(self, list: list):
        for asset in list:
            if (asset.asset_name == self.asset_name):
                return asset



class Track():
    def __init__(self, id=0, asset_name: str = "", low_alert: float = 0, high_alert: float = 0, interval: str = ""):
        self.id = id
        self.asset_name = asset_name
        self.low_alert = low_alert
        self.high_alert = high_alert
        self.interval = interval

    



