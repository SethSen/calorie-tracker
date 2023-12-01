import connexion
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
import yaml
import logging.config
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import json
from personal_info import PersonalInfo
from food_log import FoodLog
from base import Base
import time
import os

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"
with open(app_conf_file, 'r') as f:
   app_config = yaml.safe_load(f.read())

db_user = app_config['datastore']['user']
db_password = app_config['datastore']['password']
db_hostname = app_config['datastore']['hostname']
db_port = app_config['datastore']['port']
db_name = app_config['datastore']['db']

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

# Logs Hostname
logger.info(f"Connected to MySQL database at {db_hostname}:{db_port}")

DB_ENGINE = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_hostname}:{db_port}/{db_name}')
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


max_retries = app_config["kafka"]["max_retries"]
current_retry = 0
while current_retry < max_retries:
    try:
        logger.info(f'Attempting to connect to Kafka. Retry count: {current_retry}')
        hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        break
    except Exception as e:
        logger.error(f'Connection to Kafka failed. Error:{str(e)}')
        sleep_time = app_config['kafka']['sleep_time']
        time.sleep(sleep_time)
        current_retry +=1
else:
    logger.error("Max Retries reached. Could not connect to Kafka")

def process_messages():
    """ Process event messages """
    logger.info("Starting Processing")
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)

    for msg in consumer:
        if msg is not None:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            logger.info(f"Message: {msg}")
            payload = msg["payload"]

            session = DB_SESSION()

            try:
                if msg["type"] == "food_log":
                    fl = FoodLog(
                        payload["trace_id"],
                        payload["user_id"],
                        payload["timestamp"],
                        payload["food_name"],
                        payload["quantity"],
                        payload["calories"],
                        payload["carbohydrates"],
                        payload["fats"],
                        payload["proteins"]
                    )
                    session.add(fl)

                elif msg["type"] == "personal_info":
                    pi = PersonalInfo(
                        payload["trace_id"],
                        payload["activity_level"],
                        payload["age"],
                        payload["height"],
                        payload["nutritional_goal"],
                        payload["sex"],
                        payload["user_id"],
                        payload["weight"]
                    )
                    session.add(pi)

                session.commit()
                logger.info("Data committed to the database.")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                session.rollback()
            finally:
                session.close()

            consumer.commit_offsets()



def get_personal_info(start_timestamp, end_timestamp):
    """ Gets personal info readings between start and end timestamps """
    session = DB_SESSION()
    try:
        start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.error(f"Error parsing timestamp: {e}")
        return {"message": "Invalid timestamp format"}, 400

    if start_timestamp_datetime >= end_timestamp_datetime:
        return {"message": "Start timestamp must be earlier than end timestamp"}, 400

    readings = session.query(PersonalInfo).filter(PersonalInfo.date_created >= start_timestamp_datetime, PersonalInfo.date_created < end_timestamp_datetime)
    results_list = [reading.to_dict() for reading in readings]
    session.close()
    return results_list, 200

def get_food_log(start_timestamp, end_timestamp):
    """ Gets food log readings between start and end timestamps """
    session = DB_SESSION()
    try:
        start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.error(f"Error parsing timestamp: {e}")
        return {"message": "Invalid timestamp format"}, 400

    if start_timestamp_datetime >= end_timestamp_datetime:
        return {"message": "Start timestamp must be earlier than end timestamp"}, 400

    readings = session.query(FoodLog).filter(FoodLog.date_created >= start_timestamp_datetime, FoodLog.date_created < end_timestamp_datetime)
    results_list = [reading.to_dict() for reading in readings]
    session.close()
    return results_list, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api('calorie-tracker.yml', base_path="/storage", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    
    app.run(port=8090)
