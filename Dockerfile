FROM python:3-alpine
MAINTAINER Gabriell Constantin Vig "gabriell.vig@sesam.io"
ARG BuildNumber=unknown
LABEL BuildNumber $BuildNumber
ARG Commit=unknown
LABEL Commit $Commit

COPY ./service /service

WORKDIR /service
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN rm -rf /usr/local/lib/python3.8/site-packages/werkzeug/debug/shared/jquery.js
RUN rm -rf /usr/local/lib/python3.8/site-packages/cherrypy/test/test.pem

EXPOSE 5000/tcp
CMD ["python3", "-u", "transform-service.py"]
