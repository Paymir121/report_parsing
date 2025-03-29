import json

from connection import Connection
from orm_models import ORMTableModel, ORMTableColumnModel, Base
def fill_example_tables_in_db():
    connection: Connection = Connection()
    Base.metadata.create_all(
        bind=connection.engine,
    )

    with open('example.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Заполнение базы данных
    for table_data in data['tables']:
        new_table: ORMTableModel = ORMTableModel(
            table_name=table_data['table_name'],
            rus_name=table_data['rus_name']
        )
        connection.session.add(new_table)
        connection.session.flush()  # Вызов flush, чтобы получить id для новых столбцов
        for column_data in table_data['columns']:
            if column_data['type']:
                new_column: ORMTableColumnModel = ORMTableColumnModel(
                    name=column_data['name'],
                    rus_name=column_data['rus_name'],
                    table_id=new_table.id,  # Используем id новой таблицы
                    type_column=column_data['type']
                )
            else:
                new_column: ORMTableColumnModel = ORMTableColumnModel(
                    name=column_data['name'],
                    rus_name=column_data['rus_name'],
                    table_id=new_table.id  # Используем id новой таблицы
                )
            connection.session.add(new_column)

    # Сохранение всех изменений в базе данных
    connection.session.commit()

    # Закрытие сессии
    connection.session.close()