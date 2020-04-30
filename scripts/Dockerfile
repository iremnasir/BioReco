FROM python:3.6-slim
WORKDIR /app
ADD . /app
RUN pip install tweepy
RUN pip install pymongo

#^^^^^^^Happens at docker build
#--------------
#happens at 'docker run'

CMD python tweet_collector.py
