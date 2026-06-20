"""Block until MySQL accepts connections (used at container startup)."""

from __future__ import annotations

import os
import sys
import time

import pymysql


def main() -> None:
    host = os.getenv("MYSQL_HOST", "mysql")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.environ["MYSQL_USER"]
    password = os.environ["MYSQL_PASSWORD"]
    database = os.environ["MYSQL_DATABASE"]
    attempts = int(os.getenv("MYSQL_WAIT_ATTEMPTS", "60"))
    delay = float(os.getenv("MYSQL_WAIT_DELAY", "2"))

    for attempt in range(1, attempts + 1):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=3,
            )
            conn.close()
            print(f"MySQL ready at {host}:{port}")
            return
        except Exception as exc:
            print(f"Waiting for MySQL ({attempt}/{attempts}) at {host}:{port}: {exc}")
            time.sleep(delay)

    print(f"MySQL not available at {host}:{port} after {attempts} attempts", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
