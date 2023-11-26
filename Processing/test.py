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

def populate_stats():
    logger.info("Start Periodic Processing")
    
    # Load existing stats from file or initialize if not present
    filename = app_config['datastore']['filename']
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            current_stats = json.load(f)
    else:
        # Initialize stats if file doesn't exist
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

    # Construct the URL using app_config
    # personal_info_url = f"{app_config['eventstore']['url']}/personal-info?timestamp={current_stats['last_updated']}"
    # food_log_url = f"{app_config['eventstore']['url']}/food-log?timestamp={current_stats['last_updated']}"

    personal_info_url = requests.get(f"{app_config['eventstore']['url']}/personal-info", params={'timestamp':current_stats['last_updated'], 'end_timestamp':timestamp})
    food_log_url = requests.get(f"{app_config['eventstore']['url']}/food-log", params = {'timestamp': current_stats['last_updated'], 'end_timestamp': timestamp})

    # Fetch new data from event store APIs
    try:
        # Make HTTP requests to get new data
        personal_info_response = requests.get(personal_info_url)
        food_log_response = requests.get(food_log_url)

        # Check responses and log info or errors
        if personal_info_response.status_code == 200:
            info_events = personal_info_response.json()
            logger.info(f"Received {len(info_events)} new personal info events")
        else:
            logger.error("Failed to retrieve personal info events")
            return

        if food_log_response.status_code == 200:
            food_log_events = food_log_response.json()
            logger.info(f"Received {len(food_log_events)} new food log events")
        else:
            logger.error("Failed to retrieve food log events")
            return

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return

    # Process new events and update stats
    for event in info_events:
        # Update stats based on personal info events
        current_stats['num_users'] += 1
        current_stats['max_age'] = max(current_stats['max_age'], event.get('age', 0))
        current_stats['max_weight'] = max(current_stats['max_weight'], event.get('weight', 0))

    for event in food_log_events:
        # Update stats based on food log events
        current_stats['num_food_log'] += 1
        current_stats['max_calories'] = max(current_stats['max_calories'], event.get('calories', 0))

    # Update the last updated timestamp
    current_stats['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Save updated stats to the file
    with open(filename, 'w') as f:
        json.dump(current_stats, f, indent=4)

    logger.info("Finished Processing")


def get_stats():
    """
    API endpoint to retrieve current statistics.
    """
    logger.info("GET /stats request started")

    # Load stats from file
    filename = app_config['datastore']['filename']
    if not os.path.isfile(filename):
        logger.error("Statistics file not found")
        return {"message": "Statistics do not exist"}, 404

    with open(filename, 'r') as f:
        current_stats = json.load(f)

    logger.debug(f"Statistics: {current_stats}")
    logger.info("GET /stats request completed")
    return current_stats, 200

def init_scheduler():
    """
    Initialize and start a scheduler for periodic tasks.
    The scheduler runs the populate_stats function at configured intervals.
    """
    sched = BackgroundScheduler(daemon=True)
    # Schedule the populate_stats function to run periodically
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

# Initialize and configure the Connexion application
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
# Add API with strict validation and response validation
app.add_api('calorie-tracker.yml', strict_validation=True, validate_responses=True)

# Start the application and scheduler when running this script as the main program
if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, debug=True, use_reloader=False)
