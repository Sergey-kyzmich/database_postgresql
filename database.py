# Информация о типах данных: https://www.postgresql.org/docs/current/datatype.html
import sys
from colorama import Fore as F, Style as S
import inspect
import pydantic
import datetime

try:#* Если запускается из текущей директории
    import create_connect as create_connect
    from config import configs, create_tables, column_type
except:#* Если запускается из директории ниже и данный файл находится в ./database
    import database.create_connect as create_connect
    from database.config import configs, create_tables, column_type

#* Функция вызывается при запуске кода и выполняет подключение к серверу
class database:
    def __init__(self, active_log: str|None=None, test_mode:bool|None=None) -> None:
        """Инициализация класса database.\n
        На вход принимает:\n
        *active_log* str|None=None - активирует сохранение действий ("all"-всех, "main"-только основных(error/connect/close_connect), None - отключает данную функцию) в бд в таблицу(log). Не является обязательным аргументом\n
        *test_mode* bool|None=None - значение True активирует вывод всех действий в консоль. Не является обязательным аргументом\n"""
        self.column_type = column_type
        #? active_log = True - сохранение всех действий в бд
        #? active_log = False - сохранение только основных действий в бд
        #? active_log = None - полностью отлючить сохранение в бд
        self.active_log = True if active_log=="all" else (False if active_log!=None else None)
        self.test_mode = test_mode

        
#* Функция осуществляет подключение к базе данных, используя заранее подготовленные профиля в config.py
    async def connect(self):
        """Подключение к базе данных.(Возвращает True, если подключение прошло успешно, иначе текст ошибки)\n
        Данных на вход не требуется.\n
        Внимание! Является асинхронной функцией."""
        try:
            #* Отображение информационного сообщения
            print(f"{F.GREEN}INFO{S.RESET_ALL}:     connecting to database.")


            class kyzmich():
                def __init__(self) -> None:
                    self.ssh_username="postgres"
                    self.ssh_host="147.45.103.230"
                    self.ssh_password="4Di9cvtuRr"
                    self.host = "localhost"
                    self.port = 5432
                    self.user = "kyzmich"
                    self.password = "kyzmich_project"
                    self.db_name = "database"

            # config = configs[0]#kyzmich()
            # if True:
            #* Поиск подходящего конфига
            for config in configs:
                if config.condition:
                    print(config)
                    #* выбор типа подключения (по ssh, либо локально)
                    if config.ssh_username!=None and config.ssh_host!=None and config.ssh_password!=None:
                        print("ssh")
                        ret = await create_connect.connect_use_ssh(config=config)
                    else:
                        print("localhost")
                        ret = await create_connect.connect_use_localhost(config=config)
                break
            print(f"{F.GREEN}INFO{S.RESET_ALL}:     connected to db use profile: {F.CYAN}{config.user}{S.RESET_ALL}.")
            #* Проверка на удачное подключение к серверу.
            if ret.error==None and ret.value!=None:
                conn, ssh_tonel = ret.value #*Если подключение установлено
            else:#* В ином случае проверка типа подключения
                await self.add_log(
                    text=ret.error,
                    type="ERROR"
                )
                if self.test_mode:
                    print(ret.error)
                return self.ret(error=ret.error)

            conn.autocommit = True  #* Включение автосохранения при запросах к бд
            self.conn = conn #* Создание экземпляра conn, для закрытия подключения по завершению работы
            self.cursor=conn.cursor() #* Создание экземпляра cursor, с помощью которого ведется работа с бд
            self.ssh_tonel=ssh_tonel #*Сохранение экземпляра ssh_tonel для его закрытия по завершению работы 
            
            #* Фиксация действий в бд
            await self.add_log(
                text=f"Подключение к бд успешно установлено! Используется профиль: {config.user}",
                type="INFO"
            )
                
            return self.ret(value=True)
        
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

        

    #* Функция используется после выполнения кода для закрытия активных подключений
    async def close_connect(self):
        """Закрытие подключения к базе данных.\n 
        Данные на вход не требуются.\n
        Внимание! Является асинхронной функцией."""
        try:
            self.conn.close()#* Закрытие подключения к бд
            if self.ssh_tonel!=None:self.ssh_tonel.close()#* Закрытие подключения к серверу(если используется ssh тунель)
            
            #* Фиксация действий в бд
            await self.add_log(
                text=f"Подключение успешно завершено.",
                type="INFO"
            )
            #* Проверка на тестовый режим
            if self.test_mode:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Подключение успешно завершено.")
                
            return self.ret(value=True)
        
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)


        
    async def create_table(self):
        """Создание таблиц, если не созданы ранее.\n 
        Данные на вход не требуются.\n
        Внимание! Является асинхронной функцией.
        """
        try:
            for execute in create_tables:
                self.cursor.execute(execute)

            #* Проверка на active_log
            if self.active_log==True:
                await self.add_log(
                    text="Проверка/Создание таблиц успешно завершена",
                    type="INFO"
                )

            #* Проверка на test_mode
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Проверка/Создание таблиц успешно завершена")
            return self.ret(value=True)
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

        

    #* Функция для выполнения не стандартных запросов
    async def execute(self, execute: str):
        """Используется, если требуется выполнить не стандартный запрос\n
        Возвращает *cursor*\n
        На вход принимает:
        *execute* str - текст запроса для postgesql таблицы \n
        Внимание! Является асинхронной функцией."""
        try:
            #* Проверка, что запрос имеет закрывающий символ
            execute = execute if execute[-1]==';' else execute+';'
            self.cursor.execute(execute)

            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
            
            execute = execute.replace('\n', '').replace("  ", "")
            if self.active_log==True:
                return await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO",
                    ret = self.ret(value=self.cursor)
                )
            else:
                return self.ret(value=self.cursor)
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

    #* Функция используется для получения колонки значений
    async def get_column(self, column: str | list, table: str, arg: str|None=None):
        """Возвращает столбец(class с ключами value(если ответ был получен), либо error(если запрос вернул ошибку))\n
        На вход принимает: \n
        *column* str - имя столбца, записи которого требуется получить(Так-же может принимать массив столбцов) \n
        *table* str - имя таблици, записи из которой требуется получить\n
        *arg* str - дополнение к запросу, если требуется получить выборку из ответа. Не является обязательным аргументом\n
        Внимание! Является асинхронной функцией."""
        try:
            #* Если было переданно несколько столбцов
            if type(column)==list:
                execute = f"""SELECT {''.join([c+', ' for c in column])[:-2]} FROM {table} {arg if arg !=None else ''};"""
            #* Если был передан один столбец
            elif type(column)==str:
                execute = f"""SELECT {column} FROM {table} {arg if arg !=None else ''};"""

            self.cursor.execute(execute)#* Выполнение запроса
            
            #* фиксация действий
            execute = execute.replace('\n', '').replace("  ", "")
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
            
            if self.active_log==True:
                return await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO",
                    ret = self.ret(value=self.cursor.fetchall())
                )
            
            else:
                return self.ret(value=self.cursor.fetchall())
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)


    #* Функция используется для получения всех данных из таблицы
    async def get_all(self, table: str, arg: str | None=None) -> list:
        """Возвращает всю таблицу.(class с ключами value(если ответ был получен), либо error(если запрос вернул ошибку)) \n
        На вход принимает: \n
        *table* str - имя таблицы, которую требуется получить \n
        Внимание! Является асинхронной функцией."""
        
        #* создание запроса
        execute = f"""SELECT * FROM {table} {arg if arg !=None else ''};"""
        self.cursor.execute(execute)#* Выполнение запроса
        #* фиксация действий
        execute = execute.replace('\n', '').replace("  ", "")
        if self.test_mode==True:
            print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
        
        if self.active_log==True:
            return await self.add_log(
                text=f"""Запрос к бд [{execute}] успешно выполнен""",
                type="INFO",
                ret = self.ret(value=self.cursor.fetchall())
            )
        else:
            return self.ret(value=self.cursor.fetchall())
        
        # except Exception as e:
        #     error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
        #     await self.add_log(
        #         text=error,
        #         type="ERROR"
        #     )
        #     if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
        #     return self.ret(error=error)
        

    #* Функция используется для получения определенной записи из таблицы
    async def get(self, id: int|str, key:str, table:str, arg: str|None=None) -> list:
        """Возвращает данные о записи.(class с ключами value(если ответ был получен), либо error(если запрос вернул ошибку)) \n
        На вход принимает: \n
        *id* int | str - идентификатор записи \n
        *key* str - имя столбца, по которому ведется поиск \n
        *table* str - имя таблицы, из которой требуется получить запись\n
        *arg* str - дополнение к запросу, если требуется получить выборку из ответа. Не является обязательным аргументом\n
        Внимание! Является асинхронной функцией.
        """
        try:
            #* Создание запроса
            execute = f"""SELECT * FROM {table} WHERE {key}={id if type(id)==int else f"'{id}'"} {arg if arg !=None else ''};"""
            self.cursor.execute(execute)#* Выполнение запроса

            #* фиксация действий
            execute = execute.replace('\n', '').replace("  ", "")
            
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
    
            if self.active_log==True:
                return await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO",
                    ret = self.ret(value=self.cursor.fetchall())
                )
            else:
                return self.ret(value=self.cursor.fetchall())
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

    #* Функция используется для создания записи в бд
    async def create(self, data: dict, table: str, arg: str|None=None, type_data: list | None=None):
        """Создает запись в таблице.
        На вход принимает:
        *data* dict - словарь, где перечислены данные для заполнения и в качестве ключей указаны названия столбцов\n
        *table* str - имя таблици, запись в которой требуется сделать\n
        *arg* str - дополнение к запросу, если требуется получить выборку из ответа. Не является обязательным аргументом\n
        *type_data* list - массив, в котором описывается тип входных данных(в формате строки)(каждый id в массиве соответствует порядковому номеру ячейки в data). 
        Не является обязательным аргументом. допустимые типы: ("integer" - integer, "string" - string, "boolean" - boolean, "timetz" - time with time zone, "timestamptz" - datetime with time zone, "jsonb" - массив с ячейками json)
        Внимание! Является асинхронной функцией."""
        #id подставляется автоматически(type: serial). Для этого требуется указать значение DEFAULT
        #требуется учесть ситуацию, когда ключи раставлены не в порядке столбцов таблицы
        
        try:
            #* Создание переменной array_data(массив строк, в котором перечислены все данные для записи в требуемом формате)
            array_data = await self.set_values_from_type(data=data, type_data=type_data)

            if type(array_data)!= list:#* если при преобразовании возникла ошибка
                print("error:", array_data)
                return self.ret(error=f"{array_data}")
            #* если при создании array_data ошибок не возникло
            execute = f"""INSERT INTO {table} 
            ({''.join([item+', ' for item in data])[:-2]}) 
            VALUES 
            ({''.join([x for x in array_data])}) 
            {arg if arg!=None else ''};"""
            #* Выполнение запроса
            self.cursor.execute(execute)

            execute = execute.replace('\n', '').replace("  ", "")
            #* фиксация действий
            if self.active_log==True:
                await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO"
                )
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
            
            return self.ret(value=True)
        
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

    #* Функция используется для обновления информации в таблице        
    async def update(self, id: int| str, key: str, data: dict, table: str, arg: str|None=None, type_data: list | None = None):
        """Обновляет запись в таблице.\n
        На вход принимает:\n
        *id* int | str - идентификатор записи \n
        *key* str - имя столбца, по которому ведется поиск \n
        *data* dict - словарь, где перечислены данные для обновления и в качестве ключей указаны названия столбцов\n
        *table* str - имя таблици, в которой требуется обновить запись\n
        *arg* str - дополнение к запросу, если требуется получить выборку из ответа. Не является обязательным аргументом\n
        *type_data* list - массив, в котором описывается тип входных данных(в формате строки)(каждый id в массиве соответствует порядковому номеру ячейки в data). 
        Не является обязательным аргументом. допустимые типы: ("integer" - integer, "string" - string, "boolean" - boolean, "timetz" - time with time zone, "timestamptz" - datetime with time zone, "jsonb" - массив с ячейками json)
        Внимание! Является асинхронной функцией."""
        try:
            #* Создание переменной array_data(массив строк, в котором перечислены все данные для записи в требуемом формате)
            array_data = await self.set_values_from_type(data=data, type_data=type_data)
            
            #*  Проверка кол-ва данных для изменения
            #* (для нескольких элементов  один запрос, 
            #* для 1-го элемента требуется другой )
            if len(array_data)>1:#* Если требуется обновить несколько ячеек
                execute = f"""UPDATE {table} SET
                ({''.join([item+', ' for item in data])[:-2]}) 
                    =
                ({''.join([x for x in array_data])}) 
                WHERE {key}={id if type(id)==int else f"'{id}'"} 
                {arg if arg!=None else ''};"""
            else:#* Если требуется обновить одну ячейку
                execute = f"""UPDATE {table} SET 
                 {''.join([item+', ' for item in data])[:-2]} 
                =
                {''.join([x for x in array_data])} 
                {arg if arg!=None else ''};"""
            self.cursor.execute(execute)#* Выполнение запроса

            #* фиксация действий
            execute = execute.replace('\n', '').replace("  ", "")
            if self.active_log==True:
                await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO"
                )
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
            
            return self.ret(value=True)
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        
                    

    #* Функция используется для удаления записи из таблицы
    async def delete(self, id: int|str, key:str, table:str, arg: str|None=None):
        """Удаляет запись из таблицы(если надо удалить одно из значений, используйте update). \n
        На вход принимает: \n
        *id* int | str - идентификатор записи \n
        *key* str - имя столбца, по которому ведется поиск \n
        *table* str - имя таблицы, из которой удаляется запись\n
        *arg* str - дополнение к запросу, если требуется получить выборку из ответа. Не является обязательным аргументом\n
        Внимание! Является асинхронной функцией.
        """
        try:
            #* Создание запроса
            execute = f"""DELETE FROM {table} 
            WHERE {key}={id if type(id)==int else f"'{id}'"} 
            {arg if arg!=None else ''};"""

            self.cursor.execute(execute)#* Выполнение запроса
            
            #* фиксация действий
            execute = execute.replace('\n', '').replace("  ", "")
            if self.active_log==True:
                await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO"
                )
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
            
            return self.ret(value=True)
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

        

    #* Функция требуется для получения кол-ва записей в таблице
    async def len(self, table: str, arg: str|None=None):
        """Возвращает кол-во записей в таблице.(class с ключами value(если ответ был получен), либо error(если запрос вернул ошибку)) \n
        На вход принимает: \n
        *table* str - имя таблицы, длину которой требуется получить.
        *arg* str - дополнение к запросу, если требуется получить выборку из ответа. Не является обязательным аргументом\n
        Внимание! Является асинхронной функцией."""
        try:
            #* Создание запроса
            execute = f"SELECT id FROM {table} {arg if arg!=None else ''};"
            self.cursor.execute(execute) #* Выполнение запроса

            #* фиксация действий
            execute = execute.replace('\n', '').replace("  ", "")
            if self.test_mode==True:
                print(f"{F.GREEN}INFO:{S.RESET_ALL}     Запрос к бд [{F.YELLOW}{execute}{S.RESET_ALL}] успешно выполнен")
    
            if self.active_log==True:
                return await self.add_log(
                    text=f"""Запрос к бд [{execute}] успешно выполнен""",
                    type="INFO",
                    ret = self.ret(value=len(self.cursor.fetchall()))
                )
            else:
                return self.ret(value=len(self.cursor.fetchall()))
        
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        


    async def add_log(self, text:str, type: str, **kvarg):
        """Создает запись в таблице log.
        Если при инициализации класса не был передан active_log(или было передано None), до запись проводиться не будет.
        Данные на вход:
        *text* str - текст записи, которую требуется сделать\n
        *type* str - тип записи(ERROR/INFO)\n
        *ret* any - доп параметр, в который передается информация, которую требуется вернуть в return(костыль для database.py)
        Внимание! Является асинхронной функцией."""
        try:
            if self.active_log!=None:
                text = text.replace("'", '"')
                execute = f"""INSERT INTO log (id, type, date, text_log) VALUES (DEFAULT, '{type}', '{f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}'}', '{text}')"""
                self.cursor.execute(execute)
                
                # print("ret" in kvarg)
                if "ret" in kvarg:
                    return kvarg["ret"]
                else:
                    return self.ret(value=True)
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

    class ret(pydantic.BaseModel):
        value: list | str | int | bool | None = None
        error: str | None = None

    #* Класс содержит информацию о столбцах, использующихся в бд(требуется для составления коректного запроса к бд)


    async def set_values_from_type(self, data: dict, type_data: list | None = None):
        try:
            array_data = []
            for i in range(len(data.items())):
                l = ''
                item = list(data.items())[i][0]# ключ элемента под номером {i}

                # {f'DEFAULT' if ("id" in data and data["id"]==None) else ('' if "id" not in data else data['id'])}
                if item == "id":#Проверка на id
                    l+=f"""{'DEFAULT, 'if data['id']==None else f'{data["id"]}, '}"""
                elif item in self.column_type.integer or (type_data!= None and type_data[i]=="integer"):#проверка на целое число
                    l+=f"{data[item]}, "
                elif item in self.column_type.string or (type_data!= None and type_data[i]=="string"):#проверка на строковое заначение
                    l+=f"'{data[item]}', "
                elif item in self.column_type.boolean or (type_data!= None and type_data[i]=="boolean"):#проверка на булевое значение
                    if data[item]==True: l+=f"TRUE, "
                    else: l+=f"FALSE, "
                elif item in self.column_type.timetz or (type_data!= None and type_data[i]=="timetz"):#проверка на значение времени+tz
                    l+=f"'{data[item]}'::timetz, "
                elif item in self.column_type.timestamptz or (type_data!= None and type_data[i]=="timestamptz"):#проверка на значение даты+времени+tz
                    l+=f"'{data[item]}'::timestamptz, "
                elif item in self.column_type.jsonb or (type_data!= None and type_data[i]=="jsonb"):#проверка на массив json-ов
                        #Данный алгоритм перебирает значения в массиве json-ов и записывает их в верном формате
                        l += "'["
                        for j in data[item]:
                            l+="{"
                            for k in j:
                                l+=f'''"{k}": {f"{j[k]}, " if type(j[k])==int else f'"{j[k]}", '}'''
                            l = l[:-2]
                            l += "}, "
                        l = l[:-2]
                        l += "]'::jsonb, "
                array_data.append(l)
            array_data[-1] = array_data[-1][:-2]
            # print(f"{array_data=}")
            return array_data
        except Exception as e:
            error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
            await self.add_log(
                text=error,
                type="ERROR"
            )
            if self.test_mode:print(f"{F.RED}{error}{S.RESET_ALL}")
            return self.ret(error=error)
        

if __name__=="__main__":
    from asyncio import run
    db = database(test_mode=True)
    run(db.connect())
    print(run(db.get_all(table="users")).value)