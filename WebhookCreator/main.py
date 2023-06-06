#Import
import time
import discord
import os
import sentry_sdk
from dotenv import load_dotenv


#Sentry
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
)



TOKEN = os.getenv('TOKEN')
ownerID = os.getenv('OWNER_ID')



class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(owner_id = ownerID,
                              intents = intents,
                              status = discord.Status.invisible
                        )
        self.synced = False
    async def on_ready(self):
        if not self.synced:
            await tree.sync()
            self.synced = True
            await bot.change_presence(activity = discord.Game(name='with Webhooks'), status = discord.Status.online)
        global owner
        owner = await bot.fetch_user(ownerID)
        print('READY')
bot = aclient()
tree = discord.app_commands.CommandTree(bot)


##Events
#Error
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    await interaction.response.send_message(error, ephemeral = True)

 
##Owner Commands----------------------------------------
#Shutdown
@tree.command(name = 'shutdown', description = 'Safely shut down the bot.')
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        await interaction.response.send_message('Engine powering down...', ephemeral = True)
        await bot.close()
    else:
        await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)
##Bot Commands----------------------------------------
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! `{int(ping)}ms`')
##Main Commands----------------------------------------
#Create Webhook
@tree.command(name = 'create_webhook', description = 'Create a webhook.')
@discord.app_commands.describe(name='Name of the webhook.')
async def self(interaction: discord.Interaction, name: str):
    if interaction.channel.permissions_for(interaction.user).manage_webhooks:
        webhook = await interaction.channel.create_webhook(name=name, reason=f'Created by {interaction.user.name}#{interaction.user.discriminator} ({interaction.user.id})')
        await interaction.response.send_message(webhook.url, ephemeral=True)
    else:
        await interaction.response.send_message('You need the permission "Manage Webhooks" for this channel to use this command!', ephemeral=True)


if __name__ == '__main__':
   bot.run(TOKEN)
