import discord
import json

class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

if __name__ == "__main__":
    with open("auth.json", "r") as auth_file:
        auth = json.load(auth_file)
    bot = RolyPoly()
    bot.run(auth["discord-token"])
