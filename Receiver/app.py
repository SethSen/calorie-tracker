import connexion
from connexion import NoContent
import yaml
import logging.config
import uuid
from pykafka import KafkaClient
import datetime
import json
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

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

def get_kafka():
    retry_count = 0
    max_retries = app_config['kafka']['max_retries']
    sleep_time = app_config['kafka']['sleep_time']

    while retry_count < max_retries:
        try:
            logger.info(f"Trying to connect to Kafka, attempt {retry_count+1}")
            client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
            kafka_topic = client.topics[str.encode(app_config['events']['topic'])]
            producer = kafka_topic.get_sync_producer()
            logger.info("Connected to Kafka successfully")
            return client, producer
            
        except Exception as e:
            logger.error(f"Connection to Kafka failed: {str(e)}")
            time.sleep(sleep_time)
            retry_count += 1
    raise Exception("Failed to connect to Kafka after retries")

client, producer = get_kafka()

def generate_trace_id():
    """Generate a unique trace ID using UUID4 for correlating events across different systems."""
    return str(uuid.uuid4())

def send_kafka(event_type, body):
    """Send an event to a specified Kafka topic."""

    msg = {
        "type": event_type,
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": body
    }

    # Send the message to the Kafka topic
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

def PersonalInfo(body):
    """Handle incoming Personal Info event by sending it to Kafka."""
    traceid = generate_trace_id()
    body["trace_id"] = traceid
    logger.info(f"Received Personal Info event with trace ID: {traceid}")
    send_kafka("personal_info", body)
    return NoContent, 201

def FoodLog(body):
    """ Handle incoming Food Log event by sending it to Kafka. """
    traceid = generate_trace_id()
    body["trace_id"] = traceid
    logger.info(f"Received Food Log event with trace ID: {traceid}")
    send_kafka("food_log", body)
    return NoContent, 201


def healthCheck():
    return NoContent, 200


# Initialize Connexion app to integrate Flask with Swagger
app = connexion.FlaskApp(__name__, specification_dir='')
# Add API with validation options
app.add_api("calorie-tracker.yml", base_path="/receiver", strict_validation=True, validate_responses=True)

# Run the application if the script is the main program
if __name__ == "__main__":
    app.run(port=8080)
