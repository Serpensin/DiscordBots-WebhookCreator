#Import
print('Loading...')
import aiohttp
import asyncio
import discord
import json
import jsonschema
import os
import platform
import sentry_sdk
import sys
import time
import traceback
from aiohttp import web
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse



#Sentry
discord.VoiceClient.warn_nacl = False
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
)

app_folder_name = 'WH-Creator'
bot_name = 'WebhookCreator'
if not os.path.exists(app_folder_name):
    os.makedirs(app_folder_name)
activity_file = os.path.join(app_folder_name, 'activity.json')
bot_version = "1.6.0"
TOKEN = os.getenv('TOKEN')
ownerID = os.getenv('OWNER_ID')
support_id = os.getenv('SUPPORT_SERVER')
topgg_token = os.getenv('TOPGG_TOKEN')
heartbeat_url = os.getenv('HEARTBEAT_URL')

# print() will only print if run in debugger. pt() will always print.
pt = print
def print(msg):
    if sys.gettrace() is not None:
        pt(msg)

#Create activity.json if not exists
class JSONValidator:
    schema = {
        "type" : "object",
        "properties" : {
            "activity_type" : {
                "type" : "string",
                "enum" : ["Playing", "Streaming", "Listening", "Watching", "Competing"]
            },
            "activity_title" : {"type" : "string"},
            "activity_url" : {"type" : "string"},
            "status" : {
                "type" : "string",
                "enum" : ["online", "idle", "dnd", "invisible"]
            },
        },
    }

    default_content = {
        "activity_type": "Playing",
        "activity_title": "Made by Serpensin: https://gitlab.bloodygang.com/Serpensin",
        "activity_url": "",
        "status": "online"
    }

    def __init__(self, file_path):
        self.file_path = file_path

    def validate_and_fix_json(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                try:
                    data = json.load(file)
                    jsonschema.validate(instance=data, schema=self.schema)  # validate the data
                except jsonschema.exceptions.ValidationError as ve:
                    print(f'ValidationError: {ve}')
                    self.write_default_content()
                except json.decoder.JSONDecodeError as jde:
                    print(f'JSONDecodeError: {jde}')
                    self.write_default_content()
        else:
            self.write_default_content()

    def write_default_content(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.default_content, file, indent=4)
validator = JSONValidator(activity_file)
validator.validate_and_fix_json()


#Bot
class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(owner_id = ownerID,
                              intents = intents,
                              status = discord.Status.invisible,
                              auto_reconnect = True
                        )
        self.synced = False
        self.initialized = False


    class Presence():
        @staticmethod
        def get_activity() -> discord.Activity:
            with open(activity_file) as f:
                data = json.load(f)
                activity_type = data['activity_type']
                activity_title = data['activity_title']
                activity_url = data['activity_url']
            if activity_type == 'Playing':
                return discord.Game(name=activity_title)
            elif activity_type == 'Streaming':
                return discord.Streaming(name=activity_title, url=activity_url)
            elif activity_type == 'Listening':
                return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
            elif activity_type == 'Watching':
                return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
            elif activity_type == 'Competing':
                return discord.Activity(type=discord.ActivityType.competing, name=activity_title)

        @staticmethod
        def get_status() -> discord.Status:
            with open(activity_file) as f:
                data = json.load(f)
                status = data['status']
            if status == 'online':
                return discord.Status.online
            elif status == 'idle':
                return discord.Status.idle
            elif status == 'dnd':
                return discord.Status.dnd
            elif status == 'invisible':
                return discord.Status.invisible


    async def on_message(self, message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'help - Shows this message\n'
                                       'activity - Set the activity of the bot\n'
                                       'status - Set the status of the bot\n'
                                       'shutdown - Shutdown the bot\n'
                                       '```')

        if message.guild is None and message.author.id == int(ownerID):
            args = message.content.split(' ')
            print(args)
            command, *args = args
            if command == 'help':
                await __wrong_selection()
                return

            elif command == 'activity':
                await Owner.activity(message, args)
                return

            elif command == 'status':
                await Owner.status(message, args)
                return

            elif command == 'shutdown':
                await Owner.shutdown(message)
                return

            else:
                await __wrong_selection()


    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        options = interaction.data.get("options")
        option_values = ""
        if options:
            for option in options:
                option_values += f"{option['name']}: {option['value']}"
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{str(timedelta(seconds=int(error.retry_after)))}`', ephemeral=True)
            return
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(f'You are missing the following permissions: `{", ".join(error.missing_permissions)}`', ephemeral=True)
            return
        else:
            try:
                try:
                    await interaction.response.send_message(f"Error! Try again.", ephemeral=True)
                except:
                    try:
                        await interaction.followup.send(f"Error! Try again.", ephemeral=True)
                    except:
                        pass
            except discord.Forbidden:
                try:
                    await interaction.followup.send(f"{error}\n\n{option_values}", ephemeral=True)
                except discord.NotFound:
                    try:
                        await interaction.response.send_message(f"{error}\n\n{option_values}", ephemeral=True)
                    except discord.NotFound:
                        pass
                except Exception as e:
                    traceback.print_exception(type(error), error, error.__traceback__)
            finally:
                traceback.print_exception(type(error), error, error.__traceback__)


    async def on_ready(self):
        if self.initialized:
            await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
            return
        if not self.synced:
            pt('Syncing commands...')
            await tree.sync()
            print('Commands synced.')
            self.synced = True
        global owner, start_time, shutdown
        shutdown = False
        try:
            owner = await bot.fetch_user(ownerID)
            print('Owner found.')
        except:
            print('Owner not found.')

        #Start background tasks
        if topgg_token:
            bot.loop.create_task(Functions.topgg())
        if heartbeat_url:
            bot.loop.create_task(Functions.health_server())
        bot.loop.create_task(Functions.webhook_count_activity())

        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        pt(r'''
 __      __          __       __                      __      ____                          __
/\ \  __/\ \        /\ \     /\ \                    /\ \    /\  _`\                       /\ \__
\ \ \/\ \ \ \     __\ \ \____\ \ \___     ___     ___\ \ \/'\\ \ \/\_\  _ __    __     __  \ \ ,_\   ___   _ __
 \ \ \ \ \ \ \  /'__`\ \ '__`\\ \  _ `\  / __`\  / __`\ \ , < \ \ \/_/_/\`'__\/'__`\ /'__`\ \ \ \/  / __`\/\`'__\
  \ \ \_/ \_\ \/\  __/\ \ \L\ \\ \ \ \ \/\ \L\ \/\ \L\ \ \ \\`\\ \ \L\ \ \ \//\  __//\ \L\.\_\ \ \_/\ \L\ \ \ \/
   \ `\___x___/\ \____\\ \_,__/ \ \_\ \_\ \____/\ \____/\ \_\ \_\ \____/\ \_\\ \____\ \__/.\_\\ \__\ \____/\ \_\
    '\/__//__/  \/____/ \/___/   \/_/\/_/\/___/  \/___/  \/_/\/_/\/___/  \/_/ \/____/\/__/\/_/ \/__/\/___/  \/_/
        ''')
        start_time = datetime.now()
        pt('READY')
        self.initialized = True
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error


# Check if all required variables are set
support_available = bool(support_id)



#Functions
class Functions():
    async def health_server():
        async def __health_check(request):
            return web.Response(text="Healthy")

        app = web.Application()
        app.router.add_get('/health', __health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        try:
            await site.start()
        except OSError as e:
            pt(f'Error while starting health server: {e}')


    async def create_support_invite(interaction):
        try:
            guild = bot.get_guild(int(support_id))
        except ValueError:
            return "Could not find support guild."
        if guild is None:
            return "Could not find support guild."
        if not guild.text_channels:
            return "Support guild has no text channels."
        try:
            member = await guild.fetch_member(interaction.user.id)
        except discord.NotFound:
            member = None
        if member is not None:
            return "You are already in the support guild."
        channels: discord.TextChannel = guild.text_channels
        for channel in channels:
            try:
                invite: discord.Invite = await channel.create_invite(
                    reason=f"Created invite for {interaction.user.name} from server {interaction.guild.name} ({interaction.guild_id})",
                    max_age=60,
                    max_uses=1,
                    unique=True
                )
                return invite.url
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue
        return "Could not create invite. There is either no text-channel, or I don't have the rights to create an invite."


    async def topgg():
        headers = {
            'Authorization': topgg_token,
            'Content-Type': 'application/json'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://top.gg/api/bots/{bot.user.id}/stats', headers=headers, json={'server_count': len(bot.guilds), 'shard_count': len(bot.shards)}) as resp:
                    if resp.status != 200:
                        print(f'Failed to update top.gg: {resp.status} {resp.reason}')
            try:
                await asyncio.sleep(60*30)
            except asyncio.CancelledError:
                pass


    async def webhook_count_activity():
        async def function():
            webhook_count = 0
            for guild in bot.guilds:
                try:
                    webhooks = await guild.webhooks()
                    for webhook in webhooks:
                        if webhook.user == bot.user:
                            webhook_count += 1
                except discord.Forbidden:
                    continue
                except discord.DiscordServerError:
                    continue
            with open(activity_file, 'r', encoding='utf8') as f:
                data = json.load(f)
            data['activity_type'] = 'Watching'
            data['activity_title'] = f"{webhook_count} webhooks in {len(bot.guilds)} guilds."
            data['activity_url'] = ''
            with open(activity_file, 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
            pt(f'Updated activity: {webhook_count} webhooks in {len(bot.guilds)} guilds.')

        while not shutdown:
            await function()
            try:
                await asyncio.sleep(60*5)
            except asyncio.CancelledError:
                pass


##Owner Commands
class Owner():
    async def activity(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'activity [playing/streaming/listening/watching/competing] [title] (url) - Set the activity of the bot\n'
                                       '```')
        def isURL(zeichenkette):
            try:
                ergebnis = urlparse(zeichenkette)
                return all([ergebnis.scheme, ergebnis.netloc])
            except:
                return False

        def remove_and_save(liste):
            if liste and isURL(liste[-1]):
                return liste.pop()
            else:
                return None

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        url = remove_and_save(args[1:])
        title = ' '.join(args[1:])
        print(title)
        print(url)
        with open(activity_file, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'playing':
            data['activity_type'] = 'Playing'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'streaming':
            data['activity_type'] = 'Streaming'
            data['activity_title'] = title
            data['activity_url'] = url
        elif action == 'listening':
            data['activity_type'] = 'Listening'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'watching':
            data['activity_type'] = 'Watching'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'competing':
            data['activity_type'] = 'Competing'
            data['activity_title'] = title
            data['activity_url'] = ''
        else:
            await __wrong_selection()
            return
        with open(activity_file, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Activity set to {action} {title}{" " + url if url else ""}.')


    async def status(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'status [online/idle/dnd/invisible] - Set the status of the bot\n'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        with open(activity_file, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'online':
            data['status'] = 'online'
        elif action == 'idle':
            data['status'] = 'idle'
        elif action == 'dnd':
            data['status'] = 'dnd'
        elif action == 'invisible':
            data['status'] = 'invisible'
        else:
            await __wrong_selection()
            return
        with open(activity_file, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Status set to {action}.')


    async def shutdown(message):
        global shutdown
        await message.channel.send('Engine powering down...')
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        await bot.close()


##Bot Commands----------------------------------------
#Bot Information
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    await interaction.response.defer()

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

    await interaction.edit_original_response(embed=embed)
#Support Invite
if support_available:
    @tree.command(name = 'support', description = 'Get invite to our support server.')
    @discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
    async def self(interaction: discord.Interaction):
        if str(interaction.guild.id) != support_id:
            await interaction.response.defer(ephemeral = True)
            await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral = True)
        else:
            await interaction.response.send_message('You are already in our support server!', ephemeral = True)
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
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
@discord.app_commands.describe(name='Name of the webhook.', channel='Channel the webhook should be created in.')
async def self(interaction: discord.Interaction, name: str, channel: discord.TextChannel):
    if channel.permissions_for(interaction.user).manage_webhooks:
        webhook = await interaction.channel.create_webhook(name=name, reason=f'Created by {interaction.user.name}#{interaction.user.discriminator} ({interaction.user.id})')
        await interaction.response.send_message(f'Webhook for channel {channel.mention}:\n{webhook.url}', ephemeral=True)
    else:
        await interaction.response.send_message(f'You need the permission "Manage Webhooks" for {channel.mention} to use this command!', ephemeral=True)




if __name__ == '__main__':
    if not TOKEN:
        sys.exit('Missing token. Please check your .env file.')
    else:
        try:
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            sys.exit('Invalid token. Please check your .env file.')
        except asyncio.CancelledError:
            if shutdown:
                pass
