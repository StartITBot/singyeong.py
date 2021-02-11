import asyncio
import logging
import time
import uuid
from typing import Union

import websockets

from singyeong.message import Message
from singyeong.utils import maybe_coroutine

try:
    import msgpack
except ImportError:
    msgpack = None

try:
    import ujson as json
except ImportError:
    import json

from singyeong.enums import Encoding, OpCode

log = logging.getLogger(__name__)


class SingyeongSocket(websockets.WebSocketClientProtocol):
    def __init__(self, **kwargs):
        self.client_id = uuid.uuid4()
        self.encoding = kwargs.pop("encoding")
        self.auth = kwargs.pop("auth")
        self.on_ready = kwargs.pop("on_ready", lambda: ...)
        self.on_message = kwargs.pop("on_message", lambda _: ...)
        self.on_error = kwargs.pop("on_error", lambda _: ...)

        self.heartbeat_interval_task = None
        super().__init__(**kwargs)

        self._last_heartbeat = None
        self._latency = None

    async def close_connection(self):
        if self.heartbeat_interval_task:
            self.heartbeat_interval_task.cancel()
        return await super().close_connection()

    @property
    def latency(self):
        """Gateway latency in milliseconds"""
        return float("infinity") if self._latency is None else self._latency * 1000

    async def heartbeat(self, sleep):
        while True:
            self._last_heartbeat = time.time()
            await self.send_json({
                "op": OpCode.HEARTBEAT,
                "d": {
                    "client_id": f'{self.client_id}'
                }
            })
            await asyncio.sleep(sleep)

    @classmethod
    async def from_client(cls, client):

        def create_protocol(**kwargs):
            return cls(
                on_error=client.on_error,
                on_ready=client._on_ready,
                on_message=client.on_raw_packet,
                encoding=client.dsn.encoding,
                auth=(client.dsn.login, client.dsn.password),
                **kwargs
            )

        return await websockets.connect(
            f"ws{'s' if client.dsn.encryption else ''}://{client.dsn.host}:{client.dsn.port}/gateway/websocket"
            f"?encoding={client.dsn.encoding.value}",
            loop=client.loop,
            create_protocol=create_protocol
        )

    async def poll_event(self):
        encoded_data: websockets.Data = await self.recv()

        try:
            data = self._decode(encoded_data)
            assert isinstance(data, dict)

            op = OpCode(data['op'])

            if op == OpCode.HELLO:

                if self.heartbeat_interval_task:
                    self.heartbeat_interval_task.cancel()

                self.heartbeat_interval_task = self.loop.create_task(self.heartbeat(
                    int(data['d']['heartbeat_interval']) / 1000
                ))

                response = {
                    "client_id": f'{self.client_id}',
                    "application_id": self.auth[0],
                }

                if self.auth[1]:
                    response['auth'] = self.auth[1]

                await self.send_json({
                    "op": OpCode.IDENTIFY,
                    "d": response
                })
                return

            if op == OpCode.READY:
                await maybe_coroutine(self.on_ready)
                return

            if op == OpCode.HEARTBEAT_ACK:
                self._latency = time.time() - self._last_heartbeat
                return

            if op == OpCode.DISPATCH:
                self.loop.create_task(self.handle_dispatch(data))
                return

        except AssertionError:
            pass
        except Exception as ex:
            await maybe_coroutine(self.on_error, ex)

    async def handle_dispatch(self, data):
        if data['t'] in ("SEND", "BROADCAST"):
            payload = data['d']

            await maybe_coroutine(
                self.on_message,
                Message(
                    nonce=payload.get('nonce'),
                    payload=payload['payload'],
                    timestamp=data['ts'],
                    event_name=data['t']
                )
            )

    async def send_json(self, data) -> None:
        encoded_data = self._encode(data)
        await self.send(encoded_data)

    def _encode(self, data: websockets.Data) -> bytes:
        if self.encoding == Encoding.JSON:
            return json.dumps(data)
        if self.encoding == Encoding.MSGPACK:
            return msgpack.packb(data)
        raise RuntimeError

    def _decode(self, data: websockets.Data) -> Union[dict, list]:
        if self.encoding == Encoding.JSON:
            return json.loads(data)
        if self.encoding == Encoding.MSGPACK:
            return msgpack.unpackb(data)
        raise RuntimeError
