from sqlalchemy.orm import Session
import models, schemas

def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Task).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(name=task.name)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_proxy(db: Session, proxy_id: int):
    return db.query(models.Proxy).filter(models.Proxy.id == proxy_id).first()

def get_proxies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Proxy).offset(skip).limit(limit).all()

def create_proxy(db: Session, proxy: schemas.ProxyCreate):
    db_proxy = models.Proxy(**proxy.dict())
    db.add(db_proxy)
    db.commit()
    db.refresh(db_proxy)
    return db_proxy