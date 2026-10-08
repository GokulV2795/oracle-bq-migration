import os

import oracledb
from dotenv import load_dotenv


load_dotenv()


def get_oracle_connection():
    host = os.getenv("ORACLE_HOST")
    port = os.getenv("ORACLE_PORT")
    service_name = os.getenv("ORACLE_SERVICE_NAME")
    username = os.getenv("ORACLE_USERNAME")
    password = os.getenv("ORACLE_PASSWORD")

    if not all(
        [
            host,
            port,
            service_name,
            username,
            password,
        ]
    ):
        raise ValueError(
            "Missing Oracle connection configuration in .env"
        )

    dsn = oracledb.makedsn(
        host,
        int(port),
        service_name=service_name,
    )

    return oracledb.connect(
        user=username,
        password=password,
        dsn=dsn,
    )