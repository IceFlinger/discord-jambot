from botmodule import botmodule 
import requests
from lxml import html
import random
import time
import hashlib

class moduleClass(botmodule):

	def default_config(self):
		return {"downloads": [{"command": "example", 
		"cache": True,
		 "web_folder": "https://example.com/images/"}],
		"uploads": [{"local_folder": "/srv/www/images",
		"command": "example", 
		"raw_folder": "/backup/unconverted",
		"max_filesize": 4000000,
		"resize": False,
		"resize_w": 500,
		"resize_h": 192,
		"resize_tolerence": 0.8}]
		}

	async def on_ready(self, client, config):
		self.cached = {}
		self.cached_list = {}
		for download in config["downloads"]:	
			self.cached[download["command"]] = False
			self.cached_list[download["command"]] = []

	def upload_flag(self, client, config, message):
		cmd = await client.get_cmd(message)
		key = cmd["cmd"]
		self.cached[key] = False
		try:
			urls = []
			if len(message.embeds) > 0:
				for link in message.embeds:
					urls.append(link.url)
			
			r = requests.get(url, stream=True)
			size = 0
			ctt = io.BytesIO()
			for chunk in r.iter_content(2048):
				size += len(chunk)
				ctt.write(chunk)
				if size > self.get("max_filesize"):
					r.close()
					self.send(e.target, "That file is too big")
					raise
			content = ctt.getvalue()
			img_in = Image.open(io.BytesIO(content))
			hash = hashlib.md5()
			hash.update(content)
			i = hash.hexdigest()
			if img_in.format == "GIF" and not self.get("resize"):
				img_in.save(self.get("local_folder") + i + '.gif', 'GIF', save_all=True, optimize=False)
				self.send(e.target, self.get("web_folder") + i + ".gif")
			else:
				img_size = img_in.size
				if img_size[0] < img_size[1] and self.get("orent_check") == "long":
					self.output("That image isn't long", ("", source, target, c, e))
					raise
				elif img_size[0] > img_size[1] and self.get("orent_check") == "tall":
					self.output("That image isn't tall", ("", source, target, c, e))
					raise
				if self.get("save_unconverted"):
					img_in.save(self.get("unconverted_folder") + i + '.png', 'PNG')
				img_out = img_in
				if self.get("resize"):
					x = self.get("resize_width")
					y = self.get("resize_height")
					if self.get("border"):
						border = self.get("border_size")
						img_out = img_in.resize((x-(border*2),y-(border*2)), Image.ANTIALIAS)
						img_out = ImageOps.expand(img_out,border=border,fill='black')
					else:
						img_out = img_in.resize((x,y), Image.ANTIALIAS)
				img_out.save(self.get("local_folder") + i + '.png', 'PNG')
				self.send(e.target, self.get("web_folder") + i + ".png")
			if self.get("flag_logfile") != "":
				dump = open(self.get("flag_logfile"), "a")
				dump.write(str(time.time()) + "\t" + e.source.nick + "\t" + i + "\n")
				dump.close()
			return True
		except:
			self.send(e.target, "Problem flagging that")
			if debug:
				raise
			else:
				pass
		return False

	async def on_message(self, client, config, message):
		cmd = await client.get_cmd(message)
		uploaded = False
		if cmd:
			if config["uploads"] != None:
				for upload in config["uploads"]:
					if cmd["cmd"] == upload["command"]:
						async with message.channel.typing():
							uploaded = self.upload_flag(client, config, message)
							if uploaded:
								url = False
								for download in config["downloads"]:
									if upload["command"] == download["command"]:
										url = download["web_folder"] + uploaded
								if url:
									await message.channel.send(url)
								else:
									await message.channel.send("Uploaded")
			if not uploaded:
				for download in config["downloads"]:
					if cmd["cmd"] == download["command"]:
						async with message.channel.typing():
							if (not self.cached[download["command"]]) or (not download["cache"]):
								r = requests.get(download["web_folder"])
								d = html.fromstring(r.content)
								imglist = d.xpath('//a[@href]/@href')
								imglist = imglist[5:] #first 4 links are random index shit, lazy way to skip (add check for image extension)
								self.cached_list[download["command"]] = imglist
								self.cached[download["command"]] = True
							else:
								imglist  = self.cached_list[download["command"]] 
							imgid = random.randint(0,len(imglist)-1)
						await message.channel.send(download["web_folder"] + imglist[imgid])