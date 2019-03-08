from botmodule import botmodule 
import discord
import random

class moduleClass(botmodule):

	def default_config(self):
		return {"santa_id": "main"}

	async def on_connect(self, client, config):
		self.tablename = "santa_" + config["santa_id"]
		query = "CREATE TABLE IF NOT EXISTS " + self.tablename + "(id INTEGER PRIMARY KEY ASC, discord_id text UNIQUE, address text, partner int DEFAULT NULL)"
		await client.db_query(query)
		await client.db_commit()

	async def on_message(self, client, config, message):
		cmd = await client.get_cmd(message)
		if cmd:
			if cmd["cmd"] == "santa" and isinstance(message.channel, discord.DMChannel):
				record = await client.db_query("SELECT address FROM " + self.tablename + " WHERE discord_id=?", (message.author.id, ))
				if cmd["args"]:
					if len(record) == 0:
						await client.db_query("INSERT OR IGNORE INTO " + self.tablename + " (discord_id) VALUES (?)", (message.author.id), )
						await client.db_query("UPDATE " + self.tablename + " SET address = ? WHERE discord_id=?", (" ".join(cmd["args"]), message.author.id))
						record = await client.db_query("SELECT address FROM " + self.tablename + " WHERE discord_id=?", (message.author.id, ))
						await message.channel.send("Added your address to the secret santa pool: " + record[0][0])
					else:
						prerecord = record[0][0]
						await client.db_query("UPDATE " + self.tablename + " SET address = ? WHERE discord_id=?", (" ".join(cmd["args"]), message.author.id))
						record = await client.db_query("SELECT address FROM " + self.tablename + " WHERE discord_id=?", (message.author.id, ))
						await message.channel.send("Updated your address from " + prerecord + " to " + record[0][0])
				else:
					if len(record) == 0:
						await message.channel.send("You aren't in the secret santa pool, use '>santa 123 myaddress' to add yourself")						
					else:
						record = await client.db_query("SELECT address FROM " + self.tablename + " WHERE discord_id=?", (message.author.id, ))
						await message.channel.send("I have this address for you in the santa pool: " + record[0][0])
			if cmd["cmd"] == "santashuffle" and cmd["admin"]:
				records = await client.db_query("SELECT id, discord_id, address FROM " + self.tablename)
				links = []
				index = list(range(1, len(records)))
				random.shuffle(index)
				print(index)
				last = 0
				while len(index) > 0:
					nextid = index.pop()
					links.append((last, nextid))
					last = nextid
				links.append((last, 0))
				links
				for i in links:
					user1 = await client.get_user_info(records[i[0]][1])
					user2 = await client.get_user_info(records[i[1]][1])
					print(user1.name + " > " + user2.name)
					await client.db_query("UPDATE " + self.tablename + " SET partner = ? WHERE id=?", (records[i[1]][0], records[i[0]][0]))
					message = "Your secret santa gift recipient is: " + user2.name + " and their address is: " + records[i[1]][2]
					dm = user1.dm_channel
					if user1.dm_channel == None:
						dm = await user1.create_dm()
					await dm.send(content=message)
			await client.db_commit()