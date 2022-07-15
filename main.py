import asyncio
from decouple import config
from DcClient import DcClient
from DcClient import check_auction_over

#TODO: Add silver bag
#TODO: Logs for every channel seperate
#TODO: DELETE PARTICIPANTS
#TODO: DELETE REPAIR COSTS
#TODO: WRITE INTO SHEET
#TODO: UPLOAD TO GIT HUB
#TODO: POST TO SERVER
#TODO: CHANGE DISCORD API CONNECTION TO SERVER




async def test():
    while True:
        await check_auction_over()
        await asyncio.sleep(10)

def start():
    TOKEN = config('TOKEN')
    client = DcClient()
    client.loop.create_task(test())
    client.run(TOKEN)

if __name__ == "__main__":
    start()
