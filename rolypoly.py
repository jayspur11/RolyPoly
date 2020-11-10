import discord

class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

if __name__ == "__main__":
    # TODO: Need to pass auth stuff here.
    bot = RolyPoly()
    bot.run()
