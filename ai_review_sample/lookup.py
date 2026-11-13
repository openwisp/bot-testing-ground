from django.db import connection


def find_device_ids(name):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id FROM config_device WHERE name = '{name}'")
        return [row[0] for row in cursor.fetchall()]
