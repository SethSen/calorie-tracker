# Importing necessary modules
import logging
import uuid
import connexion
import json
import datetime
from connexion import NoContent
import os
from swagger_ui_bundle import swagger_ui_path
import requests
import yaml
import logging.config
from pykafka import KafkaClient
from flask_cors import CORS, cross_origin

# Load application configuration from YAML file
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load logging configuration from YAML file
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Initialize logger
logger = logging.getLogger('basicLogger')

def get_personal_info(index):
    """ Retrieves a personal information record from Kafka topic based on the index."""
    # Configure Kafka client
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    
    # Create Kafka consumer
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving personal info at index %d" % index)
    
    try:
        lst = []
        # Read messages from Kafka topic
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            logger.debug(msg['type'])
            # Check for specific type of message
            if msg['type'] == 'personal_info':
               lst.append(msg) 
        # Return the message at the specified index
        logger.debug(lst[index])  
        return lst[index], 201

    except IndexError:
        # Handle case where index is out of range
        logger.error("No more messages found")
    logger.error("Could not find personal info at index %d" % index)
    return {"message": "Not Found"}, 404

def get_food_log(index):
    """ Retrieves a food log record from Kafka topic based on the index."""
    # Configuration and setup similar to get_personal_info function
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving food_log at index %d" % index)
    
    try:
        lst = []
        # Read and process messages from Kafka
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            logger.debug(msg)
            if msg['type'] == 'food_log':
               lst.append(msg) 
        return lst[index], 201

    except IndexError:
        logger.error("No more messages found")
    logger.error("Could not find food log at index %d" % index)
    return {"message": "Not Found"}, 404

# Initialize Connexion, which integrates Flask with Swagger
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("calorie-tracker.yml", strict_validation = True, validate_responses=True)

# Run the application if this script is executed as the main program
if __name__ == "__main__":
    app.run(port=8110)
