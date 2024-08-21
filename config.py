from pydantic import BaseModel

#! Конфиги записывать в переменную configs(как в примере) 
#? check line 24-48
#! ЗАПРОС НА СОЗДАНИЕ ТАБЛИЦ указывать в переменной create_tables
#? check line 51-64
#! Создание класса с типами колонок в таблицах column_type
#? check line 76-92

class config(BaseModel):
    condition: bool# Сюда передается условие, при выполнении которого будет использоваться данный профиль
    ssh_username:str | None = None # имя профиля на сервере(обычно это postgres)
    ssh_host: str| None = None # ip адрес сервера, на котором находится бд
    ssh_password: str| None = None # пароль от профиля на сервере
    # в любом раскладе это localhost
    # (т.к. при подключении удаленно используется ssh тунель и в таком случае указывается localhost)
    # (при подключении локально передается localhost)
    host: str #? в любом случае используется localhost 
    port: int | None = 5432 # стандартный порт для подключения к бд 5432, но если требуется, то можно передать иной
    user: str # имя пользователя postgresql(посмотреть psql->\du)
    password:str # пароль пользователя postgresql(задается при создании пользователя)
    db_name: str # название базы данных, к которой идет подключение (посмотреть psql->\l)

# сюда записывать конфиги
configs=[]

#! Пример:
# user = "server"# используется для примера
# configs = [
#     config(
#     condition = (True if user == "kyzmich" else False),
#     ssh_username="postgres",
#     ssh_host="128.128.128.128",
#     ssh_password="ssh_password",
#     host = "localhost",
#     port = 5432,
#     user = "kyzmich",
#     password = "ssh_password",
#     db_name = "name"
#     ),
#     config(
#         condition = (True if user=="server" else False),
#         host = "localhost",
#         user = "server",
#         password = "password",
#         db_name = "name"
#     )
# ]


#! Переменная, в которой записываются psql запросы на создание таблиц.
#* (в конце запроса обязательно ;)
# таблица log требуется для создания записей с логами()
#? Если такой таблицы не требуется, то при инициализации класса требуется либо задать active_log=None, либо не указывать вовсе.
create_tables = [
    """CREATE TABLE IF NOT EXISTS log (id SERIAL, type TEXT, date TEXT, text_log TEXT);"""
    ]

#? Пример:

# create_tables = [
#     """CREATE TABLE table1 (id integer, name TEXT);""",
#     """CREATE TABLE IF NOT EXISTS log (id SERIAL, type TEXT, date TEXT, text_log TEXT);"""
# ]


class column_type_class(BaseModel):
    
    integer: list | None=None
    string: list | None=None
    boolean: list | None=None
    jsonb: list | None=None
    timetz: list | None=None
    timestamptz: list | None=None

#* Переменная column_type содержит информацию о колонках в таблице(тип колонок) 
#* Данная информация требуется для корректного преобразования данных в psql запрос
#* Требуется указать названия всех колонок, которые будут использоваться во ВСЕХ таблицах 
#* см Пример по заполнению
column_type = column_type_class(

)

#? Пример:
# column_type = column_type_class(
#             integer= ["id", "user_id"],
#             string= ["login", "role", "email"],
#             boolean= ['admin'],
#             timetz= [],
#             timestamptz= ["date_registration"],
#             jsonb= ["tasks"]
#         )