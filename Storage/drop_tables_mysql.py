import mysql.connector
import yaml

# Connect to the MySQL server
# conn = mysql.connector.connect(host='localhost', user='root', password='password', database='calorie_tracker')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']


db_conn = mysql.connector.connect(
    host=hostname,
    user=user,
    password=password,
    database=db,
    port=port,
    auth_plugin='mysql_native_password')

db_cursor = db_conn.cursor()

db_cursor.execute("""
DROP TABLE food_log, personal_info
""")

db_conn.commit()
db_conn.close()
