from pydantic import BaseModel


class BotSchema(BaseModel):
    id: str
    name: str
