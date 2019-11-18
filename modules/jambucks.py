from botmodule import botmodule 
import logging
import traceback
import re

mentionmatch = re.compile(r'^<@!?\d+>$')

class moduleClass(botmodule):
	def default_config(self):
		return {"table_id": "global",
				"name": "Jambucks",
				"symbol": "ʝ", #<:heh:255037771167694848>
				"default_balance": 100} 

	def on_init(self):
		self.logger = logging.getLogger("jambot.jambucks")

	async def create_account(self, client, config, userid):
		await client.db_query("INSERT OR IGNORE INTO  " + self.tablename + " (id, val) VALUES (?, ?)", (userid, config["default_balance"]))
		await client.db_commit()

	async def get_bal(self, client, config, userid):
		bal = await client.db_query("SELECT val FROM " + self.tablename + " WHERE id=(?)", (userid))
		await client.db_commit()
		return bal[0][0]

	async def transfer_val(self, client, config, sender, recipient, amount):
		await client.db_query("UPDATE " + self.tablename + " SET val=val+(?) WHERE id=(?)", (amount, recipient))
		await client.db_query("UPDATE " + self.tablename + " SET val=val-(?) WHERE id=(?)", (amount, sender))
		await client.db_commit()

	async def check_enabled(self, client, config, userid):
		active = await client.db_query("SELECT active FROM " + self.tablename + " WHERE id=(?)", (userid))
		await client.db_commit()
		return active[0][0]

	async def on_connect(self, client, config):
		self.tablename = "money_" + config["table_id"]
		query = "CREATE TABLE IF NOT EXISTS " + self.tablename + " (id int PRIMARY KEY, val int DEFAULT 0, active bool DEFUALT true)"
		await client.db_query(query)
		await client.db_commit()

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		command = cmd["cmd"]
		args = cmd["args"]
		admin = cmd["admin"]
		if command=="balance":
			await self.create_account(client, config, message.author.id)
			balance = await self.get_bal(client, config, message.author.id)
			await message.channel.send("Your balance is " + str(balance) + config["symbol"])
		if command=="send":
			if len(args) != 2:
				await message.channel.send("Send " + config["name"] + " to someone, usage: " + client.cmd_prefix() + "send @Recipient amount")
			else if not mentionmatch.match(args[0]):
				await message.channel.send("Unknown user " + args[0] + ", use a @Mention to select user, usage: " + client.cmd_prefix() + "send @Recipient amount")
			else if not args[1].isdigit():
				await message.channel.send("Not sure how to send " + args[1] + config["symbol"] + ", usage: " + client.cmd_prefix() + "send @Recipient amount")
			else if len(message.mentions) != 1:
				await message.channel.send("Can only send to a single user at once, usage: " + client.cmd_prefix() + "send @Recipient amount")
			else:
				recipient = message.mentions[0].id
				sender = message.author.id
				amount = int(args[1])
				await self.create_account(client, config, sender)
				sender_bal = await self.get_bal(client, config, sender)
				if amount > sender_bal:
					await message.channel.send("You don't have enough " + config["name"] + " to send that much (You have " + str(sender_bal) + config["symbol"] + ")")
				else:
					await self.create_account(client, config, recipient)
					if self.check_enabled(client, config, sender) and self.check_enabled(client, config, sender):
						await self.transfer_val(client, config, sender, recipient, amount)
						new_bal = await self.get_bal(client, config, sender)
						await message.channel.send("You sent " + amount + config["symbol"]+ " to " + args[0] + " (New balance: " + new_bal + config["symbol"] + ")")
					else:
						await message.channel.send("Can't perform transaction, disabled account involved.")
		if command=="gift" and admin:
