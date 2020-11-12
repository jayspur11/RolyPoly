import discord
import json
import random
import re


class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

    async def on_message(self, message):
        # Ignore messages not directed at the bot.
        if not self.user.mentioned_in(message):
            return

        with message.channel.typing():
            # Drop all refs in the message.
            command = re.sub(r"<..\d+>", "", message.content.lower()).split()
            if not command:
                return

            cat_name = ' '.join([word.capitalize() for word in command[1:]])
            channel_name = '-'.join(command[1:])

            if command[0] in ["add", "join"]:
                await self._add_game(cat_name, channel_name, message)
            elif command[0] in ["remove", "leave"]:
                await self._remove_role(cat_name, message)
            elif command[0] in ["games", "list"]:
                await self._list_games(message)
            elif command[0] == "help":
                await self._help(message)
            else:
                # TODO: send error message
                pass

    async def _remove_role(self, cat_name, message):
        existing_role = await self._get_role_with_name(
            message.guild, self._role_for_category(cat_name))
        if existing_role:
            await message.author.remove_roles(existing_role)
            # TODO: add reaction to indicate this is done
        else:
            # TODO: send error message
            pass

    async def _add_game(self, cat_name, channel_name, message):
        creation_reason = "New game requested by {}".format(
            message.author.name)
        role_name = self._role_for_category(cat_name)
        existing_role = await self._get_role_with_name(message.guild,
                                                       role_name)
        if existing_role:
            await message.author.add_roles(existing_role)
        else:
            new_role = await message.guild.create_role(
                name=role_name,
                colour=discord.Colour.from_rgb(random.randint(0, 255),
                                               random.randint(0, 255),
                                               random.randint(0, 255)),
                mentionable=True,
                reason=creation_reason)

            new_category = await message.guild.create_category(
                name=cat_name,
                overwrites={
                    new_role:
                    discord.PermissionOverwrite(read_messages=True),
                    message.guild.default_role:
                    discord.PermissionOverwrite(read_messages=False)
                },
                reason=creation_reason)

            await message.guild.create_text_channel(name=channel_name,
                                                    category=new_category)

            await message.guild.create_voice_channel(name=cat_name,
                                                     category=new_category)

            await message.author.add_roles(new_role)

        # TODO: add reaction to indicate that this is done

    async def _list_games(self, message):
        games = []
        for role in message.guild.roles:
            if role.name[-1] == u"\u200B":
                games.append(role.name[:-1])

        if not games:
            # TODO: send a message about how there are no games
            pass
        else:
            await message.channel.send(
                "Here are the games I know about:\n\n{}".format('\n'.join(games))
            )

    async def _help(self, message):
        pass

    async def _get_role_with_name(self, guild, role_name):
        for role in guild.roles:
            if role.name == role_name:
                return role
        return None

    def _role_for_category(self, cat_name):
        return cat_name + u"\u200B"


if __name__ == "__main__":
    with open("auth.json", "r") as auth_file:
        auth = json.load(auth_file)
    bot = RolyPoly()
    bot.run(auth["discord-token"])
