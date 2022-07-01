import sqlite3 as sq
from typing import Dict, List

with sq.connect('database.sqlite3') as conn:
    cursor = conn.cursor()


def fetchall(table: str, columns: List[str]) -> List[dict]:
    columns_str = ', '.join(columns)
    cursor.execute(f"select {columns_str} from {table}")
    result = []
    for row in cursor.fetchall():
        item = {}
        for index, value in enumerate(row):
            item[columns[index]] = value
        result.append(item)

    return result


def insert(table: str, column_dict: Dict) -> None:
    values = tuple(column_dict.values())
    columns = ', '.join(column_dict.keys())
    placeholders = ', '.join('?' * len(values))
    cursor.execute(f"insert into {table}({columns}) values({placeholders})", values)
    conn.commit()


def update(table: str, columns_dict: dict, index: int) -> None:
    new_values = tuple(columns_dict.values())
    column_list = [column+'=?' for column in columns_dict.keys()]
    columns = ', '.join(column_list)
    cursor.execute(f"update {table} set {columns} where id={index}", new_values)
    conn.commit()


def delete(table: str, index: int) -> None:
    cursor.execute(f"delete from {table} where id={index}")
    conn.commit()


def get_cursor() -> cursor:
    return cursor


def _init() -> None:
    with open('create_bases.sql', 'r') as file:
        script = file.read()
        cursor.executescript(script)
    conn.commit()
    


if __name__ == '__main__':
    _init()