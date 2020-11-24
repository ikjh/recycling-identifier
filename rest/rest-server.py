from flask import Flask, request, Response
import jsonpickle, pickle
import platform
import io, os, sys
import pika
import psycopg2
import hashlib, requests
import json
from google.cloud import storage

##
## Configure test vs. production
##

rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"
postgresHost = os.getenv("POSTGRES_HOST") or "localhost"

print("Connecting to rabbitmq({}) and postgres({})".format(rabbitMQHost,postgresHost))

postgresConn = psycopg2.connect(
    host=postgresHost,
    database="postgresdb",
    user="postgresadmin",
    password="admin123")

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return '<h1> Recyclable Identifier Server</h1><p> Use a valid endpoint </p>'

@app.route('/scan/url', methods=['POST'])
def scanUrl():
    wconnection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    lconnection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    wchannel = wconnection.channel()
    lchannel = lconnection.channel()
    wchannel.exchange_declare(exchange='toWorker', exchange_type='direct')
    wchannel.queue_declare(queue='workerimg')
    lchannel.exchange_declare(exchange='logs', exchange_type='topic')
    try:
        url = jsonpickle.decode(request.data)['url']
        img_response = requests.get(url)
        ioBuffer = img_response.content
        h = hashlib.blake2b()
        h.update(ioBuffer)
        hash = h.hexdigest()
        response = {'hash': hash}
        message = {'hash': hash, 'name': url}

        storage_client = storage.Client()
        bucket = storage_client.bucket('trash-imgs')
        blob = bucket.blob(url.split('/')[-1])
        if(img_response.headers.get('content-type').startswith("image")):
            blob.upload_from_string(img_response.content, content_type=img_response.headers.get('content-type'))
            log_message2 = '0.0.0.0.rest.info POST /scan/image/' + url + ' uploaded to trash-imgs bucket'
            lchannel.basic_publish(exchange='logs', routing_key='info', body=log_message2)
        
        wchannel.basic_publish(exchange='toWorker', routing_key='workerimg', body=json.dumps(message))
        
    except:
        response = {'hash': ''}
        message = {'hash': '', 'name': url}
        wchannel.basic_publish(exchange='toWorker', routing_key='workerimg', body=json.dumps(message))

        debug_message = sys.exc_info()[0]
        lchannel.basic_publish(exchange='logs', routing_key='err', body=debug_message)
    
    log_message = '0.0.0.0.rest.info POST /scan/url ' +  message['hash'] + ' status=200'
    lchannel.basic_publish(exchange='logs', routing_key='info', body=log_message)

    wconnection.close()
    lconnection.close()

    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")

@app.route('/check/<string:hash>', methods=['GET'])
def getIsRecyclable(hash):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    
    response = 'no'
    # TO DO: query database
    hashes = None
    if hashes is None:
        log_message = '0.0.0.0.rest.info GET /check/' + hash + ' has not been scanned.'
    elif hashes == []:
        log_message = '0.0.0.0.rest.info GET /check/' + hash + ' is not recyclable'
    else:
        log_message = '0.0.0.0.rest.info GET /check/' + hash + ' is recyclable'
        response = 'yes'

    channel.basic_publish(exchange='logs', routing_key='info', body=log_message)

    connection.close()
    return {'isRecyclable' : response}

# start flask app
app.run(host="0.0.0.0")