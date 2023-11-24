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

# Load the configuration and logging
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Database setup
user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']
connection_str = f"mysql+pymysql://{user}:{password}@{hostname}:{port}/{db}"
DB_ENGINE = create_engine(connection_str)
Session = sessionmaker(bind=DB_ENGINE)
Base.metadata.create_all(DB_ENGINE)

def get_personal_info(timestamp):
    """ Gets new personal info readings after the timestamp """
    session = Session()
    try:
        timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.error(f"Error parsing timestamp: {e}")
        return {"message": "Invalid timestamp format"}, 400
    readings = session.query(PersonalInfo).filter(PersonalInfo.date_created >= timestamp_datetime)

    results_list = [reading.to_dict() for reading in readings]
    session.close()
    return results_list, 200

def get_food_log(timestamp):
    """ Gets new food log readings after the timestamp """
    session = Session()
    try:
        timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.error(f"Error parsing timestamp: {e}")
        return {"message": "Invalid timestamp format"}, 400
    readings = session.query(FoodLog).filter(FoodLog.date_created >= timestamp_datetime)

    results_list = [reading.to_dict() for reading in readings]
    session.close()
    return results_list, 200

def process_messages():
    """ Process incoming Kafka messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)

    for msg in consumer:
        if msg is not None:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            logger.info(f"Message: {msg}")
            payload = msg["payload"]

            session = Session()

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



# Flask App Setup
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("calorie-tracker.yml", strict_validation=True, validate_responses=True)

# Thread for Kafka
def start_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

if __name__ == "__main__":
    start_kafka_thread()
    app.run(port=8090)