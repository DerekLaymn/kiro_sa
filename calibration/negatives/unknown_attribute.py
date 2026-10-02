from typing import reveal_type


class Message:
    data = None


def receive(msg: Message) -> None:
    reveal_type(msg.data)


receive(Message())
