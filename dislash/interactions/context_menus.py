class ApplicationCommandType:
    CHAT_INPUT = 1
    SLASH = 1
    USER = 2
    MESSAGE = 3


class ApplicationCommand:
    def __init__(self, type):
        self.type = type


class UserCommand(ApplicationCommand):
    def __init__(self, name):
        super().__init__(ApplicationCommandType.USER)
        self.name = name
    
    def __repr__(self):
        return f"<UserCommand name={self.name}>"
    
    def to_dict(self):
        return {
            "type": self.type,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        if data.pop("type", 0) == ApplicationCommandType.USER:
            return UserCommand(data["name"])


class MessageCommand(ApplicationCommand):
    def __init__(self, name):
        super().__init__(ApplicationCommandType.MESSAGE)
        self.name = name
    
    def __repr__(self):
        return f"<MessageCommand name={self.name}>"
    
    def to_dict(self):
        return {
            "type": self.type,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        if data.pop("type", 0) == ApplicationCommandType.MESSAGE:
            return MessageCommand(data["name"])
