from pydantic import BaseModel


class TradeSchema(BaseModel):
    id: str
    symbol: str
