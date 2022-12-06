# Info

With this bot you can create application webhooks that can be used to send messages with buttons.
Keep in mind that the webhooks get deleted, if you remove the bot from your server. (But it doesn't have to be online.)

You can use the bot to create webhooks for your server, or for other servers. (If you have the permission to create webhooks in that server.)


### Setup

#### Classic
      1. Make sure you have Python 3.9 installed. I used 3.9.7 to develop this bot. (https://www.python.org/downloads/)
      2. Clone this repo, or download the zip file.
      3. Open a terminal inside "WebhookCreator" in the folder where you cloned the repo, or extracted the zip file.
      4. Run `pip install -r requirements.txt` to install the dependencies.
      5. Open the file ".env" and enter your bot token and your owner id.
      6. Run `python main.py` or `python3 main.py` to start the bot.

#### Docker
##### Create the image yourself
      1. Make sure you have Docker installed. (https://docs.docker.com/get-docker/)
      2. Clone this repo, or download the zip file.
      3. Open a terminal inside "WebhookCreator" in the folder where you cloned the repo, or extracted the zip file.
      4. Run `docker build -t webhookcreator .` to build the docker image.
      5. Run `docker run -d -e TOKEN=BOT_TOKEN -e owner_id=DISCORD_ID_OF_OWNER --name webhookcreator webhookcreator` to start the bot.
##### Use my pre-build image
      1. Make sure you have Docker installed. (https://docs.docker.com/get-docker/)
      2. Open a terminal.
      3. Run `docker run -d -e TOKEN=BOT_TOKEN -e owner_id=DISCORD_ID_OF_OWNER --name webhookcreator serpensin/doscord_webhook_creator` to start the bot.

You can also [invite](https://discord.com/api/oauth2/authorize?client_id=974023271303499796&permissions=536870912&scope=bot%20applications.commands) the bot I host to your server.