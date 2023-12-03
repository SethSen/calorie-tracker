import connexion
import yaml
import logging
import logging.config
import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os.path
from flask_cors import CORS, cross_origin
from connexion import NoContent

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

if os.path.isfile(app_config['datastore']['filename']):
        f = open(app_config['datastore']['filename'])
        f_content = f.read()
        json_object = json.loads(f_content)
        f.close()
else:
    json_object = {'receiver_health': False,
                    'storage_health': False,
                    'processing_health': False,
                    'audit_health': False,
                    'last_updated': "2023-10-12T11:06:15.894272"}
    file_path = app_config['datastore']['filename']
    with open(file_path, 'w') as data_json:
        json.dump(json_object, data_json, indent=4)

def get_health():
    if os.path.isfile(app_config['datastore']['filename']):
        f = open(app_config['datastore']['filename'])
        f_content = f.read()
        json_object = json.loads(f_content)
        f.close()
        return json_object, 201
    else:
        logger.error("File does not exist")
        return "stats do not exist", 404

def health_check():
    if os.path.isfile(app_config['datastore']['filename']):
        f = open(app_config['datastore']['filename'])
        f_content = f.read()
        json_object = json.loads(f_content)
        f.close()
    else:
        json_object = {'receiver_health': False,
                        'storage_health': False,
                        'processing_health': False,
                        'audit_health': False,
                        'last_updated': "2023-10-12T11:06:15.894272"}
    file_path = app_config['datastore']['filename']
    with open(file_path, 'w') as data_json:
        json.dump(json_object, data_json, indent=4)


    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%dT%H:%M:%S.%f')

    logger.info("Health check beginning")
    check_receiver = requests.get(f"{app_config['urls']['receiver']}/health")
    check_storage = requests.get(f"{app_config['urls']['storage']}/health")
    check_processing = requests.get(f"{app_config['urls']['processing']}/health")
    check_audit = requests.get(f"{app_config['urls']['audit']}/health")

    logger.info(f"Health check over")
    if check_receiver.status_code == 200:
        logger.info(f"Receiver is health: {check_receiver.status_code}")
        health_receiver = "Running"
    else:
        health_receiver = "Down"
    if check_storage.status_code == 200:
        logger.info(f"Receiver is health: {check_storage.status_code}")
        health_storage = "Running"
    else:
        health_storage = "Down"
    if check_processing.status_code == 200:
        logger.info(f"Receiver is health: {check_processing.status_code}")
        health_processing = "Running"
    else:
        health_processing = "Down"
    if check_audit.status_code == 200:
        logger.info(f"Receiver is health: {check_audit.status_code}")
        health_audit = "Running"
    else:
        health_audit = "False"
    health_dict =  {'receiver_health': health_receiver,
                        'storage_health': health_storage,
                        'processing_health': health_processing,
                        'audit_health': health_audit,
                        'last_updated': timestamp}
    f = open(app_config['datastore']['filename'], 'w')
    f.write(json.dumps(health_dict))
    f.close()
    logger.debug(f"The current data is {health_dict}")
    logger.info(f"Processing period ended")
def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(health_check,
                  'interval',
                  seconds=app_config['scheduler']['period_sec'])
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yaml",
            strict_validation = True,
            validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8120, debug = True, use_reloader=False)