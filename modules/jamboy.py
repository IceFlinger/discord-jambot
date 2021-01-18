from botmodule import botmodule 
import discord
import pyboy
import logging
import asyncio
import io
from PIL import Image, ImageOps

buttons = {
	"up": (pyboy.WindowEvent.PRESS_ARROW_UP, pyboy.WindowEvent.RELEASE_ARROW_UP),
	"down": (pyboy.WindowEvent.PRESS_ARROW_DOWN, pyboy.WindowEvent.RELEASE_ARROW_DOWN),
	"right": (pyboy.WindowEvent.PRESS_ARROW_RIGHT, pyboy.WindowEvent.RELEASE_ARROW_RIGHT),
	"left": (pyboy.WindowEvent.PRESS_ARROW_LEFT, pyboy.WindowEvent.RELEASE_ARROW_LEFT),
	"a": (pyboy.WindowEvent.PRESS_BUTTON_A, pyboy.WindowEvent.RELEASE_BUTTON_A),
	"b": (pyboy.WindowEvent.PRESS_BUTTON_B, pyboy.WindowEvent.RELEASE_BUTTON_B),
	"start": (pyboy.WindowEvent.PRESS_BUTTON_START, pyboy.WindowEvent.RELEASE_BUTTON_START),
	"select": (pyboy.WindowEvent.PRESS_BUTTON_SELECT, pyboy.WindowEvent.RELEASE_BUTTON_SELECT)
}

button_map_words = {
	**buttons,
	"Up": buttons["up"],
	"Down": buttons["down"],
	"Right": buttons["right"],
	"Left": buttons["left"],
	"A": buttons["a"],
	"B": buttons["b"],
	"Start": buttons["start"],
	"Select": buttons["select"],
	"u": buttons["up"],
	"d": buttons["down"],
	"r": buttons["right"],
	"l": buttons["left"],
	"U": buttons["up"],
	"D": buttons["down"],
	"R": buttons["right"],
	"L": buttons["left"]
}

class moduleClass(botmodule):
	def default_config(self):
		return {"romname": "red.gb",
			"frame_file": "frame.png",
			"save_state": "game.state",
			"button_press_ticks": 4,
			"blend": 0.4,
			"color": '#779679',
			"input_frame_delay": 0.3}

	async def on_ready(self, client, config):
		self.emu = pyboy.PyBoy(config["romname"])
		self.emu.set_emulation_speed(0)
		self.sending_frame = False
		self.frame_timer = 0
		try:
			save_state = open(config["save_state"], "rb")
			self.emu.load_state(save_state)
			save_state.close()
		except:
			save_state = open(config["save_state"], "x")
			save_state.close()
		await self.emu_tick(client, config)

	async def emu_tick(self, client, config):
		self.emu.tick()
		loop = asyncio.get_running_loop()
		asyncio.run_coroutine_threadsafe(self.emu_tick(client, config), loop)

	async def send_frame(self, client, config, channel):
		if not self.sending_frame:
			self.sending_frame = True
			async with channel.typing():
				while self.frame_timer > 0:
					await asyncio.sleep(0.1)
					self.frame_timer = self.frame_timer - 0.1
				frame_raw = self.emu.botsupport_manager().screen().screen_image()
				color = Image.new('RGB', frame_raw.size, config["color"])
				frame_raw = Image.blend(frame_raw, color, config["blend"])
				width, height = frame_raw.size
				frame_raw = frame_raw.resize((width*2,height*2), Image.NEAREST)
				frame_raw.save(config["frame_file"], "PNG")
				await channel.send(file=discord.File(config["frame_file"]))
				save_state = open(config["save_state"], "wb")
				self.emu.save_state(save_state)
				save_state.close()
			self.sending_frame = False

	async def send_game_input(self, client, config, button, channel, amount):
		for i in range(0, amount):
			self.emu.send_input(button[0])
			for i in range(0, config["button_press_ticks"]):
				self.emu.tick()
			self.emu.send_input(button[1])
			self.frame_timer = config["input_frame_delay"]
			if amount > 1:
				await asyncio.sleep(0.1)
		await self.send_frame(client, config, channel)

	async def on_message(self, client, config, message):
		if message.content == "f":
			self.frame_timer = 0.1
			await self.send_frame(client, config, message.channel)
		if (message.content in button_map_words):
			await self.send_game_input(client, config, button_map_words[message.content], message.channel, 1)
		elif (message.content[:len(message.content)-1] in button_map_words):
			try:
				await self.send_game_input(client, config, button_map_words[message.content[:len(message.content)-1]], message.channel, int(message.content[-1]))
			except ValueError:
				pass
