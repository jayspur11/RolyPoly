import discord
import json
import re

class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

    async def on_message(self, message):
        if not self.user.mentioned_in(message):
            return
        async with message.channel.typing():
            # drop all refs in the message
            command = re.sub(r"<..\d+>", "", message.content).split()
            role_name = ' '.join([word.capitalize() for word in command[1:]])
            channel_name = '-'.join([word.lower() for word in command[1:]])
            if "join" == command[0]:
                # TODO: find the appropriate role and assign it
                pass
            elif "register" == command[0]:
                # TODO: create a new group & role, if it doesn't already exist
                pass
            else:
                # TODO: send an error message
                pass

if __name__ == "__main__":
    with open("auth.json", "r") as auth_file:
        auth = json.load(auth_file)
    bot = RolyPoly()
    bot.run(auth["discord-token"])
