#!/usr/bin/env python
import discord
import asyncio
import aioodbc #ayooodbck
import importlib
import yaml
import traceback
import sys
import botmodule
import logging
import json
import pyodbc

logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("jambolog.txt"),logging.StreamHandler()])

config_file = "jambot.yml"

class loaded_mods():
	def __init__(self):
		self.loaded = []
		self.instances = {}
	
	async def fetch_mod_context(self, configs, modname, server, channel):
		chanindex = str(modname) + str(server) + str(channel)
		servindex = str(modname) + str(server)
		if chanindex in self.instances:
			try:
				conf = configs["servers"][server]["channels"][channel][modname]
			except:
				conf = {}
			return {"module": self.instances[chanindex], "config": conf}
		elif servindex in self.instances:
			try:
				conf = configs["servers"][server][modname]
			except:
				conf = {}
			return {"module": self.instances[servindex], "config": conf}
		elif modname in self.instances:
			try:
				conf = configs[modname]
			except:
				conf = {}
			return {"module": self.instances[modname], "config": conf}
		return False

	async def fetch_mod_config(self, configs, instname):
		conf = {}
		module = self.instances[instname].name
		if self.instances[instname].context == "global":
			conf = configs[module]
		elif self.instances[instname].context == "server":
			conf = configs["servers"][self.instances[instname].server][module]
		elif self.instances[instname].context == "channel":
			conf = configs["servers"][self.instances[instname].server]["channels"][self.instances[instname].channel][module]
		return {"module": self.instances[instname], "config": conf}

	def loadmod(self, module, server = "", channel = ""):
		moduleClass = getattr(importlib.import_module("modules." + module), 'moduleClass')
		context = ""
		if server == "" and channel == "":
			context = "global"
		elif channel == "":
			context = "server"
		else:
			context = "channel"
		newmodule = moduleClass(module, context, server, channel)
		self.instances[module + str(server) + str(channel)] = newmodule
		if not module in self.loaded:
			self.loaded.append(module)


class jambot(discord.Client):
	def initialize(self, config_file):
		self.config_file = config_file
		with open(config_file) as stream:
			try:
				self.config = yaml.load(stream)
			except yaml.YAMLError as exc:
				print(exc)
		self.mods = loaded_mods()
		if "global_modules" in self.config:
			for module in self.config["global_modules"]:
				self.mods.loadmod(module)
				print("Loaded " + module + "(Global)")
				settings = self.mods.instances[module].defaults
				try:
					for setting in self.config[module]:
						settings[setting] = self.config[module][setting]
				except:
					pass
				self.config[module] = settings
		try:
			for server in self.config["servers"]:
				try:
					for channel in self.config["servers"][server]["channels"]:
						for module in self.config["servers"][server]["channels"][channel]["channel_modules"]:
							self.mods.loadmod(module, server, channel)
							print("Loaded " + module + str(server) + str(channel) + "(Channel)")
							settings = self.mods.instances[module + str(server) + str(channel)].defaults
							try:
								for setting in self.config["servers"][server]["channels"][channel][module]:
									settings[setting] = self.config["servers"][server]["channels"][channel][module][setting]
							except:
								pass
							self.config["servers"][server]["channels"][channel][module] = settings
				except KeyError:
					pass
				try:
					for module in self.config["servers"][server]["server_modules"]:
							self.mods.loadmod(module, server)
							print("Loaded " + module + str(server) + "(Server)")
							settings = self.mods.instances[module + str(server)].defaults
							try:
								for setting in self.config["servers"][server][module]:
									settings[setting] = self.config["servers"][server][module][setting]
							except:
								pass
							self.config["servers"][server][module] = settings
				except KeyError:
					pass
		except KeyError:
			pass

#DB
	async def db_query(self, query, params = ()):
		cur = await self.db.cursor()
		await cur.execute(query, params)
		try:
			r = await cur.fetchall()
		except pyodbc.ProgrammingError:
			r = []
		await cur.close()
		return r

	async def db_commit(self):
		await self.db.commit()

#Helpers

	async def get_context(self, channel):
		if isinstance(channel, discord.Reaction):
			channel = channel.message
		if isinstance(channel, discord.Message):
			channel = channel.channel
		if isinstance(channel, discord.TextChannel):
			return {"server": channel.guild.id, "channel": channel.id}
		else:
			return {"server": channel.id, "channel": channel.id}
		return {}

	def cmd_prefix(self):
		return self.config["command_prefix"]

	def get_cmd(self, message):
		cmd = self.config["command_prefix"]
		admin = False
		if message.author.id == self.config["owner"]:
			admin = True
		if (message.content[:len(cmd)] == cmd):
			cmdstring = message.content[len(cmd):].split()
			return {"cmd": cmdstring[0], "args": cmdstring[1:], "admin": admin}
		else:
			return False

#save
#load?

	async def save_config(self):
		mainkeys = ["database", "command_prefix", "version", "token", "owner"]


# Discord API Event Calls
# Channel-context calls

	async def on_typing(self, channel, user, when):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_typing(self, inst["config"], channel, user, when)

	async def on_message(self, message):
		cmd = self.get_cmd(message)
		if (cmd):
			if cmd["cmd"] == "save" and cmd["admin"]:
				print(yaml.dump(self.config, default_flow_style=False))
				print(json.dumps(self.config))
			if cmd["cmd"] == "load" and cmd["admin"]:
				pass
			if cmd["cmd"] == "set" and cmd["admin"]:
				pass
			if cmd["cmd"] == "get" and cmd["admin"]:
				pass
		for module in self.mods.loaded:
			context = await self.get_context(message)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_message(self, inst["config"], message)

	async def on_message_delete(self, message):
		for module in self.mods.loaded:
			context = await self.get_context(message)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_message_delete(self, inst["config"], message)

	async def on_message_edit(self, before, after):
		for module in self.mods.loaded:
			context = await self.get_context(before)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_message_edit(self, inst["config"], before, after)

	async def on_reaction_add(self, reaction, user):
		for module in self.mods.loaded:
			context = await self.get_context(reaction)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_reaction_add(self, inst["config"], reaction, user)

	async def on_reaction_remove(self, reaction, user):
		for module in self.mods.loaded:
			context = await self.get_context(reaction)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_reaction_remove(self, inst["config"], reaction, user)

	async def on_reaction_clear(self, message, reactions):
		for module in self.mods.loaded:
			context = await self.get_context(message)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_reaction_clear(self, inst["config"], message, reactions)

	async def on_private_channel_delete(self, channel):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_private_channel_delete(self, inst["config"], channel)

	async def on_private_channel_create(self, channel):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_private_channel_create(self, inst["config"], channel)

	async def on_private_channel_update(self, before, after):
		for module in self.mods.loaded:
			context = await self.get_context(before)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_private_channel_update(self, inst["config"], before, after)

	async def on_private_channel_pins_update(self, channel, last_pin):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_private_channel_pins_update(self, inst["config"], channel, last_pin)

	async def on_guild_channel_delete(self, channel):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_guild_channel_delete(self, inst["config"], channel)

	async def on_guild_channel_create(self, channel):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_guild_channel_create(self, inst["config"], channel)

	async def on_guild_channel_update(self, before, after):
		for module in self.mods.loaded:
			context = await self.get_context(before)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_guild_channel_update(self, inst["config"], before, after)

	async def on_guild_channel_pins_update(self, channel, last_pin):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_guild_channel_pins_update(self, inst["config"], channel, last_pin)

	async def on_webhooks_update(self, channel):
		for module in self.mods.loaded:
			context = await self.get_context(channel)
			inst = await self.mods.fetch_mod_context(self.config, module, context["server"], context["channel"])
			if inst != False:
				await inst["module"].on_webhooks_update(self, inst["config"], channel)

# All instance calls
	async def on_ready(self):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			await inst["module"].on_ready(self, inst["config"])

	async def on_connect(self):
		dsn = 'Driver=SQLite3;Database=' + self.config["database"]
		self.db = await aioodbc.connect(dsn=dsn, loop=self.loop) #needs to be setup after login/event loop is running
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			await inst["module"].on_connect(self, inst["config"])

	async def on_shard_ready(self, shard_id):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			await inst["module"].on_shard_ready(self, inst["config"], shard_id)

	async def on_resumed(self):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			await inst["module"].on_resumed(self, inst["config"])

	async def on_error(self, event, *args, **kwargs):
		await super(jambot, self).on_error(event, *args, **kwargs)
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			await inst["module"].on_error(self, inst["config"], event, *args, **kwargs)

# Global only calls

	async def on_socket_raw_receive(self, msg):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_socket_raw_receive(self, inst["config"], msg)

	async def on_socket_raw_send(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_socket_raw_send(self, inst["config"], payload)

	async def on_raw_message_delete(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_raw_message_delete(self, inst["config"], payload)

	async def on_raw_bulk_message_delete(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_raw_bulk_message_delete(self, inst["config"], payload)

	async def on_raw_message_edit(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_raw_message_edit(self, inst["config"], payload)

	async def on_raw_reaction_add(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_raw_reaction_add(self, inst["config"], payload)

	async def on_raw_reaction_remove(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_raw_reaction_remove(self, inst["config"], payload)

	async def on_raw_reaction_clear(self, payload):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			if inst["module"].context == "global":
				await inst["module"].on_raw_reaction_clear(self, inst["config"], payload)

# Server-level calls
	async def get_server_context(self, guild):
		if isinstance(guild, discord.Role) or isinstance(guild, discord.Member):
			guild = guild.guild
		return guild.id

	async def on_guild_join(self, guild):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_join(self, inst["config"], guild)

	async def on_guild_remove(self, guild):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_remove(self, inst["config"], guild)

	async def on_guild_update(self, before, after):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(before)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_update(self, inst["config"], before, after)

	async def on_guild_role_create(self, role):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(role)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_role_create(self, inst["config"], role)

	async def on_guild_role_delete(self, role):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(role)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_role_delete(self, inst["config"], role)

	async def on_guild_role_update(self, before, after):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(before)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_role_update(self, inst["config"], before, after)

	async def on_guild_emojis_update(self, guild, before, after):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_emojis_update(self, inst["config"], guild, before, after)

	async def on_guild_available(self, guild):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_available(self, inst["config"], guild)

	async def on_guild_unavailable(self, guild):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_guild_unavailable(self, inst["config"], guild)

	async def on_voice_state_update(self, member, before, after):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(member)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"]. on_voice_state_update(self, inst["config"], member, before, after)

	async def on_member_ban(self, guild, user):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_member_ban(self, inst["config"], guild, user)

	async def on_member_unban(self, guild, user):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(guild)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_member_unban(self, inst["config"], guild, user)

	async def on_member_update(self, before, after):
		for module in self.mods.instances:
			inst = await self.mods.fetch_mod_config(self.config, module)
			serv = await self.get_server_context(after)
			if inst["module"].context == "global" or (inst["module"].server == serv):
				await inst["module"].on_member_update(self, inst["config"], before, after)

#clean up db
	async def logout(self):
		self.pool.close()
		await self.pool.wait_closed()
		await super(jambot, self).on_error(event, *args, **kwargs)


if __name__ == "__main__":
	if "--help" in sys.argv:
		print("Jambot Modular Discord Bot. Usage:")
		print(" jambot.py [config file]")
		print("Defaults to jambot.cfg")
		sys.exit(0)
	if len(sys.argv) > 1:
		config_file = sys.argv[1]
	bot = jambot()
	try:
		bot.initialize(config_file)
		bot.run(bot.config["token"])
	except discord.errors.LoginFailure as e:
		print("Token is invalid.")
		exit()
	except:
		traceback.print_exc()
	exit()
