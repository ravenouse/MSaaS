import os
import sys
import redis
from minio import Minio
from flask import Flask, request, Response
from flask import send_file
import json
import jsonpickle
import base64
import io
import hashlib
import zipfile


# Redis
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

# minio
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"
bucketname='my-bucketname'
client = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

# Initialize the Flask application
app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return '<h1> Music Separation Server</h1><p> Use a valid endpoint </p>'

@app.route('/apiv1/separate', methods=['POST'])
def separate():
    r = request
    json = jsonpickle.decode(r.data)
    mp3 = json['mp3'].encode('utf-8')
    mp3_filename = json['callback']['data']['mp3'].split('/')[-1]

    # try to write the the mp3 file
    try:
        print("wiritng file locally")
        with open(f"./{mp3_filename}", "wb") as f:
            f.write(base64.b64decode(mp3))
            print("successfully wrote file locally")
    except Exception as e:
        print(e)

    # redis
    try:
        print("writing file/hash to redis")
        mp3_hash = hashlib.md5(mp3_filename.encode('utf-8')).hexdigest()
        print(f"hash is {mp3_hash}")
        redisClient.lpush('logging', mp3_filename)
        redisClient.lpush('working', mp3_hash)
        redisClient.lpush('queue', mp3_hash)
        redisClient.lpush('remove', mp3_hash)
        print("successfully sent redis messages to logger and worker")

    except Exception as e:
        print(e)
    
    # minio
    # detect if the bucket exists
    if not client.bucket_exists(bucketname):
        print(f"Create bucket {bucketname}")
        client.make_bucket(bucketname)
    try:
        print("writing file to minio")
        client.fput_object(bucketname, mp3_hash + '.mp3', f"./{mp3_filename}")
        print("successfully wrote file to minio")
    except Exception as e:
        print(e)

    response = {'hash': mp3_hash, 'reson': 'Song enqueued for separation'}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")

@app.route('/apiv1/queue', methods=['GET'])
def queue():
    mp3_hash = redisClient.lpop('queue').decode('utf-8')
    response = {'queue': mp3_hash}
    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype="application/json")

@app.route('/apiv1/track//track', methods=['GET'])
def track():
    while True:
        work = redisClient.blpop("track", timeout=0)
        dict_msg = work[1].decode('utf-8')
        dict_msg = json.loads(dict_msg)
        print(dict_msg)
        with zipfile.ZipFile('output.zip', 'w') as zipObj:
            for mp3_filename, path in dict_msg.items():
                print(f"mp3_filename: {mp3_filename}")
                print(f"path: {path}")
                if path:
                    client.fget_object(bucketname, path, f'./{mp3_filename}')
                    zipObj.write(f'./{mp3_filename}')
        return send_file('output.zip', as_attachment=True)
        
@app.route('/apiv1/remove//track', methods=['GET'])
def remove():
    os.remove('output.zip')
    
    return "the result mp3 file removed"
    
app.run(host="0.0.0.0", port=5005)