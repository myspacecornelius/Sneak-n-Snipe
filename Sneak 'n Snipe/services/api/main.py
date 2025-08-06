from fastapi import FastAPI, Depends, HTTPException, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sneak 'n Snipe API",
    description="The main API gateway for the Sneak 'n Snipe application.",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:5173",  # React frontend
    "http://localhost:3000",  # Grafana
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sneak 'n Snipe API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task)

@app.get("/tasks/", response_model=list[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db, skip=skip, limit=limit)
    return tasks

@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.post("/proxies/", response_model=schemas.Proxy)
def create_proxy(proxy: schemas.ProxyCreate, db: Session = Depends(get_db)):
    return crud.create_proxy(db=db, proxy=proxy)

@app.get("/proxies/", response_model=list[schemas.Proxy])
def read_proxies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    proxies = crud.get_proxies(db, skip=skip, limit=limit)
    return proxies

@app.get("/proxies/{proxy_id}", response_model=schemas.Proxy)
def read_proxy(proxy_id: int, db: Session = Depends(get_db)):
    db_proxy = crud.get_proxy(db, proxy_id=proxy_id)
    if db_proxy is None:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return db_proxy
