from jambot import botModule
import asyncio
import discord
#Small sample module
#self.send(chan, msg):
#self.db_query(statement, params)
#self.db_commit()
class moduleClass(botModule):
	dbload = False #Set this to True if this module uses DB access, so it only gets created/loaded when needed

	def init_settings(self):
		self.set("setting", "test", "private test setting",True)
		self.set("test", "setting", "public test setting", False)

	def bind_events(self):
		@self.c.event
		async def on_message(message):
			command_sent = self.is_command(message)
			print(command_sent)
			if command_sent:
				if command_sent["command"] == 'test':
					counter = 0
					tmp = await self.c.send_message(message.channel, 'Calculating messages...')
					async for log in self.c.logs_from(message.channel, limit=100):
						if log.author == message.author:
							counter += 1
						await self.c.edit_message(tmp, 'You have {} messages.'.format(counter))
				elif command_sent["command"] == 'sleep':
					await asyncio.sleep(5)
					await self.c.send_message(message.channel, 'Done sleeping')