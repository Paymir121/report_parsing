# Описание
### О проекте
Десктопное приложение для парсинга отчетов excel в **PostgreSQL**
## Основная логика
- Характеристики таблиц в файле examlpe.json
- при запуске файла fill_db_example.py в БД добавляются характеристики целевых таблиц. Данные хранятся в таблице tables и tables_columns
- Пользователь выбирает excel файл
- Приложение парсит файл и вставляет данные в базу данных

### Технологии
- **Python - 3.9**
- **PostgreSQL - 13.10**
- **PySide - 6**
- **SQLAlchemy**

### Авторы
- [Nikki Nikonor](https://github.com/Paymir121)

## Для запуска проекта вам понадобится:

### Клонирование репозитория:
Просите разрешение у владельца репозитория( можно со слезами на глазах)
Клонируете репозиторий:

```bash
    git clone  git@github.com:Paymir121/report_parsing.git
```

### Cоздать  виртуальное окружение:
```
    python -m venv venv
```

# активировать виртуальное окружение, Если у вас Linux/macOS
```
    source venv/bin/activate
```
# Активировать виртуальное окружение, Если у вас windows
```
    source venv/scripts/activate
```

### Установить зависимости из файла requirements.txt:
```
    pip install -r requirements.txt
```

### Запуск проекта:
```
    python main.py
```