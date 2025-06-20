@echo off
setlocal

REM Set image name (unique per build)
set IMAGE_NAME=webhookcreator_debug

REM Build the Docker image
docker build -t %IMAGE_NAME% .

REM Run the Docker container in attached mode
docker run --rm --env-file .env -it %IMAGE_NAME%

REM After container exits, remove the image
docker rmi %IMAGE_NAME%

endlocal
