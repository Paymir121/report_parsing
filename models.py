from orm_models import OrmTable, OrmColumn


class Column:
    def __init__(self,
                 name: str,
                 orm_model: OrmColumn
                 ):
        self.name: str = name
        self.orm_model: OrmColumn = orm_model

class Table:
    def __init__(
            self,
            name: str,
            columns: list[Column],
            orm_model: OrmTable
    ):
        self.orm_model: OrmTable = orm_model
        self.name: str = name
        self.columns: list[OrmColumn] = columns if columns else []
