from datetime import datetime


class LastNotifiedDict(dict):
    def __setitem__(self, key, value):
        if not isinstance(value, datetime):
            raise ValueError("Value must be a datetime object")
        super().__setitem__(key, value)

    def to_json(self):
        return {str(mac).lower(): dt.isoformat() for mac, dt in self.items()}

    @classmethod
    def from_json(cls, data):
        return cls({str(mac).lower(): datetime.fromisoformat(dt) for mac, dt in data.items()})

