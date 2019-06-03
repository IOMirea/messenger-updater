FROM python:3.7-alpine

WORKDIR /code

RUN apk add --no-cache \
	build-base \
	git

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
RUN rm /requirements.txt

EXPOSE 8081
CMD ["python3.7", "updater/app.py"]
