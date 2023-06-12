#Import
import discord
import os
import platform
import sentry_sdk
import sys
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta


#Sentry
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
)


bot_version = "1.1.0"
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
        global owner, start_time
        owner = await bot.fetch_user(ownerID)
        start_time = datetime.now()
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
#Bot Information
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    member_count = sum(guild.member_count for guild in bot.guilds)

    embed = discord.Embed(
        title=f"Informationen about {bot.user.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

    embed.add_field(name="Created at", value=bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), inline=True)
    embed.add_field(name="Bot-Version", value=bot_version, inline=True)
    embed.add_field(name="Uptime", value=str(timedelta(seconds=int((datetime.now() - start_time).total_seconds()))), inline=True)

    embed.add_field(name="Bot-Owner", value=f"<@!{ownerID}>", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="Server", value=f"{len(bot.guilds)}", inline=True)
    embed.add_field(name="Member count", value=str(member_count), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="Shards", value=f"{bot.shard_count}", inline=True)
    embed.add_field(name="Shard ID", value=f"{interaction.guild.shard_id if interaction.guild else 'N/A'}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="Python-Version", value=f"{platform.python_version()}", inline=True)
    embed.add_field(name="discord.py-Version", value=f"{discord.__version__}", inline=True)
    embed.add_field(name="Sentry-Version", value=f"{sentry_sdk.consts.VERSION}", inline=True)

    embed.add_field(name="Repo", value=f"[GitLab](https://gitlab.bloodygang.com/Serpensin/Discord-Webhook-Creator)", inline=True)
    embed.add_field(name="Invite", value=f"[Invite me](https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=536870912&scope=bot%20applications.commands)", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)  

    await interaction.response.send_message(embed=embed)
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
    if not TOKEN:
        sys.exit('Missing token. Please check your .env file.')
    else:
        try:
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            sys.exit('Invalid token. Please check your .env file.')

