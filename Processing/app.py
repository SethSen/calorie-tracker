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
    if os.path.isfile(app_config['datastore']['filename']):
        f = open(app_config['datastore']['filename'])
        f_content = f.read()
        json_object = json.loads(f_content)
        f.close()
        return json_object, 201
    else:
        logger.error("File does not exist")
        return "stats do not exist", 404


def populate_stats():
    if os.path.isfile(app_config['datastore']['filename']):
        f = open(app_config['datastore']['filename'])
        f_content = f.read()
        current_stats = json.loads(f_content)
        f.close()
    else:
        current_stats = {
            'num_users': 0,
            'max_age': 0,
            'max_weight': 0,
            'num_food_log': 0,
            'max_calories': 0,
            'last_updated': "2000-01-01T00:00:00Z"
        }

    logger.info("Start Periodic Processing")
    personal_info_url = requests.get(f"{app_config['eventstore']['url']}/personal-info", params={'timestamp':current_stats['last_updated']})
    food_log_url = requests.get(f"{app_config['eventstore']['url']}/food-log", params={'timestamp':current_stats['last_updated']})
    logger.info(f"There have been {len(personal_info_url.json())} personal info logs and {len(food_log_url.json())} food logs since {current_stats['last_updated']}")
    
    if personal_info_url.status_code != 200:
        logger.error(f'Error from personal info received: {personal_info_url.status_code}')
    elif food_log_url.status_code != 200:
        logger.error(f'Error from food log received: {food_log_url.status_code}')

    personal_info_response = personal_info_url.json()
    food_log_response = food_log_url.json()


    if len(personal_info_response):
        max_age = max(
            [
                current_stats['max_age'],
                max([float(i["age"]) for i in personal_info_response])
            ]
        )
        max_weight = max(
            [
                current_stats['max_weight'],
                max([float(i['weight']) for i in personal_info_response])
            ]
        )
    else: 
        max_age = current_stats['max_age']
        max_weight = current_stats['max_weight']
        
    if len(food_log_response):
        max_calories = max(
            [
                current_stats['max_calories'],
                max([float(i['calories']) for i in food_log_response])
            ]
        )
    else:
        max_calories = current_stats['max_calories']


    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    data = {
        'num_users': current_stats['num_users']+len(personal_info_response),
        'max_age': max_age,
        'max_weight': max_weight,
        'num_food_log': current_stats['num_food_log']+len(food_log_response),
        'max_calories': max_calories,
        'last_updated': timestamp
    }

    f = open(app_config['datastore']['filename'], 'w')
    f.write(json.dumps(data))
    f.close()
    logger.debug(f"The current data is {data}")
    logger.info(f"Processing period ended")


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
