import discord
import json
import re

class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

    async def on_message(self, message):
        # Ignore messages not directed at the bot.
        if not self.user.mentioned_in(message):
            return

        async with message.channel.typing():
            # Drop all refs in the message.
            command = re.sub(r"<..\d+>", "", message.content.lower()).split()
            if not command:
                return

            role_name = ' '.join([word.capitalize() for word in command[1:]])
            channel_name = '-'.join(command[1:])

            if command[0] in ["join"]:
                self._assign_role(role_name, message)
            elif command[0] in ["remove", "leave"]:
                self._remove_role(role_name, message)
            elif command[0] in ["register", "add"]:
                self._add_game(role_name, channel_name, message)
            elif command[0] in ["games", "list"]:
                self._list_games(message)
            elif command[0] in ["help"]:
                self._help(message)
            else:
                # TODO: send error message
                pass

    async def _assign_role(self, role_name, message):
        pass

    async def _remove_role(self, role_name, message):
        pass

    async def _add_game(self, role_name, channel_name, message):
        pass

    async def _list_games(self, message):
        pass

    async def _help(self, message):
        pass

if __name__ == "__main__":
    with open("auth.json", "r") as auth_file:
        auth = json.load(auth_file)
    bot = RolyPoly()
    bot.run(auth["discord-token"])
