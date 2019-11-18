class botmodule():
	def default_config(self):
		return {}

	def on_init(self):
		pass

	def __init__(self, name, context, server = "", channel = ""):
		self.name = name
		self.context = context
		self.server = server
		self.channel = channel
		self.defaults = self.default_config()
		self.on_init()

# Channel-context calls
# Called by the most specifically context module for any given loaded module type (sandboxed)

	async def on_typing(self, client, config,  channel, user, when):
		pass

	async def on_message(self, client, config,  message):
		pass

	async def on_message_delete(self, client, config, message):
		pass

	async def on_message_edit(self, client, config, before, after):
		pass

	async def on_reaction_add(self, client, config, reaction, user):
		pass

	async def on_reaction_remove(self, client, config, reaction, user):
		pass

	async def on_reaction_clear(self, client, config, message, reactions):
		pass

	async def on_private_channel_delete(self, client, config, channel):
		pass

	async def on_private_channel_create(self, client, config, channel):
		pass

	async def on_private_channel_update(self, client, config, before, after):
		pass

	async def on_private_channel_pins_update(self, client, config, channel, last_pin):
		pass

	async def on_guild_channel_delete(self, client, config, channel):
		pass

	async def on_guild_channel_create(self, client, config, channel):
		pass

	async def on_guild_channel_update(self, client, config, before, after):
		pass

	async def on_guild_channel_pins_update(self, client, config, channel, last_pin):
		pass

	async def on_webhooks_update(self, client, config, channel):
		pass


# All instance calls
# Called by every loaded instance

	async def on_connect(self, client, config):
		pass

	async def on_ready(self, client, config):
		pass

	async def on_shard_ready(self, client, config, shard_id):
		pass

	async def on_resumed(self, client, config):
		pass

	async def on_error(self, client, config, event, *args, **kwargs):
		pass


# Global only calls
# Only called in global context

	async def on_socket_raw_receive(self, client, config, msg):
		pass

	async def on_socket_raw_send(self, client, config, payload):
		pass

	async def on_raw_message_delete(self, client, config, payload):
		pass

	async def on_raw_bulk_message_delete(self, client, config, payload):
		pass

	async def on_raw_message_edit(self, client, config, payload):
		pass

	async def on_raw_reaction_add(self, client, config, payload):
		pass

	async def on_raw_reaction_remove(self, client, config, payload):
		pass

	async def on_raw_reaction_clear(self, client, config, payload):
		pass


# Server-level calls
# Called by every module loaded into any context relevant to triggering server

	async def on_guild_join(self, client, config, guild):
		pass

	async def on_guild_remove(self, client, config, guild):
		pass

	async def on_guild_update(self, client, config, before, after):
		pass

	async def on_guild_role_create(self, client, config, role):
		pass

	async def on_guild_role_delete(self, client, config, role):
		pass

	async def on_guild_role_update(self, client, config, before, after):
		pass

	async def on_guild_emojis_update(self, client, config, guild, before, after):
		pass

	async def on_guild_available(self, client, config, guild):
		pass

	async def on_guild_unavailable(self, client, config, guild):
		pass

	async def on_voice_state_update(self, client, config, member, before, after):
		pass

	async def on_member_ban(self, client, config, guild, user):
		pass

	async def on_member_unban(self, client, config, guild, user):
		pass

	async def on_member_update(self, client, config, before, after):
		pass
