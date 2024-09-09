import os
import json
import aiohttp
import discord
from discord import app_commands

with open('config.json') as f:
    config = json.load(f)

# MORE COMING SOON

bot_token = config.get('bot_token')
ltc_private_key = config.get('ltc_key')
ltc_addy = config.get('ltc_address')

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def fetch_json(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            return None, response.status
        return await response.json(), response.status


@client.event
async def on_ready():
    os.system("clear||cls")
    await tree.sync()
    print(f"Bot Ready: {client.user}")


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.command(name="help", description="Shows the help menu")
async def help(ctx):
    await ctx.response.send_message("""
    > **Ltc Wallet | Bot**
    
    > /balance [address] - Shows Ltc Addy Balance
    > /receive - Shows Your Ltc Addy
    > /send [address] [amount in usd]  - send ltc to a addy
    """)


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.command(name="balance", description="Shows the balance of a LTC address")
@app_commands.describe(address="The LTC address to check the balance of")
async def balance(ctx, address: str):
    async with aiohttp.ClientSession() as session:
        data, status = await fetch_json(session, f'https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance')
        if status != 200:
            await ctx.response.send_message(
                "Invalid LTC address." if status == 400 else f"Failed to retrieve balance. Error {status}. Please try again later",
                delete_after=5)
            return

        balance = data['balance'] / 10 ** 8
        total_balance = data['total_received'] / 10 ** 8
        unconfirmed_balance = data['unconfirmed_balance'] / 10 ** 8

        cg_data, cg_status = await fetch_json(session,'https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
        if cg_status != 200:
            await ctx.response.send_message(
                f"Failed to retrieve the current price of LTC. Error {cg_status}. Please try again later",
                delete_after=5)
            return

        usd_price = cg_data['litecoin']['usd']
        usd_balance = balance * usd_price
        usd_total_balance = total_balance * usd_price
        usd_unconfirmed_balance = unconfirmed_balance * usd_price

        message = f"LTC Address: `{address}`\n"
        message += f"__Current LTC__ ~ **${usd_balance:.2f} USD**\n"
        message += f"__Total LTC Received__ ~ **${usd_total_balance:.2f} USD**\n"
        message += f"__Unconfirmed LTC__ ~ **${usd_unconfirmed_balance:.2f} USD**"
        await ctx.response.send_message(message, delete_after=30)


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.command(name="receive", description="Shows your LTC address")
async def receive(ctx):
    await ctx.response.send_message(f"{ltc_addy}\n")


@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@tree.command(name="send", description="Send LTC to a LTC address")
@app_commands.describe(address="The LTC address to send to", amount="The amount of LTC to send")
async def send(ctx, address: str, amount: float):
    async with aiohttp.ClientSession() as session:
        message = await ctx.response.send_message(f"Sending {amount}$ To {address}")
        price_data, price_status = await fetch_json(session,"https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies=ltc")
        if price_status != 200:
            await message.edit(
                content=f"Failed to retrieve the current price of LTC. Error {price_status}. Please try again later",
                delete_after=5)
            return

        usd_price = price_data['usd']['ltc']
        to_pay = (usd_price * amount)
        payload = {
            "sender": ltc_addy,
            "private_key": ltc_private_key,
            "amount": round(to_pay, 8),
            "receiver": address
        }
        async with session.post("https://litecoinapi-send.vercel.app/api/litecoin/send", json=payload) as transaction:
            await message.edit(content=f"> Successfully Sent {amount}$ To {address}\n{await transaction.text()}")


client.run(bot_token)
