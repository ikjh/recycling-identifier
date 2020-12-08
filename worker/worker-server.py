import pickle
import platform
import io
import os
import sys
import pika
import hashlib
from google.cloud import storage
from google.cloud import vision
import json
import psycopg2


hostname = platform.node()

##
## Configure test vs. production
##
postgresHost = os.getenv("POSTGRES_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and postgres({})".format(rabbitMQHost, postgresHost))

rabbitMQ = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
rabbitMQChannel = rabbitMQ.channel()

rabbitMQChannel.exchange_declare(exchange='toWorker', exchange_type='direct')
result = rabbitMQChannel.queue_declare('workerimg')

print(' [*] made ' + result.method.queue + ' queue')
print(' [*] Waiting for logs. To exit press CTRL+C')

rabbitMQChannel.queue_bind(exchange='toWorker', queue=result.method.queue, routing_key='workerimg')

# create table
sqlTable = 'CREATE TABLE IF NOT EXISTS images (hash_id VARCHAR(255) PRIMARY KEY, object VARCHAR(255), is_recyclable VARCHAR(255) NOT NULL);'
conn = None
try:
    conn = psycopg2.connect(host=postgresHost, database="postgresdb", user="postgresadmin", password="admin123")
    cur = conn.cursor()
    cur.execute(sqlTable)
    cur.close()
    conn.commit()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    if conn is not None:
        conn.close()


def callback(ch, method, properties, body):

    print(" [x] %r:%r" % (method.routing_key, json.loads(body)), file=sys.stderr)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQHost))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='topic')
    initial_message = hostname + '.worker.info recieved hash'
    channel.basic_publish(exchange='logs', routing_key='info', body=initial_message)
    
    hashImg = json.loads(body)['hash'] 
    name = json.loads(body)['name']

    # check if hash already exists in table
    try:
        postgresConn = psycopg2.connect(host=postgresHost, database="postgresdb", user="postgresadmin", password="admin123")
        cur = postgresConn.cursor()
        cur.execute("SELECT is_recyclable FROM images WHERE hash_id=%s", (hashImg,))
        row = cur.fetchone()
        if row is None:
            # retrieve image from google storage
            storage_client = storage.Client()
            blob = storage_client.bucket('recyclables').get_blob(name.split('/')[-1])
            tmpfile = 'tmp-'+blob.name
            blob.download_to_filename(tmpfile)

            sqlInsert = """INSERT INTO images (hash_id, object, is_recyclable) VALUES (%s,%s,%s)"""

            # find labels of image using vision api
            client = vision.ImageAnnotatorClient()
            file_name = os.path.abspath(tmpfile)
            with io.open(file_name, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            # Performs label detection on the image file
            response = client.label_detection(image=image)
            labels = response.label_annotations
            object_name = labels[0].description
            is_recyclable = 'no'

            for label in labels:
                if 'Aluminum' in label.description or 'Tin' in label.description:
                    object_name = label.description
                    is_recyclable = 'yes'

            # insert into table
            record_to_insert = (hashImg, object_name, is_recyclable)
            cur.execute(sqlInsert, record_to_insert)

            db_message = hostname + '.worker.info added hash and info to postgres'
            channel.basic_publish(exchange='logs', routing_key='info', body=db_message)
            
            postgresConn.commit()

            os.remove(tmpfile)
        else:
            log_message = hostname + '.worker.info already scanned hash'
            channel.basic_publish(exchange='logs', routing_key='info', body=log_message)
                 
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        err_message = hostname + 'worker.info ' + error
        channel.basic_publish(exchange='logs', routing_key='info', body=err_message)
    finally:
        if postgresConn is not None:
            postgresConn.close()

    connection.close()


rabbitMQChannel.basic_consume(queue='workerimg', on_message_callback=callback, auto_ack=True)

rabbitMQChannel.start_consuming()