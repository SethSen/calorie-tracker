FROM ubuntu:18.04

LABEL maintainer="ssen1@my.bcit.ca"

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip

# Assuming this Dockerfile is in the same directory as the service's requirements.txt
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

# Copy the entire service directory
COPY . /app

# Adjust this for each service
ENTRYPOINT ["python3"]
CMD ["app.py"]
