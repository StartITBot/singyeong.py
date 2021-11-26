import time
import traceback
import singyeong

client = singyeong.Client("singyeong://receiver@localhost:4000")


@client.event
async def on_raw_packet(message: singyeong.Message):
    payload = message.payload
    took_ms = (time.time() - payload['foo']) * 1000
    print("Pong! Latency:", int(took_ms), "ms")


@client.event
def on_error(exc):
    traceback.print_exc()


client.run()
