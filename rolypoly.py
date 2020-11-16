import discord
import json
import random
import re


_CATALOG_CHANNEL_NAME = "game-catalog"


async def add_to_catalog(game, catalog):
    new_game_message = await catalog.send(game)
    await new_game_message.add_reaction("❤")


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
    await add_to_catalog(cat_name, catalog_channel)


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


def get_games(guild):
    games = []
    for role in guild.roles:
        if role.name[-1] == u"\u200B":
            games.append(role.name[:-1])
    return games


async def update_games(guild):
    catalog = await get_catalog_channel(guild)
    existing_games = set()
    async for message in catalog.history():
        existing_games.add(message.content)
    for game in get_games(guild):
        if game not in existing_games:
            await add_to_catalog(game, catalog)


def get_text_channel_for_game(guild, cat_name, channel_name):
    for category in guild.categories:
        if category.name == cat_name:
            for text_channel in category.text_channels:
                if text_channel.name == channel_name:
                    return text_channel


class RolyPoly(discord.Client):
    async def on_ready(self):
        print("RolyPoly reporting for duty!")

    async def on_message(self, message):
        # Ignore messages not directed at the bot.
        if not self.user in message.mentions:
            return

        with message.channel.typing():
            # Drop all refs in the message.
            command = re.sub(r"<..\d+>", "", message.content.lower()).split()
            if not command:
                return

            cat_name = ' '.join([word.capitalize() for word in command[1:]])
            channel_name = '-'.join(command[1:])

            if message.author == message.guild.owner:
                # Owner-only commands
                if command[0] == "delete":
                    await self._delete_game(message)
                    return
                elif command[0] == "update":
                    await update_games(message.guild)
                    await message.channel.send("Done!")
                    return

            if command[0] in ["add", "join"]:
                await self._add_game(cat_name, channel_name, message)
            elif command[0] in ["remove", "leave"]:
                await self._remove_role(cat_name, message)
            elif command[0] in ["games", "list"]:
                await self._list_games(message)
            elif command[0] in ["voice"]:
                await self._add_voice(message)
            else:
                await self._help(message)

    async def on_raw_reaction_add(self, payload):
        channel = self.get_channel(payload.channel_id)
        if (channel.name != _CATALOG_CHANNEL_NAME
                or channel.category is not None
                or payload.member == self.user):
            return

        message = await channel.fetch_message(payload.message_id)
        if message.author != self.user:
            return

        role = self._get_role_with_name(
            message.guild, self._role_for_category(message.content))
        if not role:
            return
        await payload.member.add_roles(role)

    async def _add_voice(self, message):
        category = message.channel.category
        if not category:
            await message.channel.send(
                "Please request a new voice channel from the corresponding "
                "text channel."
            )
            return

        new_voice = await message.guild.create_voice_channel(
            name="{category} {number}".format(category=category.name,
                                              number=len(category.channels)),
            category=category)
        await message.channel.send("Created {}!".format(new_voice.name))

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
            if existing_role in message.author.roles:
                await message.delete()
                return
            await message.author.add_roles(existing_role)
        else:
            await build_new_group(message.guild, role_name, creation_reason,
                                  cat_name, channel_name, message.author)

        await get_text_channel_for_game(
            message.guild, cat_name,
            channel_name).send("Welcome, {}!".format(message.author.mention))
        await message.delete()

    async def _delete_game(self, message):
        cat_name = ' '.join(
            [word.capitalize() for word in message.channel.name.split('-')])
        role_name = self._role_for_category(cat_name)
        existing_role = self._get_role_with_name(message.guild, role_name)
        if not existing_role:
            await message.channel.send(
                "Please request deletion from within the group.")
            return

        await existing_role.delete()
        existing_category = message.channel.category
        for channel in existing_category.channels:
            await channel.delete()
        await existing_category.delete()
        catalog = await get_catalog_channel(message.guild)
        await catalog.purge(check=(lambda msg: msg.content == cat_name))

    async def _list_games(self, message):
        games = get_games(message.guild)
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
            " game that's not here, I'll set up a new group for you.\n"
            "`voice` -- add another voice channel for a game. Must be requested"
            " from that game's text channel.")

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
    intents = discord.Intents.none()
    intents.guilds = True
    intents.members = True
    intents.guild_messages = True
    intents.guild_reactions = True
    bot = RolyPoly(intents=intents)
    bot.run(auth["discord-token"])
