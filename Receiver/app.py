import connexion
from connexion import NoContent
import yaml
import logging.config
import uuid
from pykafka import KafkaClient
import datetime
import json
import time

# Load application configuration from 'app_conf.yml'
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load logging configuration from 'log_conf.yml'
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Initialize the logger with the specified configuration
logger = logging.getLogger('basicLogger')
max_retries = app_config["kafka"]["max_retries"]
current_retry = 0
while current_retry < max_retries:
    try:
        logger.info(f'Attempting to create Kafka Client. Retry count: {current_retry}')
        client = KafkaClient(hosts=f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
        topic = client.topics[str.encode(app_config['events']['topic'])]
        logger.info(f'Succesful connection')
        break
    except Exception as e:
        logger.error(f'Kafka creation failed. Error:{str(e)}')
        sleep_time = app_config['kafka']['sleep_time']
        time.sleep(sleep_time)
        current_retry +=1
else:
    logger.error("Max Retries reached. Could not connect to Kafka")

def generate_trace_id():
    """Generate a unique trace ID using UUID4 for correlating events across different systems."""
    return str(uuid.uuid4())

def send_kafka(event_type, body):
    """Send an event to a specified Kafka topic."""
    logger.info(f"Sending {event_type} event to Kafka")
    # Set up Kafka client
    host = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=host)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()

    # Create the message with event details
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

# Initialize Connexion app to integrate Flask with Swagger
app = connexion.FlaskApp(__name__, specification_dir='')
# Add API with validation options
app.add_api("calorie-tracker.yml", strict_validation=True, validate_responses=True)

# Run the application if the script is the main program
if __name__ == "__main__":
    app.run(port=8080)
