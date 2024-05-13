import os
import json
import requests
import discord
from discord.ext import commands

with open('config.json') as f:
    config = json.load(f)
 
 # MORE COMING SOON

prefix = config.get('prefix')
token = config.get('token')
ltc_priv_key = config.get('ltckey')
ltc_addy = config.get('ltc_address')
	
client = commands.Bot(command_prefix=prefix, self_bot=True, help_command=None)

@client.event
async def on_connect():
	os.system("clear||cls")
	print(f"Logged In: {client.user}")


@client.command()
async def help(ctx):
    await ctx.send(f"""
    > **Ltc Wallet | SelfBot**
    
    > {prefix}balance [addy] - Shows Ltc Addy Balance
    > {prefix}recieve - Shows Your Ltc Addy
    > {prefix}send [addy] [amount in usd]  - send ltc to a addy
    """)

@client.command(aliases=['bal'])
async def balance(ctx, addy):
	response = requests.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{addy}/balance')
	if response.status_code != 200:
		if response.status_code == 400:
			await ctx.send("Invalid LTC address.")
		else:
			await ctx.send(f"Failed to retrieve balance. Error {response.status_code}. Please try again later", delete_after=5)
			return
	data = response.json()
	balance = data['balance'] / 10 ** 8
	total_balance = data['total_received'] / 10 ** 8
	unconfirmed_balance = data['unconfirmed_balance'] / 10 ** 8
	cg_response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd')
	if cg_response.status_code != 200:
		await ctx.send(f"Failed to retrieve the current price of LTC. Error {cg_response.status_code}. Please try again later", delete_after=5)
		return
	usd_price = cg_response.json()['litecoin']['usd']
	usd_balance = balance * usd_price
	usd_total_balance = total_balance * usd_price
	usd_unconfirmed_balance = unconfirmed_balance * usd_price
	message = f"LTC Address: `{addy}`\n"
	message += f"__Current LTC__ ~ **${usd_balance:.2f} USD**\n"
	message += f"__Total LTC Received__ ~ **${usd_total_balance:.2f} USD**\n"
	message += f"__Unconfirmed LTC__ ~ **${usd_unconfirmed_balance:.2f} USD**"
	await ctx.send(message, delete_after=30)
       

@client.command(aliases=['addy'])
async def recieve(ctx):
	await ctx.message.delete()
	await ctx.send(f"{ltc_addy}\n")

@client.command(aliases=["pay", "sendltc"])
async def send(ctx, addy, amount):
	if "$" in amount:
		object = amount.split("$")
		amount = float(amount[:-1])
	else:
		amount = float(amount)
	message = await ctx.send(f"Sending {amount}$ To {addy}")
	r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies=ltc")
	usd_price = r.json()['usd']['ltc']
	topay = (usd_price * amount)
	payload = {
	"sender": ltc_addy, 
	"private_key": ltc_priv_key,
	"amount": round(topay, 8),
	"receiver": addy
	}
	headers = {
	"accept": "application/json",
	"content-type": "application/json",
	}
	transaction = requests.post(f"https://litecoinapi-send.vercel.app/api/litecoin/send", json=payload) #oWN API HEHEHEH
	await message.edit(content=f"> Successfully Sent {amount}$ To {addy}\n{transaction.text}")
	


client.run(token)
