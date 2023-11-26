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

# Load application configuration and logging
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def get_stats():
    logger.info("GET /stats request started")
    filename = app_config['datastore']['filename']

    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            current_stats = json.load(f)
        return current_stats, 200
    else:
        logger.error("Statistics file not found")
        return {"message": "Statistics do not exist"}, 404

def populate_stats():
    logger.info("Start Periodic Processing")

    filename = app_config['datastore']['filename']
    if not os.path.isfile(filename):
        logger.error("Statistics file not found. Using default stats.")
        current_stats = {
            'num_users': 0,
            'max_age': 0,
            'max_weight': 0,
            'num_food_log': 0,
            'max_calories': 0,
            'last_updated': "2000-01-01T00:00:00Z"
        }
    else:
        with open(filename, 'r') as f:
            current_stats = json.load(f)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

    try:
        response_users = requests.get(f"{app_config['eventstore']['url']}/personal-info", params={'timestamp': current_stats['last_updated']})
        response_food_logs = requests.get(f"{app_config['eventstore']['url']}/food-log", params={'timestamp': current_stats['last_updated']})

        if response_users.status_code == 200 and response_food_logs.status_code == 200:
            data_users = response_users.json()
            data_food_logs = response_food_logs.json()

            # Calculate new statistics
            max_age = max([current_stats['max_age']] + [int(u['age']) for u in data_users])
            max_weight = max([current_stats['max_weight']] + [int(u['weight']) for u in data_users])
            max_calories = max([current_stats['max_calories']] + [int(f['calories']) for f in data_food_logs])

            updated_data = {
                'num_users': current_stats['num_users'] + len(data_users),
                'max_age': max_age,
                'max_weight': max_weight,
                'num_food_log': current_stats['num_food_log'] + len(data_food_logs),
                'max_calories': max_calories,
                'last_updated': timestamp
            }

            # Write updated data to the file
            with open(filename, 'w') as f:
                json.dump(updated_data, f, indent=4)
            logger.debug(f"Updated data: {updated_data}")

        else:
            logger.error(f"Failed to retrieve data from APIs. Status: Users - {response_users.status_code}, Food Logs - {response_food_logs.status_code}")

    except Exception as e:
        logger.error(f"Error during processing: {e}")

    logger.info("Periodic Processing Ended")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start
