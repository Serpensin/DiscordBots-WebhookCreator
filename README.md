# WebhookCreator DiscordBot [![Discord Bot Invite](https://img.shields.io/badge/Invite-blue)](https://discord.com/oauth2/authorize?client_id=1251220473790861454)[![Discord Bots](https://top.gg/api/widget/servers/1251220473790861454.svg)](https://top.gg/bot/1251220473790861454)

With this bot you can create application webhooks that can be used to send messages with buttons.
Keep in mind that the webhooks get deleted, if you remove the bot from your server. (But it doesn't have to be online.)

You can use the bot to create webhooks for your server, or for other servers. (If you have the permission to create webhooks in that server.)


### Setup

#### Classic
      1. Make sure you have Python 3.9 installed. I used 3.9.7 to develop this bot. (https://www.python.org/downloads/)
      2. Clone this repo, or download the zip file.
      3. Open a terminal inside "WebhookCreator" in the folder where you cloned the repo, or extracted the zip file.
      4. Run `pip install -r requirements.txt` to install the dependencies.
      5. Open the file ".env.template" and enter your bot token and your owner id. After that, rename it to ".env".
      6. Run `python main.py` or `python3 main.py` to start the bot.

#### Docker
##### Create the image yourself
      1. Make sure you have Docker installed. (https://docs.docker.com/get-docker/)
      2. Clone this repo, or download the zip file.
      3. Open a terminal inside "WebhookCreator" in the folder where you cloned the repo, or extracted the zip file.
      4. Run `docker build -t webhookcreator .` to build the docker image.
      5. Run `docker run -d -e TOKEN=BOT_TOKEN -e owner_id=DISCORD_ID_OF_OWNER --name webhookcreator serpensin/discord_webhook_creator` to start the bot.
##### Use my pre-build image
      1. Make sure you have Docker installed. (https://docs.docker.com/get-docker/)
      2. Open a terminal.
      3. Run `docker run -d -e TOKEN=BOT_TOKEN -e owner_id=DISCORD_ID_OF_OWNER --name webhookcreator serpensin/discord_webhook_creator` to start the bot.

#### Run the bot
You only need to expose the port `-p 5000:5000`, if you want to use an external tool, to test, if the bot is running.
In this case, you need to call the `/health` endpoint.
```bash
docker run -d \
-e SUPPORT_SERVER=ID_OF_SUPPORTSERVER \
-e TOKEN=BOT_TOKEN \
-e OWNER_ID=DISCORD_ID_OF_OWNER \
--name Hercules \
--restart any \
--health-cmd="curl -f http://localhost:5000/health || exit 1" \
--health-interval=30s \
--health-timeout=10s \
--health-retries=3 \
--health-start-period=40s \
-p 5000:5000 \
-v hercules_log:/app/Basis/Logs \
ghcr.io/serpensin/discordbots-webhookcreator:latest
```