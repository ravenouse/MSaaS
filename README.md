# MSaaS (Music-Separation-as-a-service) Project Readme

![separation](images/music_separation.png)

MSaaS is a class project for creating a Kubernetes cluster that provides a REST API for automatic music separation service and prepares the different tracks for retrieval. This project is focused on deploying containers providing three services: rest, worker, and redis.

The REST frontend will accept API requests for analysis and handle queries concerning MP3's. The REST worker will queue tasks to workers using redis queues. The worker node will receive work requests to analyze MP3's and cache results in a Min.io.

This project relies on the [Facebook demucs](https://github.com/facebookresearch/demucs) as its core.

## Quick Start

1. Start the Kubernetes cluster.

```shell
minikube start
minikube tunnel 
```

2. Deploy all resources to the Kubernetes cluster

```shell
./deploy-all.sh
```

3. Send sample requests to the REST API

```shell
python sample-requests.py
```
