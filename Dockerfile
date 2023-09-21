# import python image version 3.8
FROM python:3.8

# add maintainer
LABEL Eko Saputro

# set working directory
WORKDIR /app

# install Cron
RUN apt-get update
RUN apt-get -y install cron

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies from requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U numpy

# copy the content of the local directory to the working directory
COPY .env .
COPY .env.example .
COPY crontab /etc/cron.d/crontab
COPY gamepass_scrapper.py .
COPY google-sheet-credentials.json .
COPY run_scrapper.sh .
COPY xbox_deals_scrapper.py .

# give execution rights to the script
RUN chmod 0644 /etc/cron.d/crontab

# add the cron job
RUN /usr/bin/crontab /etc/cron.d/crontab

# run the command on container startup
CMD ["cron", "-f"]
