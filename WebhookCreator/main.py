#Import
import time
startupTime_start = time.time()
import aiohttp
import asyncio
import datetime
import discord
import json
import jsonschema
import os
import platform
import psutil
import sentry_sdk
import signal
import sys
from aiohttp import web
from CustomModules import log_handler
from dotenv import load_dotenv
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile



load_dotenv()
discord.VoiceClient.warn_nacl = False
APP_FOLDER_NAME = 'WH-Creator'
BOT_NAME = 'WebhookCreator'
if not os.path.exists(APP_FOLDER_NAME):
    os.makedirs(APP_FOLDER_NAME)
ACTIVITY_FILE = os.path.join(APP_FOLDER_NAME, 'activity.json')
BOT_VERSION = "1.9.1"
TOKEN = os.getenv('TOKEN')
OWNERID = os.getenv('OWNER_ID')
SUPPORTID = os.getenv('SUPPORT_SERVER')
TOPGG_TOKEN = os.getenv('TOPGG_TOKEN')
LOG_LEVEL = os.getenv('LOG_LEVEL')

#Sentry
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
    release=f'{BOT_NAME}@{BOT_VERSION}'
)

#Set-up logging
os.makedirs(f'{APP_FOLDER_NAME}//Logs', exist_ok=True)
os.makedirs(f'{APP_FOLDER_NAME}//Buffer', exist_ok=True)
LOG_FOLDER = f'{APP_FOLDER_NAME}//Logs//'
BUFFER_FOLDER = f'{APP_FOLDER_NAME}//Buffer//'
log_manager = log_handler.LogManager(LOG_FOLDER, BOT_NAME, LOG_LEVEL)
discord_logger = log_manager.get_logger('discord')
program_logger = log_manager.get_logger('Program')
program_logger.info('Engine powering up...')


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
                    program_logger.debug(f'ValidationError: {ve}')
                    self.write_default_content()
                except json.decoder.JSONDecodeError as jde:
                    program_logger.debug(f'JSONDecodeError: {jde}')
                    self.write_default_content()
        else:
            self.write_default_content()

    def write_default_content(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.default_content, file, indent=4)
validator = JSONValidator(ACTIVITY_FILE)
validator.validate_and_fix_json()


#Bot
class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(owner_id = OWNERID,
                              intents = intents,
                              status = discord.Status.invisible,
                              auto_reconnect = True
                        )
        self.synced = False
        self.initialized = False
        self.webhook_count = 0
        self.guild_count = 0


    async def on_message(self, message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'broadcast - Broadcast a message to all server owners\n'
                                       'help - Shows this message\n'
                                       'log - Get the log\n'
                                       'shutdown - Shutdown the bot\n'
                                       '```')

        if message.guild is None and message.author.id == int(OWNERID):
            args = message.content.split(' ')
            program_logger.debug(args)
            command, *args = args
            if command == 'help':
                await __wrong_selection()
                return
            elif command == 'log':
                await Owner.log(message, args)
                return
            elif command == 'shutdown':
                await Owner.shutdown(message)
                return
            elif command == 'broadcast':
                await Owner.broadcast(' '.join(args))
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
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{str(datetime.timedelta(seconds=int(error.retry_after)))}`', ephemeral=True)
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
                    program_logger.warning(f"Unexpected error while sending message: {e}")
            finally:
                try:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}")
                except AttributeError:
                    program_logger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}")
                sentry_sdk.capture_exception(error)

    async def on_ready(self):
        if self.initialized:
            return
        if not self.synced:
            program_logger.info('Syncing commands...')
            await tree.sync()
            program_logger.debug('Commands synced.')
            self.synced = True
        global owner, start_time, shutdown
        shutdown = False
        try:
            owner = await bot.fetch_user(OWNERID)
            program_logger.debug('Owner found.')
        except:
            program_logger.debug('Owner not found.')

        #Start background tasks
        if TOPGG_TOKEN:
            bot.loop.create_task(Functions.topgg())
        bot.loop.create_task(Functions.health_server())
        bot.loop.create_task(Functions.webhook_count_activity())

        program_logger.info(r'''
 __      __          __       __                      __      ____                          __
/\ \  __/\ \        /\ \     /\ \                    /\ \    /\  _`\                       /\ \__
\ \ \/\ \ \ \     __\ \ \____\ \ \___     ___     ___\ \ \/'\\ \ \/\_\  _ __    __     __  \ \ ,_\   ___   _ __
 \ \ \ \ \ \ \  /'__`\ \ '__`\\ \  _ `\  / __`\  / __`\ \ , < \ \ \/_/_/\`'__\/'__`\ /'__`\ \ \ \/  / __`\/\`'__\
  \ \ \_/ \_\ \/\  __/\ \ \L\ \\ \ \ \ \/\ \L\ \/\ \L\ \ \ \\`\\ \ \L\ \ \ \//\  __//\ \L\.\_\ \ \_/\ \L\ \ \ \/
   \ `\___x___/\ \____\\ \_,__/ \ \_\ \_\ \____/\ \____/\ \_\ \_\ \____/\ \_\\ \____\ \__/.\_\\ \__\ \____/\ \_\
    '\/__//__/  \/____/ \/___/   \/_/\/_/\/___/  \/___/  \/_/\/_/\/___/  \/_/ \/____/\/__/\/_/ \/__/\/___/  \/_/
        ''')
        start_time = datetime.datetime.now()
        program_logger.info(f"Initialization completed in {time.time() - startupTime_start} seconds.")
        self.initialized = True
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error


class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        program_logger.info('Received signal to shutdown...')
        bot.loop.create_task(Owner.shutdown(owner))


# Check if all required variables are set
support_available = bool(SUPPORTID)



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
            program_logger.warning(f'Error while starting health server: {e}')

    async def create_support_invite(interaction):
        try:
            guild = bot.get_guild(int(SUPPORTID))
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
            'Authorization': TOPGG_TOKEN,
            'Content-Type': 'application/json'
        }
        while not shutdown:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'https://top.gg/api/bots/{bot.user.id}/stats', headers=headers, json={'server_count': len(bot.guilds), 'shard_count': len(bot.shards)}) as resp:
                    if resp.status != 200:
                        program_logger.debug(f'Failed to update top.gg: {resp.status} {resp.reason}')
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
                except (discord.Forbidden, discord.DiscordServerError, discord.NotFound):
                    continue
            if webhook_count == bot.webhook_count and len(bot.guilds) == bot.guild_count:
                return
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{webhook_count} webhooks in {len(bot.guilds)} guilds.'
                )
            await bot.change_presence(activity = activity, status = discord.Status.online)
            bot.webhook_count = webhook_count
            bot.guild_count = len(bot.guilds)
            program_logger.info(f'Updated activity: {webhook_count} webhooks in {len(bot.guilds)} guilds.')

        while not shutdown:
            await function()
            try:
                await asyncio.sleep(60*5)
            except asyncio.CancelledError:
                pass


##Owner Commands
class Owner():
    async def log(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'log [current/folder/lines] (Replace lines with a positive number, if you only want lines.) - Get the log\n'
                                       '```')
        if args == []:
            await __wrong_selection()
            return
        if args[0] == 'current':
            try:
                await message.channel.send(file=discord.File(f'{LOG_FOLDER}{BOT_NAME}.log'))
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(f'{BUFFER_FOLDER}Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                        f.write(f'{LOG_FOLDER}{BOT_NAME}.log')
                    try:
                        await message.channel.send(file=discord.File(f'{BUFFER_FOLDER}Logs.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await message.channel.send("The log is too big to be sent directly.\nYou have to look at the log in your server (VPS).")
                    os.remove(f'{BUFFER_FOLDER}Logs.zip')
                    return
        elif args[0] == 'folder':
            if os.path.exists(f'{BUFFER_FOLDER}Logs.zip'):
                os.remove(f'{BUFFER_FOLDER}Logs.zip')
            with ZipFile(f'{BUFFER_FOLDER}Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                for file in os.listdir(LOG_FOLDER):
                    if file.endswith(".zip"):
                        continue
                    f.write(f'{LOG_FOLDER}{file}')
            try:
                await message.channel.send(file=discord.File(f'{BUFFER_FOLDER}Logs.zip'))
            except discord.HTTPException as err:
                if err.status == 413:
                    await message.channel.send("The folder is too big to be sent directly.\nPlease get the current file or the last X lines.")
            os.remove(f'{BUFFER_FOLDER}Logs.zip')
            return
        else:
            try:
                if int(args[0]) < 1:
                    await __wrong_selection()
                    return
                else:
                    lines = int(args[0])
            except ValueError:
                await __wrong_selection()
                return
            with open(f'{LOG_FOLDER}{BOT_NAME}.log', 'r', encoding='utf8') as f:
                with open(f'{BUFFER_FOLDER}log-lines.txt', 'w', encoding='utf8') as f2:
                    count = 0
                    for line in (f.readlines()[-lines:]):
                        f2.write(line)
                        count += 1
            await message.channel.send(content=f'Here are the last {count} lines of the current logfile:', file=discord.File(f'{BUFFER_FOLDER}log-lines.txt'))
            if os.path.exists(f'{BUFFER_FOLDER}log-lines.txt'):
                os.remove(f'{BUFFER_FOLDER}log-lines.txt')
            return

    async def shutdown(message):
        global shutdown
        program_logger.info('Engine powering down...')
        try:
            await message.channel.send('Engine powering down...')
        except:
            await owner.send('Engine powering down...')
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

        await bot.close()

    async def broadcast(message):
        already_send = []
        success = 0
        forbidden = 0
        error = 0
        for guild in bot.guilds:
            guild_owner = await bot.fetch_user(guild.owner_id)
            if guild_owner.id in already_send:
                continue
            try:
                await guild_owner.send(f'Broadcast from the owner of the bot:\n{message}')
                success += 1
                already_send.append(guild_owner.id)
            except discord.Forbidden:
                forbidden += 1
            except Exception as e:
                error += 1
        await owner.send(f'Broadcast finished.\nSuccess: {success}\nForbidden: {forbidden}\nError: {error}')


##Bot Commands----------------------------------------
#Bot Information
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def botinfo(interaction: discord.Interaction):
    await interaction.response.defer()

    member_count = sum(guild.member_count for guild in bot.guilds)

    embed = discord.Embed(
        title=f"Informationen about {bot.user.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

    embed.add_field(name="Created at", value=bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), inline=True)
    embed.add_field(name="Bot-Version", value=BOT_VERSION, inline=True)
    embed.add_field(name="Uptime", value=str(datetime.timedelta(seconds=int((datetime.datetime.now() - start_time).total_seconds()))), inline=True)

    embed.add_field(name="Bot-Owner", value=f"<@!{OWNERID}>", inline=True)
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
    embed.add_field(name="Invite", value=f"[Invite me](https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=536871936&scope=bot%20applications.commands)", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    if interaction.user.id == int(OWNERID):
        # Add CPU and RAM usage
        process = psutil.Process(os.getpid())
        cpu_usage = process.cpu_percent()
        ram_usage = round(process.memory_percent(), 2)
        ram_real = round(process.memory_info().rss / (1024 ** 2), 2)

        embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_real} MB", inline=True)

    await interaction.edit_original_response(embed=embed)
#Support Invite
if support_available:
    @tree.command(name = 'support', description = 'Get invite to our support server.')
    @discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
    async def support(interaction: discord.Interaction):
        if str(interaction.guild.id) != SUPPORTID:
            await interaction.response.defer(ephemeral = True)
            await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral = True)
        else:
            await interaction.response.send_message('You are already in our support server!', ephemeral = True)
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
async def ping(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! `{int(ping)}ms`')
##Main Commands----------------------------------------
#Create Webhook
@tree.command(name = 'create_webhook', description = 'Create a webhook.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel.id))
@discord.app_commands.describe(name='Name of the webhook.', channel='Channel the webhook should be created in.')
async def create_webhook(interaction: discord.Interaction, name: str, channel: discord.TextChannel):
    if name.lower() in ['discord', 'wumpus']:
        await interaction.response.send_message('Please choose a different name for your webhook.', ephemeral=True)
        return
    if not channel.permissions_for(interaction.user).manage_webhooks:
        await interaction.response.send_message(f'You need the permission "Manage Webhooks" for {channel.mention} to use this command!', ephemeral=True)
        return
    if not channel.permissions_for(interaction.guild.me).manage_webhooks:
        await interaction.response.send_message(f'I need the permission "Manage Webhooks" for {channel.mention} to use this command!', ephemeral=True)
        return
    if len(name) < 1 or len(name) > 80 or name.strip() == '':
        name = 'WebhookCreator'
    try:
        webhook = await channel.create_webhook(name=name, reason=f'Created by {interaction.user.name}#{interaction.user.discriminator} ({interaction.user.id})')
        await interaction.response.send_message(f'Webhook for channel {channel.mention}:\n{webhook.url}', ephemeral=True)
    except discord.errors.HTTPException as e:
        if e.code == 30007:
            await interaction.response.send_message(f'You reached the maximum amount of webhooks in this guild.\nThis is a limit, imposed by discord, which I can\'t change.', ephemeral=True)
        else:
            _message = f'Error while creating webhook: {e}'    
            await interaction.response.send_message(_message, ephemeral=True)
            program_logger.error(_message)




if __name__ == '__main__':
    if not TOKEN:
        error_message = 'Missing token. Please check your .env file.'
        program_logger.critical(error_message)
        sys.exit(error_message)
    else:
        try:
            SignalHandler()
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            error_message = 'Invalid token. Please check your .env file.'
            program_logger.critical(error_message)
            sys.exit(error_message)
        except asyncio.CancelledError:
            if shutdown:
                pass
