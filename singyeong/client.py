import asyncio
import logging
import traceback
import warnings

import websockets

from .backoff import ExponentialBackoff
from .dsn import DSN
from .enums import Encoding, OpCode
from .exceptions import UnsupportedEncoding, WSClosed
from .message import Message
from .query import Target
from .utils import maybe_coroutine, with_type
from .websocket import SingyeongSocket

log = logging.getLogger(__name__)


class Client:
    # noinspection PyTypeChecker
    def __init__(self, dsn, *, loop=None):
        self.ws = None
        self.dsn = DSN(dsn)
        self.loop = asyncio.get_event_loop() if loop is None else loop

        if self.dsn.encoding == Encoding.MSGPACK:
            raise ImportError("Unsupported MSGPACK encoding. Type 'pip install msgpack'.")

        if self.dsn.encoding == Encoding.ETF:
            warnings.warn(f"Unsupported ETF encoding. Switching to JSON.", UnsupportedEncoding)
            self.dsn.encoding = Encoding.JSON

        self._metadata = {}
        self._closed = False
        self._ready = asyncio.Event()

    @property
    def latency(self):
        """Gateway latency in milliseconds"""
        return self.ws.latency if self.ws else float("infinity")

    async def send(self, target: [dict, Target], payload, nonce=None):

        data = {
            "target": target if isinstance(target, dict) else target.as_dict(),
            "payload": payload
        }

        if nonce is not None:
            data['nonce'] = nonce

        await self.ws.send_json({
            "op": OpCode.DISPATCH,
            "t": "SEND",
            "d": data
        })

    async def broadcast(self, target: [dict, Target], payload, nonce=None):

        data = {
            "target": target if isinstance(target, dict) else target.as_dict(),
            "payload": payload
        }

        if nonce is not None:
            data['nonce'] = nonce

        await self.ws.send_json({
            "op": OpCode.DISPATCH,
            "t": "BROADCAST",
            "d": data
        })

    async def update_metadata(self, md):
        self._metadata.update(md)

        await self.wait_until_ready()
        await self.ws.send_json({
            "op": OpCode.DISPATCH,
            "t": "UPDATE_METADATA",
            "d": {key: with_type(value) for key, value in self._metadata.items()}
        })

    def is_closed(self):
        """Indicates if the websocket connection is closed."""
        return self._closed

    # noinspection PyMethodMayBeStatic, PyUnusedLocal
    def on_error(self, exc):
        traceback.print_exc()

    async def on_raw_packet(self, message: Message):
        """Called when the 신경 has sent to you BROADCAST or SEND event."""

    async def on_ready(self):
        """Called when the 신경 has accepted you, and will send you packets. Usually after login is successful."""

    async def _on_ready(self):
        if self._metadata:
            await self.ws.send_json({
                "op": OpCode.DISPATCH,
                "t": "UPDATE_METADATA",
                "d": {key: with_type(value) for key, value in self._metadata.items()}
            })

        self._ready.set()
        await maybe_coroutine(self.on_ready)

    async def wait_until_ready(self):
        await self._ready.wait()

    def start(self):
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        backoff = ExponentialBackoff()

        while not self.is_closed():
            try:
                self.ws = await SingyeongSocket.from_client(self)
                while True:
                    await self.ws.poll_event()
            except asyncio.CancelledError:
                raise
            except (OSError,
                    ValueError,
                    asyncio.TimeoutError,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError,
                    WSClosed,
                    websockets.InvalidMessage):

                self.ws.close()

                if self.is_closed():
                    return

                retry = backoff.delay()
                log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
