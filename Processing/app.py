# Import necessary libraries
import connexion
import yaml
import logging.config
import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
from flask_cors import CORS, cross_origin

# Load application configuration from 'app_conf.yml'
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load logging configuration from 'log_conf.yml'
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Initialize logger
logger = logging.getLogger('basicLogger')

def get_stats():
    logger.info("GET /stats request started")
    filename = app_config['datastore']['filename']

    try:
        with open(filename, 'r') as f:
            current_stats = json.load(f)
    except FileNotFoundError:
        logger.error("Statistics file not found")
        return {"message": "Statistics do not exist"}, 404

    logger.debug(f"Statistics: {current_stats}")
    logger.info("GET /stats request completed")
    return current_stats, 200


def populate_stats():
    logger.info("Start Periodic Processing")
    
    filename = app_config['datastore']['filename']
    try:
        with open(filename, 'r') as f:
            current_stats = json.load(f)
    except FileNotFoundError:
        logger.error("Statistics file not found")
        current_stats = {
            'num_users': 0,
            'max_age': 0,
            'max_weight': 0,
            'num_food_log': 0,
            'max_calories': 0,
            'last_updated': "2000-01-01T00:00:00Z"
        }

    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    personal_info_url = f"{app_config['eventstore']['url']}/personal-info?timestamp={current_stats['last_updated']}&end_timestamp={timestamp}"
    food_log_url = f"{app_config['eventstore']['url']}/food-log?timestamp={current_stats['last_updated']}&end_timestamp={timestamp}"

    try:
        personal_info_response = requests.get(personal_info_url)
        food_log_response = requests.get(food_log_url)

        if personal_info_response.status_code == 200:
            info_events = personal_info_response.json()
            logger.info(f"Received {len(info_events)} new personal info events")
        else:
            logger.error("Failed to retrieve personal info events")
            info_events = []

        if food_log_response.status_code == 200:
            food_log_events = food_log_response.json()
            logger.info(f"Received {len(food_log_events)} new food log events")
        else:
            logger.error("Failed to retrieve food log events")
            food_log_events = []

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        info_events = []
        food_log_events = []

    for event in info_events:
        current_stats['num_users'] += 1
        current_stats['max_age'] = max(current_stats['max_age'], event.get('age', 0))
        current_stats['max_weight'] = max(current_stats['max_weight'], event.get('weight', 0))

    for event in food_log_events:
        current_stats['num_food_log'] += 1
        current_stats['max_calories'] = max(current_stats['max_calories'], event.get('calories', 0))

    current_stats['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(filename, 'w') as f:
        json.dump(current_stats, f, indent=4)

    logger.info("Finished Processing")

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

# Initialize and configure the Connexion application
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api('calorie-tracker.yml', strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, debug=True, use_reloader=False)
