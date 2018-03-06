'''This script manages the flask server'''

from flask import abort, jsonify, Flask, send_file, request, url_for, send_from_directory
from logging.handlers import RotatingFileHandler
from pprint import pprint

import logging, json, os, subprocess
from database import Database

app = Flask(__name__, static_folder='static', static_url_path='')

database = Database()

'''Logging Configuration'''

formatter = logging.Formatter(
    '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
)
logHandler = RotatingFileHandler('info.log', maxBytes=1000, backupCount=1)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logHandler)

''' Routes '''

@app.route('/')
def index():
    """
    Returns the list of endpoints.
    """
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, rule))
        output.append(line)

    output = sorted(output)
    return jsonify(output)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'static/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/ratio', methods=['GET'])
def highest_ratio():
    screen_name = request.args.get('seed')
    if screen_name:
        seed = database.find_seed_by_screen_name(screen_name)
        if seed:
            result = database.highest_ratio_by_seed(seed['id'])
            return jsonify(result)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/activeusers', methods=['GET'])
def active_users():
    screen_name = request.args.get('seed')
    if screen_name:
        seed = database.find_seed_by_screen_name(screen_name)
        if seed:
            active = database.count_active_users_by_seed(seed['id'])
            total = database.count_users_by_seed(seed['id'])

            result = [
                {
                    "name" : "Activos",
                    "count" : active
                },
                {
                    "name" : "Inactivos",
                    "count" : total - active
                }
            ]
            return jsonify(result)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/gender', methods=['GET'])
def gender():
    screen_name = request.args.get('seed')
    if screen_name:
        seed = database.find_seed_by_screen_name(screen_name)
        if seed:
            gender = database.gender_proportion(seed['id'])
            result = [
                {
                    "name" : "Male",
                    "value" : gender['male']*100/gender['total'],
                    "color" : "#FEC514",
                    "face" : "https://www.amcharts.com/lib/images/faces/C02.png"
                },
                {
                    "name" : "Female",
                    "value" : gender['female']*100/gender['total'],
                    "color" : "#DB4C3C",
                    "face" : "https://www.amcharts.com/lib/images/faces/D02.png"
                }
            ]
            return jsonify(result)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/age', methods=['GET'])
def age():
    screen_name = request.args.get('seed')
    if screen_name:
        seed = database.find_seed_by_screen_name(screen_name)
        if seed:
            age = database.age_proportion(seed['id'])
            result = []
            for age_group in age['count']:
                entry = {
                    "count" : age_group['count'],
                }
                if "max" in age_group:
                    entry['age'] = "{0} - {1}".format(age_group['min'], age_group['max'])
                else:
                    entry['age'] = "{0}+".format(age_group['min'])
                result.append(entry)
            return jsonify(result)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/hours', methods=['GET'])
def hours():
    screen_name = request.args.get('seed')
    if screen_name:
        seed = database.find_seed_by_screen_name(screen_name)
        if seed:
            colours = [
                "#CD0D74",
                "#8A0CCF",
                "#2A0CD0",
                "#0D52D1",
                "#0D8ECF",
                "#04D215",
                "#B0DE09",
                "#F8FF01",
                "#FCD202",
                "#FEB802",
                "#FF8201",
                "#FF6600",
                "#FF0F00",
                "#FF6600",
                "#FF8201",
                "#FEB802",
                "#FCD202",
                "#F8FF01",
                "#B0DE09",
                "#04D215",
                "#0D8ECF",
                "#0D52D1",
                "#2A0CD0",
                "#8A0CCF"
            ]
            hours = seed['followers_hours']
            result = []
            for hour in sorted(hours.keys()):
                value = hours[hour]
                entry = {
                    "name" : hour,
                    "value" : value,
                    "colour" : colours.pop()
                }
                result.append(entry)
            return jsonify(result)
        else:
            abort(404)
    else:
        abort(404)

@app.route('/api/influencers', methods=['GET'])
def influencers():
    result = database.main_influencers()
    return jsonify(result)

@app.route('/api/map', methods=['GET'])
def map():
    with open('tweets_map.json') as file:
        json_data = json.load(file)

    return jsonify(json_data)

@app.route('/api/sentiment', methods=['GET'])
def sentiment():
    topic = request.args.get('topic')
    if topic:
        topic = database.find_topic(topic)
        if topic:
            total = topic['sentiment']['P'] + topic['sentiment']['N'] + topic['sentiment']['NEU']
            result = [{
                "name" : "Positive",
                "value" : topic['sentiment']['P']*100/total,
                "color" : "#42F450"
            },
            {
                "name" : "Negative",
                "value" : topic['sentiment']['N']*100/total,
                "color" : "#DB4C3C"
            },
            {
                "name" : "Neutral",
                "value" : topic['sentiment']['NEU']*100/total,
                "color" : "#A6A6A6"
            }]
            return jsonify(result)
        else:
            abort(404)
    else:
        aboirt(404)
    


''' Main routine '''

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=8000)
