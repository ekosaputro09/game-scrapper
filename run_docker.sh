docker kill game-scrapper && docker rm game-scrapper
docker build -t game-scrapper . && docker run --name game-scrapper -it -d --restart unless-stopped game-scrapper