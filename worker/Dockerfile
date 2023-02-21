FROM xserrat/facebook-demucs:latest

RUN pip3 install redis
RUN pip3 install minio
RUN pip3 install requests jsonpickle

WORKDIR /srv
COPY short-hop.mp3 /srv
COPY worker.py /srv
COPY test.py /srv

ENTRYPOINT [ "python3", "worker.py" ]



