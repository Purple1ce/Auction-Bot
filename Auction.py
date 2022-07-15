from Bidder import Bidder
from datetime import datetime

def is_float(n):
    try:
        float(n)
    except ValueError:
        return False
    return True


class Auction:
    def __init__(self, channel):
        self.participants = []
        self.minimum_increment = 0.2
        self.running = False
        self.open = False
        self.timeleft = 0
        self.channel = channel
        self.bidder = [Bidder("Starting Bid", 0, 0)]
        self.repair_cost = 0
        self.messages = []
        self.date = 0

    def get_highest_bidder(self):
        return self.bidder[len(self.bidder)-1].user

    def get_highest_bid(self):
        return self.bidder[len(self.bidder) - 1].bid

    async def check_timeleft(self, message):
        substring = message.content.replace("!set time", "")
        substring = substring.replace(" ", "")
        if not substring.isnumeric():
            await message.channel.send("Auction time needs to be a number!", delete_after=10)
        else:
            await self.set_timeleft(int(substring) * 60)

            await message.channel.send("Auction time was set to " + substring + "h.")

    async def set_timeleft(self, num):
        if num <= 0:
            await self.end()
            self.timeleft = 0
        else:
            self.timeleft = num

    async def get_timeleft(self, message):
        hours = self.timeleft // 60
        minutes = self.timeleft % 60
        await message.channel.send(f"{message.author.mention}, "
                                   f"time left on the auction is : {hours}h and {minutes}m")

    async def get_participants(self):
        names = []
        for p in self.participants:
            names.append(p.name)
        await self.channel.send("Participants are: "+", ".join(names))

    def start(self, participants, channel):
        self.participants = participants
        self.running = True
        self.open = True
        self.timeleft = 1440
        self.channel = channel
        self.date = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")

    async def check_start(self, message):
        if not message.mentions:
            await message.channel.send("No participant in lootsplit. "
                                       "Please mention participants", delete_after=10)

        elif self.running:
            await message.channel.send(f"An auction is already running, "
                                       f"{message.author.mention}", delete_after=10)
        elif self.open:
            await self.channel.send(f"{message.author.mention}, there is still and auction open!"
                                    f"Please finish and close the current Auction before you can"
                                    f"start a new one.")
        else:
            self.start(message.mentions, message.channel)
            await message.channel.send("An auction has been started.")
            if not self.bidder[0].bid == 0:
                await message.channel.send(f" starting bid is: {self.get_highest_bid()}"
                                           f" million silver")
            await message.channel.send(f" Minimum increment is: {self.minimum_increment}"
                                       f"million silver")

    async def set_starting_bid(self, message):
        substring = message.content.replace("!starting bid", "")
        substring = substring.replace(" ", "")
        if not is_float(substring):
            await message.channel.send(f"{message.author.mention}"
                                       f"The starting bid needs to be a number!",delete_after=10)
        else:
            await message.channel.send(f"The starting bid was set to {substring}!")
            num = round(float(substring))
            self.bidder[0].bid = num

    async def set_minimum_increment(self, message):
        substring = message.content.replace("!minimum increment", "")
        substring = substring.replace(" ", "")
        if not is_float(substring):
            await message.channel.send(f"{message.author.mention}"
                                       f"The minimum Bid needs to be a number!",delete_after=10)
        else:
            await message.channel.send(f"The minimum increment was set to {substring}!")
            self.minimum_increment = round(float(substring), 1)

    async def add_repaircost(self, message):
        substring = message.content.replace("!add repaircost", "")
        substring = substring.replace(" ", "").replace(".", "").replace(",", "")
        if not substring.isnumeric():
            await message.channel.send(f"{message.author.mention}"
                                       f"The minimum Bid needs to be a number!", delete_after=10)
        else:
            num = int(substring)
            self.repair_cost += num
            await message.channel.send(f"{num:,} has been added to the repair costs!")
            await message.channel.send(f"The total repair cost now is: {self.repair_cost:,}")

    async def delete_last_bid(self):
        last = len(self.bidder)
        if last > 1:
            bid = self.bidder[last-1]
            print(bid.message)
            await bid.message.delete()
            await self.channel.send(f"{bid.user.mention}, The last bid has been deleted",
                                    delete_after=360)
            self.bidder.pop(-1)
        else:
            await self.channel.send("There is no bid to delete", delete_after=10)

    async def bid(self, message):
        substring = message.content.replace("bid", "")
        substring = substring.replace(" ", "")
        if not is_float(substring):
            await message.channel.send(
                f"{message.author.mention}Your bid needs to be a number and not {substring}!",
                delete_after=10)
        else:
            num = round(float(substring), 1)
            if num < (self.get_highest_bid() + self.minimum_increment):
                await message.channel.send(f"{message.author.mention} your bid needs to be"
                                           f" {self.minimum_increment} higher than"
                                           f" {self.get_highest_bid()}.", delete_after=10)
            else:
                bid_author = message.author
                message = await message.channel.send(f"{message.author.mention} "
                                                     f"you bid on the Auction: "
                                                     f"{num} million silver.")
                self.bidder.append(Bidder(bid_author, num, message))

    async def close(self, category, log_channel_substr):
        log_channel = 0
        for channel in category.channels:
            if log_channel_substr in channel.name:
                log_channel = channel

        log_message = "___________________________\n"
        log_message += f"Auction from {self.date}"
        if not log_channel == 0:
            for message in self.messages:
                if len(log_message)+len(message.content) >= 2000:
                    await log_channel.send(log_message)
                    log_message = ""
                else:
                    log_message += "\n"+message.content

        log_message += "___________________________"
        await log_channel.send(log_message)

        self.bidder = [Bidder("Starting Bid", 0, 0)]
        self.repair_cost = 0
        self.messages = []
        self.open = False

    async def add_participant(self, message):
        if not message.mentions:
            await message.channel.send("No participant mentioned. "
                                       "Please mention participants", delete_after=10)

        elif any(p in message.mentions for p in self.participants):
                await message.channel.send("Participant already exists.")
        else:
            names = []
            for m in message.mentions:
                names.append(m.name)
            names = ", ".join(names)

            await message.channel.send(f"{names} have been added to the split.")
            self.participants.extend(message.mentions)

    async def end(self):
        self.running = False
        await self.channel.send("Auction is over!")
        if self.get_highest_bidder() == "Starting Bid":
            await self.channel.send("No bid was done. No one won the Auction.")
        else:
            await self.channel.send(f"{self.get_highest_bidder().mention} has won the auction"
                                    f" with a bid of {self.get_highest_bid()} Million Silver.")
