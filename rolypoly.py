import discord
import json
import random
import re


_CATALOG_CHANNEL_NAME = "game-catalog"


async def build_new_group(guild, role_name, creation_reason, cat_name,
                          channel_name, author):
    new_role = await guild.create_role(name=role_name,
                                       colour=discord.Colour.from_rgb(
                                           random.randint(0, 255),
                                           random.randint(0, 255),
                                           random.randint(0, 255)),
                                       mentionable=True,
                                       reason=creation_reason)

    new_cat = await guild.create_category(
        name=cat_name,
        overwrites={
            new_role:
            discord.PermissionOverwrite(read_messages=True,
                                        send_messages=True,
                                        embed_links=True,
                                        attach_files=True,
                                        read_message_history=True,
                                        mention_everyone=True,
                                        external_emojis=True,
                                        add_reactions=True,
                                        connect=True,
                                        speak=True,
                                        stream=True,
                                        use_voice_activation=True),
            guild.default_role:
            discord.PermissionOverwrite(read_messages=False)
        },
        reason=creation_reason)

    await guild.create_text_channel(name=channel_name, category=new_cat)
    await guild.create_voice_channel(name=cat_name, category=new_cat)
    await author.add_roles(new_role)
    catalog_channel = await get_catalog_channel(guild)
    new_game_message = await catalog_channel.send(cat_name)
    await new_game_message.add_reaction("❤")


async def get_catalog_channel(guild):
    for channel in guild.channels:
        if channel.name == _CATALOG_CHANNEL_NAME and not channel.category:
            return channel
    return await guild.create_text_channel(name=_CATALOG_CHANNEL_NAME,
                                           overwrites={
                                               guild.default_role:
                                               discord.PermissionOverwrite(
                                                   read_messages=True,
                                                   send_messages=False)
                                           })


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
            else:
                await self._help(message)

    async def on_raw_reaction_add(self, payload):
        channel = self.get_channel(payload.channel_id)
        if (channel.name != _CATALOG_CHANNEL_NAME
                or payload.event_type != "REACTION_ADD"):
            return

        message = await channel.fetch_message(payload.message_id)
        if message.author != self.user:
            return

        role = self._get_role_with_name(
            message.guild, self._role_for_category(message.content))
        await payload.member.add_roles(role)

    async def _remove_role(self, cat_name, message):
        existing_role = self._get_role_with_name(
            message.guild, self._role_for_category(cat_name))
        if existing_role:
            await message.author.remove_roles(existing_role)
            await message.add_reaction("👋")
        else:
            await message.channel.send("Could not find that role.")

    async def _add_game(self, cat_name, channel_name, message):
        creation_reason = "New game requested by {}".format(
            message.author.name)
        role_name = self._role_for_category(cat_name)
        existing_role = self._get_role_with_name(message.guild, role_name)
        if existing_role:
            await message.author.add_roles(existing_role)
        else:
            await build_new_group(message.guild, role_name, creation_reason,
                                  cat_name, channel_name, message.author)

        await message.add_reaction("🙌")

    async def _list_games(self, message):
        games = []
        for role in message.guild.roles:
            if role.name[-1] == u"\u200B":
                games.append(role.name[:-1])
        games.sort()

        if not games:
            await message.channel.send(
                "No games have been added to this server yet!")
        else:
            await message.channel.send(
                "Here are the games I know about:\n\n{}".format(
                    '\n'.join(games)))

    async def _help(self, message):
        await message.channel.send(
            "Here are the things you can ask me to do:\n"
            "`join Game Name` -- join the group for *Game Name*, gaining access"
            " to its channels.\n"
            "`leave Game Name` -- leave the group for *Game Name*, hiding the"
            " channels from your view.\n"
            "`list` -- show the games that other people have joined on this"
            " server. You don't have to stick to this list! If you ask for a"
            " game that's not here, I'll set up a new group for you.")

    def _get_role_with_name(self, guild, role_name):
        for role in guild.roles:
            if role.name == role_name:
                return role
        return None

    def _role_for_category(self, cat_name):
        # The actual role has a nonprinting character at the end, so we can
        # identify which roles we've added just through the roles list.
        return cat_name + u"\u200B"


if __name__ == "__main__":
    with open("auth.json", "r") as auth_file:
        auth = json.load(auth_file)
    bot = RolyPoly()
    bot.run(auth["discord-token"])
