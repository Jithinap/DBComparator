import json
import mysql.connector
import unittest

def check_if_table_empty(dbname, username, password, tablenames):
    conn = None

    try:
        conn = mysql.connector.connect(
            host=dbname,
            user=username,
            password=password,
            database='scripting'
        )
        cursor = conn.cursor()

        for table in tablenames:
            query = f"SELECT COUNT(*) FROM {table}"
            cursor.execute(query)

            table_data_status = cursor.fetchone()
            print(f"Table {table} contains {table_data_status[0]} rows")

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

    return True

def read_test_data_from_file(filename):
    try:
        with open(filename, 'r') as file:
            test_data = json.load(file)
        return test_data
    except FileNotFoundError:
        print(f"Config file not found: {filename}")
    except Exception as e:
        print(f"Error reading config file: {filename} : {str(e)}")
        return []

class TestTableHavingData(unittest.TestCase):
    def test_table_having_data(self):
        test_data = read_test_data_from_file('testdata_for_mysql_scripting_db.json')
        for data in test_data:
            dbname = data["hostname"]
            username = data["username"]
            password = data["password"]
            tablenames = data["tablename"]
            if not isinstance(tablenames, list):
                tablenames = [tablenames]
            table_data = check_if_table_empty(dbname, username, password, tablenames)
            self.assertTrue(table_data, f"\nWarning: {tablenames} tables are having data")

if __name__ == '__main__':
    unittest.main()
