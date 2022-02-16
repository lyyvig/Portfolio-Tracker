from datetime import datetime
import json
import os
from time import sleep
from discord.ext import commands, tasks
from Entities import Account, Asset
from Manager import AccountManager, AssetManager, TrackManager

bot = commands.Bot(command_prefix='!', description='Hi')
asset_manager = AssetManager()
account_manager = AccountManager()
track_manager = TrackManager()

config = {"aliases": {}, "channel_id": 0}

def __write_config():
    a= open("config.json", "w")
    a.write(str(config).replace("'", "\""))
    a.close()

def __read_config():
    global config
    try:
        f = open("config.json", "r")
        config = json.loads(f.read())
        f.close()
    except FileNotFoundError:
        __write_config()
    except:
        pass

__read_config()



@bot.command()
async def add(ctx: commands.context.Context, api_key, api_secret):
    account = Account(0, str(ctx.author.id), api_key, api_secret)
    if(account_manager.exists(account.discord_id)):
        await ctx.send("Account is already added")
    else:
        account_manager.add(account)

@bot.command()
async def delete(ctx: commands.context.Context):
    discord_id = str(ctx.author.id)
    if(not account_manager.exists(discord_id)):
        await ctx.send("Account doesn't exist")
    else:
        account_manager.delete(discord_id)
    
@bot.command()
async def balance(ctx: commands.context.Context, discord_id=None):
    if(discord_id):
        discord_id = discord_id[3:-1]
    else:
        discord_id = str(ctx.author.id)
    print(discord_id)

    if(not account_manager.exists(discord_id)):
        await ctx.send("Account doesn't exist")
        return

    balance = asset_manager.get_balance(discord_id)
    await ctx.send("Balance: %.2f$" % (balance))





@bot.command()
async def assets(ctx: commands.context.Context, discord_id=None):
    if(discord_id):
        discord_id = discord_id[3:-1]
    else:
        discord_id = str(ctx.author.id)

    assets = asset_manager.get_all(discord_id)

    if(not account_manager.exists(discord_id)):
        await ctx.send("Account doesn't exist")
        return

    await ctx.send("%-7s %-15s %15s %10s %10s" %
                   ("Asset", "Amount", "BuytimeVal", "Worth", "Profit"))
    for asset in assets:
        await ctx.send("%-7s %-.5f %.1f$ %.2f$ %.2f%%" %
                       (asset.asset_name, asset.amount, asset.buytime_worth,
                        asset.value, (asset.value - asset.buytime_worth) / asset.buytime_worth * 100))

@bot.command()
async def asset(ctx: commands.context.Context, sub_command, asset, amount=0):
    discord_id = str(ctx.author.id)
    if(sub_command in ('add', 'a', 'append')):
        asset_manager.add(Asset(asset_name=asset.upper(), amount=amount, discord_id=discord_id, is_staked=1), account_manager.get_by_discord_id(discord_id))
    elif(sub_command in ('del', 'd', 'delete')):
        asset_manager.delete(asset, discord_id)






@bot.command() 
async def track(ctx: commands.context.Context, sub_command, asset):
    if (sub_command.lower() in ('a', 'add', 'append')):
        track_manager.add(asset.upper())
    elif(sub_command.lower() in ('d', 'del', 'delete')):
        track_manager.delete(asset.upper())

@bot.command()
async def alert(ctx: commands.context.Context, asset):
    track_manager.add_alert(asset.upper())






@bot.command()
async def bn(ctx: commands.context.Context, asset, currency="USDT"):
    try:
        if asset in config["aliases"]:
            asset = config["aliases"][asset]
        price = asset_manager.get_price(asset.upper() + currency)
        await ctx.send("%s's price: %.4f"%(asset.upper(), price))
    except:
        await ctx.send("Coin does not exist")




@bot.command()
async def set_channel(ctx: commands.context.Context):
    config["channel_id"] = ctx.channel.id
    __write_config()

@bot.command()
async def alias(ctx: commands.context.Context, key, value):
    config["aliases"][key] = value
    __write_config()


async def __buy_sell_check(channel):
    accounts = account_manager.get_all()
    for account in accounts:
        changes = asset_manager.check_changes(account)
        for change in changes:
            if(change["change"] > 0):
                isbuy = "bought"
            else:
                isbuy = 'sold'
            if("USD" not in change["asset"]):
                await channel.send("<@!%s> just %s %.4f %s at %.4f$ worth of %.2f$ @everyone" % (
                    account.discord_id, isbuy, change["change"], change["asset"],
                    change["price"], change["change"] * change["price"]
                ))

async def __track_alert_check(channel, interval):
    alerts = track_manager.check_alert()
    for alert in alerts:
        await channel.send("%s just went %s %.4f$ @everyone"%(
            alert["asset"], alert["change"], alert["price"]
        ))

    tracks = track_manager.check_interval(interval)
    for track in tracks:
        await channel.send("%s changed %.2f%% in last %s Price: %.4f$ @everyone"%(
            track["asset"], track["change_percentage"], track["interval"], track["price"]
        ))


@tasks.loop(seconds=60)
async def min_check():
    await bot.wait_until_ready()
    channel = bot.get_channel(config["channel_id"])
    if(not channel):
        return
    await __buy_sell_check(channel)
    await __track_alert_check(channel, '1m')
    tm = datetime.now()
    if(tm.minute == 0):
        await __track_alert_check(channel, '1h')
        if(tm.hour%4 == 0):
            await __track_alert_check(channel, '4h')
            if(tm.hour == 0):
                await __track_alert_check(channel, '1d')


@bot.event
async def on_ready():
    print("Bot ready %s"%(bot.user))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if(not config["channel_id"]):
        config["channel_id"] = message.channel.id
        __write_config()
    
    

sleep(62-datetime.now().second)
min_check.start()
bot.run(os.environ['TOKEN'])
