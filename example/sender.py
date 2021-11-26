import asyncio
import time
import traceback
import singyeong

client = singyeong.Client("singyeong://sender@localhost:4000")


@client.event
async def on_ready():
    while True:
        await client.broadcast(singyeong.Target(application="receiver"), {
            "foo": time.time()
        })
        print("Ping!")
        await asyncio.sleep(3)


@client.event
def on_error(exc):
    traceback.print_exc()


client.run()
