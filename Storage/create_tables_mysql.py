import pymysql
import yaml

# Connect to the MySQL server

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Database connection parameters
user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']

# Connect to the MySQL server
db_conn = pymysql.connect(
    host=hostname,
    user=user,
    password=password,
    database=db,
    port=port
)

db_cursor = db_conn.cursor()

# Creating the personal_info table
personal_info_table = '''
CREATE TABLE personal_info (
id INT NOT NULL AUTO_INCREMENT,
trace_id VARCHAR(100) NOT NULL,
user_id INT NOT NULL,
age INT NOT NULL,
sex VARCHAR(10) NOT NULL,
height INT NOT NULL,
weight INT NOT NULL,
activity_level VARCHAR(50) NOT NULL,
nutritional_goal VARCHAR(50) NOT NULL,
date_created VARCHAR(100) NOT NULL,
CONSTRAINT personal_info_pk PRIMARY KEY (id))
'''

# Creating the food_log table
food_log_table = '''
CREATE TABLE food_log (
id INT NOT NULL AUTO_INCREMENT,
trace_id VARCHAR(100) NOT NULL,
user_id INT NOT NULL,
timestamp VARCHAR(100) NOT NULL,
food_name VARCHAR(250) NOT NULL,
quantity INT NOT NULL,
calories INT NOT NULL,
carbohydrates INT NOT NULL,
fats INT NOT NULL,
proteins INT NOT NULL,
date_created VARCHAR(100) NOT NULL,
CONSTRAINT food_log_pk PRIMARY KEY (id))
'''

db_cursor.execute(personal_info_table)
db_cursor.execute(food_log_table)
db_conn.commit()
db_conn.close()
