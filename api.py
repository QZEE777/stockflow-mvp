from fastapi import FastAPI
from pydantic import BaseModel
from parser import parse_message

app = FastAPI()

class MessageRequest(BaseModel):
    message: str

@app.post("/parse")
def parse(req: MessageRequest):
    return parse_message(req.message)
