FROM python:3.7-alpine

ARG UID=1000
ARG GID=1000

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

RUN addgroup -g $GID -S iomirea && \
    adduser -u $UID -S updater -G iomirea
RUN chown -R updater:iomirea /code
RUN chown -R updater:iomirea /config

# docker socket access issue
#USER updater

VOLUME /config
VOLUME /api

EXPOSE 8081

CMD ["python", "updater/app.py"]
