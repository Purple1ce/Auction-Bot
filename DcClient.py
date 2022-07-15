import sys
import traceback

import discord
from Auction import Auction

admin_role = "Auctioneer"
split_name_substr = "loot-split"
log_channel_substr = "auction-log"

auctions = {}


def get_auction(message):
    number = message.channel.name[len(message.channel.name)-1]
    if not number.isnumeric():
        number = 1
    return auctions[int(number) - 1]


async def check_auction_over():
    for a in auctions.values():
        if a.running:
            await a.set_timeleft(a.timeleft-60)


class DcClient(discord.Client):

    def get_log_channel(self, guild):
        for channel in guild.channels:
            if log_channel_substr in channel.name:
                return channel
            else:
                return 0

    async def on_ready(self):
        print("made it here")
        await self.check_for_channel()

    async def on_message(self, message):
        try:
            if split_name_substr in message.channel.name:
                await self.process_message(message)
        except Exception as e:
            log_channel = self.get_log_channel(message.channel.guild)
            if log_channel != 0:
                await log_channel.send(traceback.format_exception(*sys.exc_info()))
            else:
                await message.channel.guild.owner.send("No Log Channel, so here is the Error")
                await message.channel.guild.owner.send(traceback.format_exception(*sys.exc_info()))

    async def check_for_channel(self):
        for server in self.guilds:
            for channel in server.channels:
                print(server.name + ", " + channel.name + ", " + str(channel.id))
                if split_name_substr in channel.name:
                    auctions[channel.id] = Auction(channel)

        print(auctions)

    async def process_message(self, message):
        auction = auctions[message.channel.id]

        auction.messages.append(message)

        if message.author == self.user:
            return

        if message.content.startswith("!starting bid "):
            if any(roles.name == admin_role for roles in message.author.roles):
                await auction.set_starting_bid(message)

        elif message.content.startswith("!minimum increment "):
            if any(roles.name == admin_role for roles in message.author.roles):
                await auction.set_minimum_increment(message)

        elif message.content.startswith("!start auction "):
            if any(roles.name == admin_role for roles in message.author.roles):
                await auction.check_start(message)

        elif message.content.startswith("!set time "):
            if any(roles.name == admin_role for roles in message.author.roles):
                await auction.check_timeleft(message)

        elif message.content == "!delete last":
            if any(roles.name == admin_role for roles in message.author.roles):
                if auction.open:
                    await auction.delete_last_bid()

        elif message.content.startswith("!add repaircost "):
            if any(roles.name == admin_role for roles in message.author.roles):
                await auction.add_repaircost(message)

        elif message.content.startswith("!close auction "):
            if any(roles.name == admin_role for roles in message.author.roles):
                if not auction.running:
                    await auction.close(message.channel.category, log_channel_substr)
                    await message.channel.purge()
                    await message.channel.send("The auction has been closed", delete_after=10)
                    return
                else:
                    await message.channel.send("The auction is still running!", delete_after=10)

        elif message.content == "!end auction!":
            if any(roles.name == admin_role for roles in message.author.roles):
                if not auction.running:
                    await message.channel.send("There is no auction running!", delete_after=10)
                else:
                    await auction.end()

        elif message.content.startswith("bid "):
            if not auction.running:
                await message.channel.send("There is no auction running!", delete_after=10)
            else:
                await auction.bid(message)

        elif message.content == "time left":
            if not auction.running:
                await message.channel.send("There is no auction running!", delete_after=10)
            else:
                await auction.get_timeleft(message)

        elif message.content == "!who":
            if not auction.open:
                await message.channel.send("There is no auction open!", delete_after=10)
            else:
                await auction.get_participants()

        elif message.content.startswith("!add participant "):
            if auction.open:
                await auction.add_participant(message)

        elif message.content.startswith("!add silverbags "):
            if auction.open:
                await auction.add_silverbags(message)

        elif message.content == "value":
            if auction.open:
                await auction.print_auction_value()

        else:
            if len(message.attachments) == 0:
                await message.channel.send(f"{message.author.mention}Wrong Command!", delete_after=10)

        if not len(message.attachments) == 0:
            if not auction.running:
                if not any(roles.name == admin_role for roles in message.author.roles):
                    await message.delete()
            else:
                await message.delete()
        else:
            await message.delete()


