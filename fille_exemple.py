import json
from connection import Connection
from orm_models import OrmColumn, OrmTable

if __name__ == '__main__':

    conn = Connection()
    with open('example.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    for table in data:
        print(table)
        columns = [OrmColumn(name=column['name']) for column in table['columns']]
        table: OrmTable = OrmTable(name=table['name'], columns=columns)
        conn.session.add(table)
    conn.session.commit()
    conn.session.close()


