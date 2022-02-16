
from copy import copy
import json
from Aspects import log_error
from BinanceService import BinanceService
from DataAccess import AccountDal, AssetDal, TrackDal
from Entities import Account, Asset, Track


class AssetManager():
	def __init__(self) -> None:
		self.__asset_dal = AssetDal()
		self.__binance_manager = BinanceService()
	
	@log_error("asset_manager.txt")
	def get_price(self, symbol):
		return self.__binance_manager.prices.get_price(symbol)

	@log_error("asset_manager.txt")
	def get_all(self, discord_id):
		assets = self.__asset_dal.get_all(
			lambda asset: asset.discord_id == discord_id)
		for asset in assets:
			asset.__setattr__("value", self.__binance_manager.prices.get_price(
				asset.asset_name+"USDT") * asset.amount)
		return assets

	@log_error("asset_manager.txt")
	def get_balance(self, discord_id):
		assets = self.__asset_dal.get_all(
			lambda asset: asset.discord_id == discord_id)
		return self.__binance_manager.get_balance(assets)


	@log_error("asset_manager.txt")
	def check_changes(self, account: Account):
		assets = self.__asset_dal.get_all(lambda a: a.discord_id == account.discord_id)
		current_assets = self.__binance_manager.get_assets(account)
		staked_assets = self.__asset_dal.get_all(lambda a: a.discord_id == account.discord_id and a.is_staked == 1)
		checked_coins = []
		changes = []

		for asset in assets:
			if(asset.is_staked == 1):
				checked_coins.append(asset.asset_name)
				continue

			match = asset.in_list(current_assets)
			if (not match):
				changes.append({"asset": asset.asset_name, "change": -float(asset.amount), "price": self.__binance_manager.prices.get_price(asset.asset_name + "USDT")})
			elif abs(asset.amount - match.amount)/ asset.amount > 0.05:
				changes.append({"asset": asset.asset_name, "change": match.amount - asset.amount, "price": self.__binance_manager.prices.get_price(asset.asset_name + "USDT")})
			checked_coins.append(asset.asset_name)
		
		for cur_asset in current_assets:
			match = cur_asset.in_list(staked_assets)
			if(match):
				if(abs(cur_asset.amount - match.amount) / cur_asset.amount < 0.1): # if staked coin and cur_asset's amount is almost same that means coin is unstaked 
					match.is_staked = 0
					self.__asset_dal.update(match)
			
			if(cur_asset.asset_name not in checked_coins):
				changes.append({"asset": cur_asset.asset_name, "change": cur_asset.amount, "price": self.__binance_manager.prices.get_price(cur_asset.asset_name + "USDT")})
		
		if(changes):
			for asset in assets:
				if(asset.is_staked == 0):
					self.__asset_dal.delete(asset.id)
			
			for cur_asset in current_assets:
				self.__binance_manager.set_buytime_worth(cur_asset, account)
				self.__asset_dal.add(cur_asset)
		return changes
	
	@log_error("asset_manager.txt")
	def add(self, asset: Asset, account: Account):
		self.__binance_manager.set_buytime_worth(asset, account)
		self.__asset_dal.add(asset)
	
	@log_error("asset_manager.txt")
	def delete(self, asset_name, discord_id):
		asset_to_delete = self.__asset_dal.get_all(lambda asset: asset.asset_name == asset_name and asset.discord_id == discord_id)[0]
		self.__asset_dal.delete(asset_to_delete.id)
	
		



class AccountManager():
	def __init__(self) -> None:
		self.__account_dal = AccountDal()
		self.__asset_dal = AssetDal()
		self.__binance_manager = BinanceService()

	@log_error("account_manager.txt")
	def exists(self, discord_id):
		accs = self.__account_dal.get_all(lambda acc: acc.discord_id == discord_id)
		if accs:
			return True
		return False

	@log_error("account_manager.txt")
	def add(self, account: Account):
		self.__account_dal.add(account)
		assets = self.__binance_manager.get_assets(account)
		for asset in assets:
			self.__binance_manager.set_buytime_worth(asset, account)
			self.__asset_dal.add(asset)
	
	@log_error("account_manager.txt")
	def delete(self, discord_id):
		acc = self.__account_dal.get_all(lambda a: a.discord_id == discord_id)[0]
		self.__account_dal.delete(acc.id)

	@log_error("account_manager.txt")
	def get_by_discord_id(self, discord_id):
		acc = self.__account_dal.get_all(lambda a: a.discord_id == discord_id)[0]
		return acc

	@log_error("account_manager.txt")
	def get_all(self):
		return self.__account_dal.get_all()



class TrackManager():
	def __init__(self) -> None:
		self.__track_dal = TrackDal()
		self.__binance_manager = BinanceService()

		

	@log_error("track_manager.txt")
	def add(self, asset_name):
		track = self.__track_dal.get_all(lambda t: t.asset_name == asset_name)
		interval = str({"1m": 1, "1h": 3, "4h": 7, "1d": 10})
		if(not track):
			track = Track(asset_name=asset_name,
						interval= interval)
			self.__track_dal.add(track)
		else:
			track = track[0]
			track.interval =interval
			self.__track_dal.update(track)

	@log_error("track_manager.txt")
	def delete(self, asset_name):
		track = self.__track_dal.get_all(lambda t: t.asset_name == asset_name)
		if(len(track) == 1):
			self.__track_dal.delete(track[0].id)

	@log_error("track_manager.txt")
	def add_alert(self, asset_name, alert):
		track = self.__track_dal.get_all(lambda t: t.asset_name == asset_name)
		if(not track):
			track = Track(asset_name=asset_name)
			if(alert > self.__binance_manager.prices.get_price(asset_name + "USDT")):
				track.high_alert = alert
			else:
				track.low_alert = alert
			self.__track_dal.add(track)
		else:
			track = track[0]
			if(alert > self.__binance_manager.prices.get_price(asset_name + "USDT")):
				track.high_alert = alert
			else:
				track.low_alert = alert
			self.__track_dal.update(track)

	@log_error("track_manager.txt")
	def check_interval(self, interval):
		track_results = []
		tracks = self.__track_dal.get_all(lambda t: t.interval)
		for track in tracks:
			track = copy(track)
			track.interval = json.loads(track.interval.replace("'", "\""))
			track_result = self.__binance_manager.track_coin(track.asset_name, interval, track.interval[interval])
			if(track_result):
				track_results.append(track_result)
		return track_results

	@log_error("track_manager.txt")
	def check_alert(self):
		alert_results = []
		high_alert_tracks = self.__track_dal.get_all(lambda t: t.high_alert)
		low_alert_tracks = self.__track_dal.get_all(lambda t: t.low_alert)
		for track in high_alert_tracks:
			if(self.__binance_manager.prices.get_price(track.asset_name + "USDT") > track.high_alert):
				alert_results.append({"asset": track.asset_name, "change": "over", "price": track.high_alert})
				track.high_alert = 0
				self.__track_dal.update(track)
		for track in low_alert_tracks:
			if(self.__binance_manager.prices.get_price(track.asset_name + "USDT") < track.low_alert):
				alert_results.append({"asset": track.asset_name, "change": "below", "price": track.low_alert})
				track.low_alert = 0
				self.__track_dal.update(track)
		return alert_results



