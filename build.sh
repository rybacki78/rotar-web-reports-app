#!/bin/bash
if [ -n "$1" ]; then
    TAG="$1"
else
    BRANCH=$(git rev-parse --abbrev-ref HEAD | sed 's/[^a-zA-Z0-9]/-/g')
    COMMIT=$(git rev-parse --short HEAD)
    TAG="${BRANCH}-${COMMIT}"
fi

IMAGE_NAME="web-reports-app"
docker build -t $IMAGE_NAME:$TAG .
echo "Built image with tag: $IMAGE_NAME:$TAG"