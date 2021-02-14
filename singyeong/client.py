import asyncio
import logging
import signal
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

        if self.dsn.encoding == Encoding.MSGPACK:  # Is msgpack installed?
            try:
                import msgpack
            except ImportError:
                raise ImportError("Unsupported MSGPACK encoding. Type 'pip install msgpack'.")

        if self.dsn.encoding == Encoding.ETF:
            warnings.warn(f"Unsupported ETF encoding. Switching to JSON.", UnsupportedEncoding)
            self.dsn.encoding = Encoding.JSON

        self._metadata = {}
        self._closing = False
        self._ready = asyncio.Event()

    @property
    def latency(self):
        """Gateway latency in milliseconds"""
        return self.ws.latency if self.ws else float("infinity")

    def event(self, coro):
        """A decorator that registers an event to listen to."""

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

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
        try:
            await maybe_coroutine(self.on_ready)
        except Exception as ex:
            await maybe_coroutine(self.on_error, ex)

    async def _on_raw_packet(self, message):
        try:
            await maybe_coroutine(self.on_raw_packet, message)
        except Exception as ex:
            await maybe_coroutine(self.on_error, ex)

    async def wait_until_ready(self):
        await self._ready.wait()

    async def _close(self):
        log.info('Closing connection.')
        self._closing = True  # Disables reconnect
        if self.ws:
            await self.ws.close()
            self.ws = None

    def run(self):
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(self.connect(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.info('Received signal to terminate singyeong and event loop.')
        finally:
            future.remove_done_callback(stop_loop_on_completion)

            if not self._closing:
                # Close connection before loop close.
                loop.run_until_complete(self._close())

            log.info('Cleaning up tasks.')
            _cancel_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())

            log.info('Closing the event loop.')
            loop.close()

        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                return None

    async def connect(self):
        backoff = ExponentialBackoff()

        while not self._closing:
            try:
                self.ws = await SingyeongSocket.from_client(self)
                while True:
                    await self.ws.poll_event()
            except asyncio.CancelledError:
                if not self._closing:
                    # Close connection before task cancel.
                    await self._close()

                raise
            except (OSError,
                    ValueError,
                    asyncio.TimeoutError,
                    websockets.ConnectionClosed,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError,
                    WSClosed,
                    websockets.InvalidMessage):

                if self._closing:
                    return

                if self.ws:
                    await self.ws.close()

                retry = backoff.delay()
                log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)


def _cancel_tasks(loop):
    try:
        task_retriever = asyncio.Task.all_tasks
    except AttributeError:
        # future proofing for 3.9 I guess
        task_retriever = asyncio.all_tasks

    tasks = {t for t in task_retriever(loop=loop) if not t.done()}

    if not tasks:
        return

    log.info('Cleaning up after %d tasks.', len(tasks))

    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    log.info('All tasks finished cancelling.')

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'Unhandled exception during Client.run shutdown.',
                'exception': task.exception(),
                'task': task
            })

