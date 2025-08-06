from pydantic import BaseModel
import datetime

class TaskBase(BaseModel):
    name: str

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    status: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class ProxyBase(BaseModel):
    host: str
    port: int
    username: str | None = None
    password: str | None = None

class ProxyCreate(ProxyBase):
    pass

class Proxy(ProxyBase):
    id: int

    class Config:
        orm_mode = True