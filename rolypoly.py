import discord
import json
import re

class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

    async def on_message(self, message):
        if not self.user.mentioned_in(message):
            return
        # drop all refs in the message
        command = re.sub(r"<..\d+>", "", message.content).strip()
        

if __name__ == "__main__":
    with open("auth.json", "r") as auth_file:
        auth = json.load(auth_file)
    bot = RolyPoly()
    bot.run(auth["discord-token"])
