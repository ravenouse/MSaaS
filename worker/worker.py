import os
import sys
import redis
from minio import Minio
import demucs

import glob

import base64
import json

# redis client
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379

# minio client
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

bucketname='my-bucketname'

def main(debug = True):
    # Connect to redis
    redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)
    print(f"Connected to redis at {redisHost}:{redisPort}")

    # Connect to minio
    minioClient =  Minio(minioHost,
                        secure=False,
                        access_key=minioUser,
                        secret_key=minioPasswd)
    print(f"Connected to minio at {minioHost}")

    # Create a bucket if it doesn't exist
    if not minioClient.bucket_exists(bucketname):
        print(f"Create bucket {bucketname}")
        minioClient.make_bucket(bucketname)

    while True:
        try:
            # listen to the redis
            work = redisClient.blpop("working", timeout=0)
            print(work[1].decode('utf-8')) # the value will be hash format of the name of the mp3 file

            # get the mp3 file from minio
            mp3_filename = work[1].decode('utf-8') + '.mp3'
            minioClient.fget_object(bucketname, mp3_filename, f"./{mp3_filename}")
            if debug == True:
                print(f"successfully get the file {mp3_filename} from minio")

            # separate the mp3 file
            os.system(f"python3 -m demucs.separate --out './output/' './{mp3_filename}' --mp3")
            if debug == True:
                print(f"successfully separate the mp3 file {mp3_filename}")

            # detect if the output folder is empty
            mp3_filename = mp3_filename.split('.')[0]
            while True:
                if len(os.listdir(f"./output/mdx_extra_q/{mp3_filename}")) == 4:
                    break
            dict_msg = {}    
            for result_mp3 in glob.glob(f"./output/mdx_extra_q/{mp3_filename}/*.mp3"):
                # upload the separated mp3 file to minio
                minio_path = mp3_filename + "/" + result_mp3.split('/')[-1]
                minioClient.fput_object(bucketname, minio_path, result_mp3)
                if debug == True:
                    print(f"successfully upload the separated mp3 file {result_mp3} to minio")
                    print(f"the path of the separated mp3 file is {minio_path}")

                # sending message to the server
                dict_msg[minio_path.split('/')[-1]] = minio_path
            dict_msg = json.dumps(dict_msg)
            redisClient.lpush('track', dict_msg)
            if debug == True:
                print(f"successfully send the message to the server")
                print(f"the message is {dict_msg}")
                
                # # convert the separated mp3 file to base64
                # with open(result_mp3, "rb") as f:
                #     base64_mp3 = base64.b64encode(f.read())
                #     if debug == True:
                #         print(f"successfully convert the separated mp3 file {result_mp3} to base64")

                # # send the separated mp3 file to the rest server
                # redisClient.lpush("track", base64_mp3)
                # if debug == True:
                #     print(f"successfully sent the message back to server")

        except Exception as e:
            print(e)
        sys.stdout.flush()
        sys.stderr.flush()
    
if __name__ == "__main__":
    main()