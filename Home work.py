import psycopg2


def create_database():
    conn = psycopg2.connect(
        dbname='clients_db',
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432'
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname='clients_db'")
    database_exists = cur.fetchone()
    if not database_exists:
        cur.execute('CREATE DATABASE clients_db')
    cur.close()
    conn.close()


def create_db(conn):
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS phones (
                client_id INTEGER,
                phone_number TEXT,
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            )
        ''')


def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO clients (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING id",
            (first_name, last_name, email)
        )
        client_id = cur.fetchone()[0]
        if phones:
            for phone in phones:
                cur.execute(
                    "INSERT INTO phones (client_id, phone_number) VALUES (%s, %s)",
                    (client_id, phone)
                )


def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO phones (client_id, phone_number) VALUES (%s, %s)",
            (client_id, phone)
        )


def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cur:
        update_query = "UPDATE clients SET "
        update_params = []
        if first_name:
            update_query += "first_name = %s, "
            update_params.append(first_name)
        if last_name:
            update_query += "last_name = %s, "
            update_params.append(last_name)
        if email:
            update_query += "email = %s, "
            update_params.append(email)
        update_query = update_query.rstrip(", ") + " WHERE id = %s"
        update_params.append(client_id)
        cur.execute(update_query, tuple(update_params))
        if phones is not None:
            cur.execute("DELETE FROM phones WHERE client_id = %s", (client_id,))
            for phone in phones:
                cur.execute(
                    "INSERT INTO phones (client_id, phone_number) VALUES (%s, %s)",
                    (client_id, phone)
                )


def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM phones WHERE client_id = %s AND phone_number = %s",
            (client_id, phone)
        )


def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM phones WHERE client_id = %s", (client_id,))
        cur.execute("DELETE FROM clients WHERE id = %s", (client_id,))


def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        query = "SELECT clients.id, clients.first_name, clients.last_name, clients.email, string_agg(phones.phone_number, ',') " \
                "FROM clients LEFT JOIN phones ON clients.id = phones.client_id " \
                "WHERE 1=1"
        params = []
        if first_name:
            query += " AND clients.first_name ILIKE %s"
            params.append('%' + first_name + '%')
        if last_name:
            query += " AND clients.last_name ILIKE %s"
            params.append('%' + last_name + '%')
        if email:
            query += " AND clients.email ILIKE %s"
            params.append('%' + email + '%')
        if phone:
            query += " AND phones.phone_number ILIKE %s"
            params.append('%' + phone + '%')
        query += " GROUP BY clients.id"
        cur.execute(query, params)
        return cur.fetchall()

# Создаем базу данных "clients_db", если она не существует
create_database()

with psycopg2.connect(database="clients_db", user="postgres", password="postgres") as conn:
    # Создаем таблицы "clients" и "phones", если они не существуют
    create_db(conn)

    # Добавление клиента Alex
    add_client(conn, 'Alex', 'Red', 'alex.smith@gmail.com', phones=['89012345678', '89112233334'])
    # Добавление клиента Kate
    add_client(conn, 'Kate', 'Fox', 'kate.fox@mail.ru', phones=['89185001020'])

    # Добавление телефона для клиента с ID 2
    add_phone(conn, client_id=2, phone='89897771122')

    # Изменение данных клиента с ID 2
    change_client(conn, 2, first_name='Mary', phones=['89605059494'])

    # Удаление телефона для клиента с ID 1
    delete_phone(conn, 1, '89012345678')

    # Удаление клиента с ID 1
    delete_client(conn, 1)

    # Поиск клиентов с фамилией Fox
    results = find_client(conn, last_name='Fox')
    for row in results:
        print(row)
