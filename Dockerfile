FROM python:3.7-alpine

ARG UID=1500
ARG GID=1500

ARG PORT=8081

# workaround for CMD not being able to parse variable at build time
ENV PORT ${PORT}

# leader updates postgres database
# TODO: choose leader randomly?
ENV LEADER 0

# enables propper stdout flushing
ENV PYTHONUNBUFFERED 1

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

USER updater

VOLUME /config
VOLUME /api

EXPOSE ${PORT}

CMD python updater/app.py --port=$PORT --host=0.0.0.0
