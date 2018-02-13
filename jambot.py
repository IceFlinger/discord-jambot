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
	def set(self, setting, value):
		try:
			message = (self.name, "SET", setting, value)
			self.send.put(message)
			self.send.join()
			return True
		except:
			print("Couldn't set " + self.name + " setting " + setting + " to " + str(value))
			return False

	def get(self, setting):
		try:
			message = (self.name, "GET", "")
			self.send.put(message)
			self.send.join()
			value = self.recv.get()
			self.recv.task_done()
			return value
		except:
			print("Couldn't get " + self.name + " setting " + setting)
			return None

	def init_settings(self):
		pass

	def bind_events(self):
		pass

	def __init__(self, name, bot, send, recv):
		self.name = name
		self.bot = bot
		self.send = send
		self.recv = recv
		self.event_loop = asyncio.new_event_loop()
		self.c = discord.Client(loop=self.event_loop)
		self.init_settings()
		self.bind_events()

class botMain():
	def set(self, setting, value, module="jambot"):
		self.settings[module][setting] = value

	def get(self, setting, module="jambot"):
		return self.settings[module][setting]

	def _spawn_module_thread(self, module, moduleClass, send, recv):
		return moduleClass(module, self, send, recv)

	def _load_modules(self):
		for module in self.get("modules"):
			moduleClass = getattr(importlib.import_module("modules." + module), 'moduleClass')
			new_queue = Queue()
			newmodule = threading.Thread(target=self._spawn_module_thread(module, moduleClass, self.recv_queue, new_queue))
			self.modules.append(newmodule)
			self.send_queues[module] = new_queue
			newmodule.start()
			print("Loaded " + module)

	def _save_config(self):
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
		self.set("modules", self.config["jambot"]["modules"].split())
		self.set("database", self.config["jambot"]["database"])
		self.set("command_prefix", self.config["jambot"]["command_prefix"][0])
		self.set("version", self.config["jambot"]["version"])
		self.set("token", self.config["jambot"]["token"])
		self.set("owner", self.config["jambot"]["owner"])
		self.recv_queue = Queue()
		self.send_queues = {}
		self._load_modules()
		self.c = discord.Client()

		@self.c.event
		async def on_ready():
			print('Logged in as ' + self.c.user.name + " " + self.c.user.id)
			print('------')
		@self.c.event
		async def on_message(message):
			cmd = self.is_command(message)
			print(cmd)
			if cmd:
				command = cmd["command"]
				admin = cmd["admin"]
				args = cmd["args"]
				if command == "save" and admin:
					self._save_config()
					await self.c.send_message(message.channel, "Saved new config to " + config_file)
				elif command == "set" and args:
					if len(args) >= 3 and admin:
						qmodule = args[0]
						qsetting = args[1]
						qvalue = " ".join(args[2:])
						message = (qmodule, "GET", qsetting)
						self.recv.put(message)
						self.recv.join()
						message = (qmodule, "SET", qsetting, qvalue)
						self.recv.put(message)
						self.recv.join()
						await self.client.send_message(message.channel, qmodule + " setting " + qsetting + " changed from " + str(oldvalue) + " to " + str(qvalue))
					except:
						await self.c.send_message(message.channel, "Couldn't set " + self.name + " setting " + setting + " to " + str(value))

if __name__ == "__main__":
	if "--help" in sys.argv:
		print("Jambot Modular Discord Bot. Usage:")
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