from botmodule import botmodule 
import logging
import inspect

class moduleClass(botmodule):

	def default_config(self):
		return {"level": 10,
				"raw_level": 10,
				"message_level": 20
		}

	def on_init(self):
		self.logger = logging.getLogger("jambot.monitor")

	async def context_string(self, client):
		server = client.get_guild(self.server)
		channel = client.get_channel(self.channel)
		if server is not None:
			if server.name is not None: # ????
				server = str(server.name)
			else:
				server = str(self.server)
		else:
			server = str(self.server)
		if channel is not None:
			channel  = str(channel.name)
		else:
			channel = str(self.channel)
		return self.context + "/" + server + "/" + channel

# Channel-context calls
# Called by the most specifically context module for any given loaded module type (sandboxed)

	async def on_typing(self, client, config, channel, user, when):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])
		try:
			serv = str(channel.guild.name)
		except:
			serv = ""
		try:
			chan = str(channel.name)
		except AttributeError:
			chan = str(channel.me.name)
		try:
			nick = user.nick
		except:
			nick = user.name
		self.logger.log(config["message_level"], serv + "/" + chan + " " + nick + " typing at: " +  str(when))

	async def on_message(self, client, config, message):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])
		try:
			serv = str(message.channel.guild.name)
		except:
			serv = ""
		try:
			chan = str(message.channel.name)
		except AttributeError:
			chan = str(message.channel.me.name)
		try:
			nick = message.author.nick
		except:
			nick = message.author.name
		self.logger.log(config["message_level"], serv + "/" + chan + " " + nick + ": " +  message.clean_content)

	async def on_message_delete(self, client, config, message):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_message_edit(self, client, config, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_reaction_add(self, client, config, reaction, user):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_reaction_remove(self, client, config, reaction, user):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_reaction_clear(self, client, config, message, reactions):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_private_channel_delete(self, client, config, channel):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_private_channel_create(self, client, config, channel):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])
		self.logger.log(config["level"], str(channel) + ": " +  inspect.stack()[0][3])

	async def on_private_channel_update(self, client, config, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_private_channel_pins_update(self, client, config, channel, last_pin):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_channel_delete(self, client, config, channel):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_channel_create(self, client, config, channel):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_channel_update(self, client, config, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_channel_pins_update(self, client, config, channel, last_pin):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_webhooks_update(self, client, config, channel):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])


# All instance calls
# Called by every loaded instance

	async def on_connect(self, client, config):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_ready(self, client, config):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_shard_ready(self, client, config, shard_id):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_resumed(self, client, config):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_error(self, client, config, event, *args, **kwargs):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])


# Global only calls
# Only called in global context

	async def on_socket_raw_receive(self, client, config, msg):
		self.logger.log(config["raw_level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])
		self.logger.log(config["raw_level"], str(msg))

	async def on_socket_raw_send(self, client, config, payload):
		self.logger.log(config["raw_level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])
		self.logger.log(config["raw_level"], str(payload))

	async def on_raw_message_delete(self, client, config, payload):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_raw_bulk_message_delete(self, client, config, payload):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_raw_message_edit(self, client, config, payload):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_raw_reaction_add(self, client, config, payload):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_raw_reaction_remove(self, client, config, payload):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_raw_reaction_clear(self, client, config, payload):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])


# Server-level calls
# Called by every module loaded into any context relevant to triggering server

	async def on_guild_join(self, client, config, guild):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_remove(self, client, config, guild):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_update(self, client, config, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_role_create(self, client, config, role):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_role_delete(self, client, config, role):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_role_update(self, client, config, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_emojis_update(self, client, config, guild, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_available(self, client, config, guild):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_guild_unavailable(self, client, config, guild):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_voice_state_update(self, client, config, member, before, after):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_member_ban(self, client, config, guild, user):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])

	async def on_member_unban(self, client, config, guild, user):
		self.logger.log(config["level"], await self.context_string(client) + ": " +  inspect.stack()[0][3])