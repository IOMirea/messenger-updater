FROM python:3.7-alpine

# leader updates postgres database
# TODO: choose leader randomly?
ENV LEADER=0

WORKDIR /code

RUN apk add --no-cache \
	gcc \
	musl-dev \
	git

# avoid cache invalidation after copying entire directory
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apk del \
	gcc \
	musl-dev

COPY . .

RUN mkdir /config
RUN mkdir /api

# volumes are owned by host user no matter what
#RUN adduser -S updater
#RUN chown -R updater /config
#RUN chown -R updater /code
#RUN chown -R updater /api
#USER updater

VOLUME /config
VOLUME /api

EXPOSE 8081

CMD ["python", "updater/app.py"]
