for /f "usebackq delims=" %%d in (`wmic os get LocalDateTime ^| findstr ^^[0-9]`) do set datetime=%%d
set BUILD_DATE=%datetime:~4,2%-%datetime:~6,2%-%datetime:~0,4%

docker buildx build --build-arg BUILD_DATE=$BUILD_DATE$ --compress --platform linux/386,linux/amd64,linux/arm/v6,linux/arm/v7,linux/arm64/v8 -t serpensin/discord_webhook_creator:latest --push ./WebhookCreator