from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import requests, json, math
from PIL import Image
import io
import time
import re
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy   dog'
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/bla": {"origins": "https://localhost:7777"}})


@app.route("/generateMeme", methods=["GET"])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def generateMeme():
    meme_url = "http://127.0.0.1:5000/getImage"
    quotes_url = 'http://api.kanye.rest/?format=text'
    image_url = 'https://api.unsplash.com/photos/random/'

    log_file = open("log.txt", "a+")
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
    start_time = time.time()
    log_file.write("Local Timestamp: " + timestampStr + "\n")
    log_file.write("Request Method: <[GET]>\n")
    log_file.write("Request URL: https://127.0.0.1:7777/generateMeme\n")
    log_file.write("Request Body: " + str(request.form) + "\n")
    log_file.write("Request Headers: " + re.sub(r'\n*', '', str(request.headers)) + "\n")
    log_file.write("API Calls:\n")

    quote = requests.request("GET", quotes_url).text

    log_file.write("\tRequest Method: <[GET]>\n")
    log_file.write("\tRequest URL: " + quotes_url + "\n")
    log_file.write("\tRequest Body: ''\n")
    log_file.write("\tRequest Headers: ''\n")
    log_file.write("\tResponse Headers: ''\n")
    log_file.write("\tResponse Body Text: " + quote + "\n\n")
    # quote = quote.replace(" ", "_")

    querystring = {'client_id': open('image_key.txt').read(),"query":"Nature"}

    image_json = json.loads(requests.request("GET", image_url, params=querystring).text)
    image = image_json['urls']['regular']

    log_file.write("\tRequest Method: <[GET]>\n")
    log_file.write("\tRequest URL: " + image_url + "\n")
    log_file.write("\tRequest Body: ''\n")
    log_file.write("\tRequest Headers: " + str(querystring) + "\n")
    log_file.write("\tResponse Headers: ''\n")
    log_file.write("\tResponse Body Text: " + str(image_json) + "\n\n")

    querystring = {'text':quote, 'image':image}

    meme = requests.request("GET", meme_url, params=querystring)

    final_image = meme.text
    response = jsonify({'img': final_image})
    response.headers.add('Access-Control-Allow-Origin', '*')
    end_time = time.time()
    log_file.write("\tRequest Method: <[GET]>\n")
    log_file.write("\tRequest URL: " + meme_url + "\n")
    log_file.write("\tRequest Body: " + str(querystring) + "\n")
    log_file.write("\tRequest Headers: ''\n")
    log_file.write("\tResponse Headers: ''\n")
    log_file.write("\tResponse Body Text: " + meme.text + "\n\n")

    process_time = end_time - start_time

    log_file.write("Response Headers: " + re.sub(r'\n*', '', str(response.headers)) + "\n")
    log_file.write("Response Body: " + str(response) + "\n")
    log_file.write("Response Time: " + str(process_time) + "\n\n____________________________________________\n\n")

    return response

@app.route("/metrics", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content- Type','Authorization'])
def getMetrics():
    log = open("log.txt").read()
    return log

app.run(port="7777")