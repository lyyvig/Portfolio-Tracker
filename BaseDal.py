import copy
from operator import truediv
from types import MethodType
from DataAccessHelper import SqliteDal as BaseDataAccess
from typing import Generic, TypeVar

Entity = TypeVar("Entity")


class BaseDal(Generic[Entity]):
    def __init__(self, table: str, class_type: type) -> None:
        self.__data_access = BaseDataAccess[Entity]("data.db", table, class_type)
        self.__data = self.__data_access.get_all()

    def get(self, id: int) -> Entity:
        for obj in self.__data:
            if(obj.id == id):
                return obj

    def get_all(self, filt : MethodType = None) -> list[Entity]:
        return list(filter(filt, self.__data))

    def add(self, entity: Entity):
        print(self.__data_access.add(entity.__dict__))
        self.__data = self.__data_access.get_all()

    def update(self, entity: Entity):
        self.__data_access.update(entity.__dict__)
        self.__data = self.__data_access.get_all()

    def delete(self, id: int):
        self.__data_access.delete(id)
        self.__data = self.__data_access.get_all()
    
    



