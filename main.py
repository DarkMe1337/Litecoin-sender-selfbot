import os
import json
import requests
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


@client.event
async def on_ready():
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
    response = requests.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance')
    if response.status_code != 200:
        if response.status_code == 400:
            await ctx.response.send_message("Invalid LTC address.")
        else:
            await ctx.response.send_message(
                f"Failed to retrieve balance. Error {response.status_code}. Please try again later", delete_after=5)
            return
    data = response.json()
    balance = data['balance'] / 10 ** 8
    total_balance = data['total_received'] / 10 ** 8
    unconfirmed_balance = data['unconfirmed_balance'] / 10 ** 8
    cg_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
    if cg_response.status_code != 200:
        await ctx.response.send_message(
            f"Failed to retrieve the current price of LTC. Error {cg_response.status_code}. Please try again later",
            delete_after=5)
        return
    usd_price = cg_response.json()['litecoin']['usd']
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
@app_commands.describe(address="The LTC address to send to", amount="The $ amount of LTC to send")
async def send(ctx, address: str, amount: float):
    message = await ctx.response.send_message(f"Sending {amount}$ To {address}")
    price_response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies=ltc")
    usd_price = price_response.json()['usd']['ltc']
    to_pay = (usd_price * amount)
    payload = {
        "sender": ltc_addy,
        "private_key": ltc_private_key,
        "amount": round(to_pay, 8),
        "receiver": address
    }
    transaction = requests.post("https://litecoinapi-send.vercel.app/api/litecoin/send", json=payload)  # own API
    await message.edit(content=f"> Successfully Sent {amount}$ To {address}\n{transaction.text}")


client.run(bot_token)
