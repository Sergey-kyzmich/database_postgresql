import psycopg2
from sshtunnel import SSHTunnelForwarder
import asyncio
from colorama import Fore as F, Style as S
import pydantic
import sys, inspect

class ret(pydantic.BaseModel):
    value: list | str | int | bool | None = None
    error: str | None = None

async def connect_use_localhost(config):
    try:
        params = {
                    'database': config.db_name,
                    'user': config.user,
                    'password': config.password,
                    'host': config.host,
                    'port': 5432
                    }
        conn = psycopg2.connect( **params)
        print(f"{F.GREEN}INFO{S.RESET_ALL}:     connected to db use profile: {F.CYAN}{config.user}{S.RESET_ALL}.")
        conn
        return ret(value=(conn, None))

    except Exception as e:
        error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"

        return ret(error=error)


async def connect_use_ssh(config):
    try:
        server = SSHTunnelForwarder(
            (config.ssh_host, 22),
            ssh_username=config.ssh_username,
            ssh_password=config.ssh_password,
            remote_bind_address=(config.host, 5432))
        server.start()
        params = {
            'database': config.db_name,
            'user': config.user,
            'password': config.password,
            'host': config.host,
            'port': server.local_bind_port
            }
        conn = psycopg2.connect(**params)
        return ret(value=(conn, server))

    except Exception as e:
        error =f"{sys.exc_info()[1]} | function: {inspect.trace()[-1][3]} | line: {sys.exc_info()[2].tb_lineno} |  path: {inspect.trace()[0][1]}"
        return ret(error=error)