from botmodule import botmodule 
import discord
import sys

# Tagging module
class moduleClass(botmodule):
	def default_config(self):
		return {"table_id": "main"}

	async def on_connect(self, client, config):
		self.tablename = "tags_" + config["table_id"]
		query = "CREATE TABLE IF NOT EXISTS " + self.tablename + "(id INTEGER PRIMARY KEY ASC, name text UNIQUE NOT NULL, tagtext text DEFAULT '')"
		await client.db_query(query)
		await client.db_commit()

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if (not message.author.id == client.user.id) and cmd:
			command = cmd["cmd"]
			args = cmd["args"]
			if (command == "tag") and len(args)>1:
				try:
					await client.db_query("INSERT OR IGNORE INTO " + self.tablename + " (name) VALUES (?)", (args[0], ))
					await client.db_query("UPDATE " + self.tablename + " SET tagtext = ? WHERE name=?", (' '.join(w for w in args[1:]), args[0]))
					await client.db_commit()
					await message.channel.send("Tagged " + args[0] + " with '" + ' '.join(w for w in args[1:]) + "'")
				except:
					await message.channel.send("Couldn't set tag")
					for error in sys.exc_info():
						print(str(error))
			elif (command == "deltag") and args and cmd["admin"]:
				if len(args) != 1:
					await message.channel.send("Give a single tag to delete")
				else:
					try:
						await client.db_query("DELETE FROM " + self.tablename + " WHERE name=?", (args[0], ))
						await client.db_commit()
						await message.channel.send("Deleted " + args[0] + " from tags")
					except:
						await message.channel.send("Something went wrong deleting " + args[0] + " from list")
						for error in sys.exc_info():
							print(str(error))
			else:
				tags = await client.db_query("SELECT name FROM " + self.tablename)
				for tag in tags:
					if tag[0] == command:
						tagtext = await client.db_query("SELECT tagtext FROM " + self.tablename + " WHERE name=?", (command, ))
						tagmsg = tagtext[0][0]
						await client.db_commit()
						await message.channel.send(tagmsg)
