#!/usr/bin/env python
import discord
import asyncio
import configparser
import sys
import importlib
import threading
import sqlite3


config_file = "jambot.cfg"

class botModule():
	dbload = False

	def set(self, setting, value, desc = "", secret = False):
		try:
			desc = self.bot.settings[self.name][setting][1]
			secret = self.bot.settings[self.name][setting][2]
		except:
			pass
		self.bot.settings[self.name][setting] = (value, desc, secret)

	def get(self, setting):
		return self.bot.settings[self.name][setting][0]

	def init_settings(self):
		pass

	def is_command(self, message):
		return self.bot.is_command(message)

	def bind_events(self):
		pass

	def __init__(self, name, bot):
		self.bot = bot
		self.event_loop = asyncio.new_event_loop()
		self.c = discord.Client(loop=self.event_loop)
		self.name = name
		self.init_settings()
		self.bind_events()
		try:
			print("Connecting on module " + name + " with " + self.bot.config["jambot"]["token"])
			self.c.run(self.bot.config["jambot"]["token"])
			print("Connected " + name)
		except:
			traceback.print_exc()
			raise

	def db_query(self, statement, params=()):
		return self.bot.database_query(statement, params)

	def db_commit(self):
		self.bot.database_commit()

class botMain():
	def set(self, setting, value):
		self.settings["jambot"][setting] = value

	def get(self, setting):
		return self.settings["jambot"][setting]

	def _spawn_module_thread(self, module, moduleClass):
		return moduleClass(module, self)

	def _load_modules(self):
		for module in self.get("modules"):
			moduleClass = getattr(importlib.import_module("modules." + module), 'moduleClass')
			self.settings[module] = {}
			newmodule = threading.Thread(target=self._spawn_module_thread(module, moduleClass))
			self.modules.append(newmodule)
			newmodule.start()
			print("Loaded " + module)

	def _load_module_settings(self, loadtarget):
		error = True
		for module in self.modules:
			if module.name == loadtarget:
				error = False #right module was found in conf, attempt to parse it
				self.config.read(config_file)
				for setting in self.settings[loadtarget]:
					if loadtarget in self.config.sections():
						for conf in self.config[loadtarget]:
							if setting == conf: #we want to ignore both missing and extra configs, only attempt matching pairs
								value = self.settings[loadtarget][setting][0]
								try:
									if type(value) is int:
										module.set(setting, self.config[loadtarget].getint(conf))
									elif type(value) is float:
										module.set(setting, self.config[loadtarget].getfloat(conf))
									elif type(value) is bool:
										module.set(setting, self.config[loadtarget].getboolean(conf))
									else:
										module.set(setting, self.config[loadtarget][conf])
								except:
									error = True #at least one setting/conf pair is malformed
					else:
						error = True #Module settings don't exist in file
		return not error

	def _load_db(self):
		self.db = sqlite3.connect(self.get("database"), check_same_thread=False)

	def is_command(self, message):
		if message.content[0] == self.get("command_prefix"):
			args = message.content.split()[1:]
			command = message.content.split()[0].split(self.get("command_prefix"))[1]
			admin = False
			if message.author.id == self.get("owner"):
				admin = True
			return {"command": command, "args": args, "admin": admin}
		return False

	def initialize(self):
		self.config = configparser.ConfigParser()
		self.config.read(config_file)
		self.settings = {}
		self.settings["jambot"] = {}
		self.modules = []
		self.db = None
		self.client = discord.Client()
		self.set("modules", self.config["jambot"]["modules"].split())
		self.set("database", self.config["jambot"]["database"])
		self.set("command_prefix", self.config["jambot"]["command_prefix"][0])
		self.set("version", self.config["jambot"]["version"])
		self.set("token", self.config["jambot"]["token"])
		self.set("owner", self.config["jambot"]["owner"])
		self._load_modules()
		for module in self.get("modules"):
			self._load_module_settings(module)
		self._load_db()

		@self.client.event
		async def on_ready():
			#self.config = configparser.ConfigParser()
			#self.config.read(config_file)
			print('Logged in as ' + self.client.user.name + " " + self.client.user.id)
			print('------')

		@self.client.event
		async def on_message(message):
			command_sent = self.is_command(message)
			print(command_sent)
			if command_sent:
				args = command_sent["args"]
				command = command_sent["command"]
				admin = command_sent["admin"]
				if command == "save" and admin:
					conf = open(config_file, 'w')
					conf.write('[jambot]\n')
					for setting in self.settings["jambot"]: 
						newconf = self.settings["jambot"][setting]
						if type(newconf) is list:
							newconf = " ".join(self.settings["jambot"][setting])
						conf.write(setting + '\t= ' + str(newconf) + "\n")
					conf.write('\n')
					for module in self.get("modules"):
						conf.write('[' + module + ']\n')
						for setting in self.settings[module]:
							conf.write('# ' + str(self.settings[module][setting][1]) + "\n")
							conf.write(setting + '\t= ' + str(self.settings[module][setting][0]) + "\n")
						conf.write('\n')
					conf.close()
					await self.client.send_message(message.channel, "Saved new config to " + config_file)
				elif command == "set" and args:
					if len(args) >= 3 and admin:
						qmodule = args[0]
						qsetting = args[1]
						qvalue = " ".join(args[2:])
						if qmodule in self.get("modules"):
							if qsetting in self.settings[qmodule]:
								if not self.settings[qmodule][qsetting][2]:
									try:
										oldvalue = self.settings[qmodule][qsetting][0]
										newvalue = oldvalue
										if type(oldvalue) is float:
											newvalue = float(qvalue)
										elif type(oldvalue) is int:
											newvalue = int(qvalue)
										elif type(oldvalue) is bool:
											if qvalue.lower() in ['true', '1', 'on', 'y', 'yes']:
												newvalue = True
											elif qvalue.lower() in ['false', '0', 'off', 'n', 'no']:
												newvalue = False
										else:
											newvalue = str(qvalue)
										self.settings[qmodule][qsetting] = (newvalue, self.settings[qmodule][qsetting][1], self.settings[qmodule][qsetting][2])
										await self.client.send_message(message.channel, qmodule + " setting " + qsetting + " changed from " + str(oldvalue) + " to " + str(newvalue))
									except:
										await self.client.send_message(message.channel,qmodule + " setting " + qsetting + " could not be set to " + str(qvalue))
								else:
									await self.client.send_message(message.channel, qmodule + " setting " + qsetting + " is protected, set with config")
							else:
								await self.client.send_message(message.channel, qsetting + " isn't a setting of " + qmodule)
						else:
							await self.client.send_message(message.channel, qmodule + " is not a loaded module")
					elif len(args) == 2:
						qmodule = args[0]
						qsetting = args[1]
						if qmodule in self.get("modules"):
							if qsetting in self.settings[qmodule]:
								if not self.settings[qmodule][qsetting][2]:
									value = self.settings[qmodule][qsetting][0]
									await self.client.send_message(message.channel, qmodule + " setting " + qsetting + " is set to " + str(value))
								else:
									await self.client.send_message(message.channel, qmodule + " setting " + qsetting + " is protected, check with config")
							else:
								await self.client.send_message(message.channel, qsetting + " isn't a setting of " + qmodule)
						else:
							await self.client.send_message(message.channel, qmodule + " is not a loaded module")
					else:
						await self.client.send_message(message.channel, "Not enough args: expect 'modulename setting (value)'")

		self.client.run(self.config["jambot"]["token"])

	def database_query(self, statement, params):
		cursor = self.db.cursor()
		return cursor.execute(statement, params).fetchall()

	def database_commit(self):
		self.db.commit()

	def shutdown(self):
		print("shutting down")

if __name__ == "__main__":
	if "--help" in sys.argv:
		print("Jambot Modular IRC Bot. Usage:")
		print(" jambot.py [config file]")
		print("Defaults to jambot.cfg")
		sys.exit(0)
	if len(sys.argv) > 1:
		config_file = sys.argv[1]
	bot = botMain()
	try:
		bot.initialize()
	except KeyboardInterrupt as e:
		bot.shutdown()
	except SystemExit as e:
		bot.shutdown()
	except:
		traceback.print_exc()
	bot.shutdown()