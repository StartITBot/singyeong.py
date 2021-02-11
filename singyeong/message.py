class Message:
    __slots__ = ('nonce', 'payload', 'timestamp', 'event_name')

    def __init__(self, **kwargs):
        self.nonce = kwargs.pop("nonce")
        self.payload = kwargs.pop("payload")
        self.timestamp = kwargs.pop("timestamp")
        self.event_name = kwargs.pop("event_name")

    def __repr__(self):
        return f"Message(" \
               f"nonce={self.nonce!r}, " \
               f"payload={self.payload!r}, " \
               f"timestamp={self.timestamp!r}, " \
               f"event_name={self.event_name!r}" \
               f")"
