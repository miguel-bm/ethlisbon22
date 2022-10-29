#! /usr/bin/env sh

export IMAGE_NAME="ethlisbon"

pipenv requirements > requirements.txt 
docker build -t $IMAGE_NAME .
