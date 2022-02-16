from BaseDal import BaseDal
from Entities import Account, Asset, Track


class AccountDal(BaseDal[Account]):
	def __init__(self) -> None:
		super().__init__("Accounts", Account)

class AssetDal(BaseDal[Asset]):
	def __init__(self) -> None:
		super().__init__("Assets", Asset)

class TrackDal(BaseDal[Track]):
	def __init__(self) -> None:
		super().__init__("Tracks", Track)


