import sqlite3
import copy
from typing import Generic, TypeVar

Entity = TypeVar("Entity")

class SqliteDal(Generic[Entity]):

    def __init__(self, database_name: str, table: str, data_object_type: type) -> None:
        self.__data_object_type = data_object_type
        self.__database_name = database_name
        self.__table = table

    # data : object parsed to dictionary

    def add(self, data: dict) -> bool:
        data = data.copy()
        conn = sqlite3.connect(self.__database_name)

        for x in data:  # if data is string adds ' if not converts to string for query standarts
            if type(data[x]) == str:
                data[x] = "\"" + data[x] + "\""
            else:
                data[x] = str(data[x])
        data.pop("id") # removes id from data because database auto allocates
        try:
            conn.execute("""insert into %s (%s) values (%s) """ % (
                self.__table, ",".join(list(data.keys())), ",".join(list(data.values()))))  # adds object to database
        except Exception as e:
            return e
        conn.commit()
        conn.close()
        return True

    def delete(self, id: int):
        conn = sqlite3.connect(self.__database_name)
        conn.execute("""delete from %s where id=%d""" % (self.__table, id))
        conn.commit()
        conn.close()

    def update(self, data:dict):
        data = data.copy()
        id = data["id"]
        data.pop("id")
        conn = sqlite3.connect(self.__database_name)
        str_data = ""
        for item in data:
            if type(data[item]) == str:
                data[item] = "\"" + data[item] + "\"" 
            str_data +="'%s'= %s, " %(item, str(data[item]))
        conn.execute("""update %s set %s where id=%d""" % (self.__table, str_data[:-2], id))
        conn.commit()
        conn.close()
        pass

    def get_all(self) -> list[Entity]:
        conn = sqlite3.connect(self.__database_name, sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()
        # getting data of given table
        cur.execute("select * from %s" % (self.__table))

        # parsing tables to list brought from db
        columns = [x[0] for x in cur.description]
        data = cur.fetchall()  # parsing data to list brought from db
        data_list = []
        # getting all atributes of object to check if object matches with db
        data_attributes = self.__data_object_type().__dir__()
        for row in data:  # iterates in all rows(objects)
            obj = self.__parse_data_to_object(  # parses data to object and returns the object
                data_attributes,
                # zips columns and rows and converts to dictionary so data gets like: {prop_name : value, ...}
                dict(zip(columns, row))
            )
            data_list.append(copy.copy(obj))

        conn.close()
        return data_list

    def get(self, id:int) -> Entity:
        conn = sqlite3.connect(self.__database_name)
        cur = conn.cursor()
        cur.execute("""select * from %s where id=%d""" % (self.__table, id))
        data = cur.fetchall()[0]
        conn.close()
        return data

    def run_query(self, query) -> list[Entity]:
        conn = sqlite3.connect(self.__database_name)
        cur = conn.cursor()
        cur.execute(query)
        ret = cur.fetchall()
        conn.close()
        return ret




    def __parse_data_to_object(self, attributes: list, data_dict: dict) -> object:
        data_object = self.__data_object_type()
        for property_of_dict in data_dict:
            # checks if object has attribute of given database variable
            if(property_of_dict in attributes):
                data_object.__setattr__(
                    property_of_dict, data_dict[property_of_dict])
            else:
                raise Exception(
                    "Error occured while parsing the database to object")
        return data_object
    
