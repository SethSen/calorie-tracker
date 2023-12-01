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

# Check environment and load configuration files
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

# Check for existing data file and initialize it if necessary
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
        'last_updated': "2000-01-01T00:00:00Z"}
    file_path = app_config['datastore']['filename']
    with open(file_path, 'w') as data_json:
        json.dump(current_stats, data_json, indent=4)

def get_stats():
    if os.path.isfile(app_config['datastore']['filename']):
        f = open(app_config['datastore']['filename'])
        f_content = f.read()
        current_stats = json.loads(f_content)
        f.close()
        return current_stats, 201
    else:
        logger.error("File does not exist")
        return "stats do not exist", 404


def populate_stats():
    if os.path.isfile(app_config['datastore']['filename']):
        with open(app_config['datastore']['filename']) as f:
            current_stats = json.loads(f.read())
    else:
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

    logger.info("Start Periodic Processing")
    
    personal_info_url = requests.get(f"{app_config['eventstore']['url']}/personal-info", params={'start_timestamp':current_stats['last_updated'], 'end_timestamp': timestamp})
    food_log_url = requests.get(f"{app_config['eventstore']['url']}/food-log", params={'start_timestamp':current_stats['last_updated'], 'end_timestamp': timestamp})
    logger.info(f"There have been {len(personal_info_url.json())} personal info logs and {len(food_log_url.json())} food logged since {current_stats['last_updated']}")

    if personal_info_url.status_code != 200 or food_log_url.status_code != 200:
        logger.error('Error from personal info or food log received')
        return  # Exit the function if there's an error

    personal_info_response = personal_info_url.json()
    food_log_response = food_log_url.json()

    # Update max_age and num_users based on new data
    new_max_age = max([float(i["age"]) for i in personal_info_response], default=current_stats['max_age'])
    new_num_users = current_stats['num_users'] + len(personal_info_response)

    # Update max_weight and max_calories if new data is available
    new_max_weight = max([float(i['weight']) for i in personal_info_response], default=current_stats['max_weight'])
    new_max_calories = max([float(i['calories']) for i in food_log_response], default=current_stats['max_calories'])

    updated_stats = {
        'num_users': new_num_users,
        'max_age': new_max_age,
        'max_weight': new_max_weight,
        'num_food_log': current_stats['num_food_log'] + len(food_log_response),
        'max_calories': new_max_calories,
        'last_updated': timestamp
    }

    with open(app_config['datastore']['filename'], 'w') as f:
        f.write(json.dumps(updated_stats))

    logger.debug(f"The current data is {updated_stats}")
    logger.info("Processing period ended")



def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api('calorie-tracker.yml',base_path="/processing",strict_validation=True, validate_responses=True )
if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, debug=True, use_reloader=False)