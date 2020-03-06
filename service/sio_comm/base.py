from typing import TypeVar

from core import AttributeStorage
from log import Log
from service import Message


_MsgT = TypeVar("_MsgT", Message, Message)


class BaseCommunicatorKey(AttributeStorage):
    pass


class BaseCommunicator:
    def __init__(self, key: BaseCommunicatorKey):
        self.key = key
        self.logger = Log(f"{self.__class__.__name__}")

    async def connect(self):
        raise NotImplementedError()

    @property
    def connected(self):
        raise NotImplementedError()

    async def send(self, msg: _MsgT) -> _MsgT:
        msg: Message
        raise NotImplementedError()

    async def get(self, msg: Message):
        msg = await self.send(msg)
        return await msg.result()

    async def recv(self) -> Message:
        raise NotImplementedError()

    async def disconnect(self):
        raise NotImplementedError()

    async def wait_disconnected(self):
        raise NotImplementedError()

    @property
    def disconnected(self):
        raise NotImplementedError()

