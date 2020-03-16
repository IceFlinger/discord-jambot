from botmodule import botmodule 
import asyncio
import requests
import logging
from datetime import datetime
from datetime import timezone
import io
import hashlib
from PIL import Image, ImageOps

def download_image(url):
	r = requests.get(url, stream=True)
	size = 0
	ctt = io.BytesIO()
	for chunk in r.iter_content(2048):
		size += len(chunk)
		ctt.write(chunk)
	return ctt.getvalue()

def next_times(config):
	params = {'lat': config["lat"], 'lng': config["long"], 'formatted': 0}
	today = requests.get(config["api"], params=params)
	params['date'] = "tomorrow"
	tomorrow = requests.get(config["api"], params=params)
	now = datetime.now(timezone.utc)
	dformat = "%Y-%m-%dT%H:%M:%S%z"
	nextrise = datetime.strptime(today.json()["results"]["sunrise"], dformat)
	if (nextrise < now):
		nextrise = datetime.strptime(tomorrow.json()["results"]["sunrise"], dformat)
	nextset = datetime.strptime(today.json()["results"]["sunset"], dformat)
	if (nextset < now):
		nextset = datetime.strptime(tomorrow.json()["results"]["sunset"], dformat)
	return({"now": now, "sunrise": nextrise, "sunset": nextset})

class moduleClass(botmodule):

	def default_config(self):
		return {"lat": 43.642496,
		"long": -79.387041,
		"api": "https://api.sunrise-sunset.org/json",
		"daytime": "https://picture",
		"nighttime": "https://picture",
		}

	def on_init(self):
		self.logger = logging.getLogger("jambot.suncycle")

	async def on_connect(self, client, config):
		self.pics = {}
		self.pics["sunrise"] = download_image(config["daytime"])
		self.pics["sunset"] = download_image(config["nighttime"])
		times = next_times(config)
		risedelay = (times["sunrise"] - times["now"]).total_seconds()
		setdelay = (times["sunset"] - times["now"]).total_seconds()
		loop = asyncio.get_running_loop()
		asyncio.run_coroutine_threadsafe(self.shift_callback(risedelay, client, config, "sunrise"), loop)
		self.logger.log(20, "sunrise scheduled in " + str(times["sunrise"] - times["now"]) + " at " + str(times["sunrise"]))
		asyncio.run_coroutine_threadsafe(self.shift_callback(setdelay, client, config, "sunset"), loop)
		self.logger.log(20, "sunset scheduled in " + str(times["sunset"] - times["now"]) + " at " + str(times["sunset"]))

	async def shift_callback(self, delay, client, config, dtype):
		await asyncio.sleep(delay)
		await self.shift_picture(client, config, self.pics[dtype])
		self.logger.log(20, "switched to " + dtype)
		await asyncio.sleep(10)
		times = next_times(config)
		loop = asyncio.get_running_loop()
		mydelay = (times[dtype] - times["now"]).total_seconds()
		asyncio.run_coroutine_threadsafe(self.shift_callback(mydelay, client, config, dtype), loop)
		self.logger.log(20, "scheduled next " + dtype + " in " + str(times[dtype] - times["now"]) + " at " + str(times[dtype]))

	async def shift_picture(self, client, config, image):
		server = client.get_guild(self.server)
		await server.edit(icon=image)