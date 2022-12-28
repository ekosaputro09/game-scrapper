# import python image version 3.8
FROM python:3.8

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
COPY google-sheet-credentials.json .
COPY gamepass_scrapper.py .
COPY run_scrapper.sh .

# give execution rights to the script
RUN chmod 0644 /app/run_scrapper.sh

# add the cron job
RUN crontab -l | { cat; echo "0 1 * * * bash /app/run_scrapper.sh"; } | crontab -

# run the command on container startup
CMD cron
