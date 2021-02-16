# 신경.py

An asynchronous client library for [신경](https://github.com/queer/singyeong), a dynamic metadata-oriented service mesh.

## WARNING

If 신경 is alpha quality software, then Singyeong.py is pre-alpha quality software. Expect things to break spectacularly.

## Installing
You can get the library directly from PyPI:
```shell
python3 -m pip install -U singyeong.py
```
If you are using Windows, then the following should be used instead:
```shell
py -3 -m pip install -U singyeong.py
```
### Install with faster json support

```shell
pip install singyeong.py[ujson]
```

### Install with msgpack support

```shell
pip install singyeong.py[msgpack]
```


## Event Reference
This section outlines the different types of events listened by Client.

### How to register event?

There are two ways to register an event, the first way is through the use of Client.event(). 
```python
import singyeong

client = singyeong.Client("singyeong://receiver@localhost:4567")

@client.event
async def on_ready():
    print('Ready!')
```

The second way is through subclassing Client and overriding the specific events. For example:

```python
import singyeong

class SingyeongClient(singyeong.Client):
    async def on_raw_packet(self, message):
        print(message.payload)

client = SingyeongClient("singyeong://receiver@localhost:4567")
```

If an event handler raises an exception, on_error() will be called to handle it, which defaults to print a traceback and ignoring the exception.

### List of available events

#### Client.on_ready()
Called when the 신경 has accepted you, and will send you packets. Usually after login is successful.

#### Client.on_raw_packet(message)
Called when the 신경 has sent to you BROADCAST or SEND event. Example below shows how to get all data from the packet:
```python
import singyeong

client = ...

@client.event
async def on_raw_packet(message: singyeong.Message):
    nonce = message.nonce  # Optional nonce, used by clients for req-res queries
    payload = message.payload  # Whatever data you want to pass
    timestamp = message.timestamp  # Timestamp of the packet when it was sent on the server. Can be used for ex. latency calculations
    event_name = message.event_name  # May be "BROADCAST" or "SEND"
```


#### Client.on_error()
Usually when an event raises an uncaught exception, a traceback is printed to stderr and the exception is ignored.
```python
import traceback

def on_error(exc):
    traceback.print_exc()
```
If you want to change this behaviour and handle the exception for whatever reason yourself, this event can be overridden. Which, when done, will suppress the default action of printing the traceback.

## Sending data

```python
import singyeong

client = ...

async def func():
    target = singyeong.Target(
        application="application id here",
        restricted=True,
        key="1234567890",
        droppable=True,
        optional=True,
        selector=singyeong.Minimum("key"),
        operators=[
            singyeong.Equal("/key", "value"),
            singyeong.LessThanEqual("/key2", 1234),
            singyeong.And(
                singyeong.GreaterThan("/key3", 10),
                singyeong.LessThan("/key3", 20),
            ),
            singyeong.In("/key4", ["123", "456"])
        ],
    )
    
    payload = {"foo": "bar"}
    
    await client.send(target, payload)  # or await client.broadcast(...)
```


### Keyword arguments for singyeong.Target():

**application**: ID of the application to query against \
**restricted**: Whether or not to allow restricted-mode clients in the query results \
**key**: The key used for consistent-hashing when choosing a client from the output \
**droppable**: Whether or not this payload can be dropped if it isn't routable \
**optional**: Whether or not this query is optional, ie. will be ignored and a client
will be chosen randomly if it matches nothing. \
**selector**: The selector used. May be None. \
**operators**: The ops used for querying.

### Available operators 

ComparisonOperator(path, to)
 - singyeong.Equal(...)
 - singyeong.NotEqual(...)
 - singyeong.GreaterThan(...)
 - singyeong.GreaterThanEqual(...)
 - singyeong.LessThan(...)
 - singyeong.LessThanEqual(...)
 - singyeong.In(...)
 - singyeong.Contains(...)
 - singyeong.NotContains(...)

LogicalOperator(comparison_op1, comparison_op2, comparison_op3, ... )
 - singyeong.And(...)
 - singyeong.Or(...)
 - singyeong.Nor(...)

### Available selectors

 - singyeong.Minimum(name)
 - singyeong.Maximum(name)
 - singyeong.Average(name)

## Run 신경 client 

You can run 신경 client in the main loop or in the separate task (if you have e.g. discord.py running).

### Running 신경 in the loop (recommended)

```python
import singyeong

client = singyeong.Client("dsn")

...

client.run()
```

### Running 신경 in the background
```python
import singyeong
import asyncio

loop = asyncio.get_event_loop()
client = singyeong.Client("dsn")

...

singyeong_task = loop.create_task(client.connect())

try:
    loop.run_until_complete(main())  # <- Your async function here
finally:    
    singyeong_task.cancel()
    loop.run_until_complete(
        asyncio.gather(singyeong_task, return_exceptions=True)
    )

```

### Running 신경 along with discord.py
In some cases, it is not required to manually close the task. E.g. discord.py automatically closes all tasks gracefully on the shutdown.

```python
import discord
import singyeong
import asyncio

loop = asyncio.get_event_loop()

bot = discord.Client()
client = singyeong.Client("dsn")

...

loop.create_task(client.connect())
bot.run("token")
```

## Logging


신경.py logs errors and debug information via the [logging](https://docs.python.org/3/library/logging.html) python
module. It is strongly recommended that the logging module is
configured, as no errors or warnings will be output if it is not set up.
Configuration of the ``logging`` module can be as simple as:

```python
import logging

logging.basicConfig(level=logging.INFO)
```

Placed at the start of the application. This will output the logs from
discord as well as other libraries that use the ``logging`` module
directly to the console.

The optional ``level`` argument specifies what level of events to log
out and can be any of ``CRITICAL``, ``ERROR``, ``WARNING``, ``INFO``, and
``DEBUG`` and if not specified defaults to ``WARNING``.

More advanced setups are possible with the [logging](https://docs.python.org/3/library/logging.html) module. For
example to write the logs to a file called ``error.log`` instead of
outputting them to the console the following snippet can be used:

```python
import logging

logger = logging.getLogger("singyeong")
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(filename="error.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)
```

This is recommended, especially at verbose levels such as ``INFO``
and ``DEBUG``, as there are a lot of events logged and it would clog the
stdout of your program.



For more information, check the documentation and tutorial of the
[logging](https://docs.python.org/3/library/logging.html) module.

# To-Do
 - Metadata support :)
 - Queues
 - Unit tests
