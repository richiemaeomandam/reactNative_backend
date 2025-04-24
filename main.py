from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import SessionLocal, engine, Base
import models, schemas
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use specific IP in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# DB dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# GET with optional filtering
@app.get("/tasks/", response_model=list[schemas.Task])
async def read_tasks(status: str = None, db: AsyncSession = Depends(get_db)):
    query = select(models.Task)
    if status == "completed":
        query = query.where(models.Task.completed == True)
    elif status == "pending":
        query = query.where(models.Task.completed == False)
    result = await db.execute(query)
    return result.scalars().all()

# POST create
@app.post("/tasks/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db: AsyncSession = Depends(get_db)):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

# PUT update
@app.put("/tasks/{task_id}", response_model=schemas.Task)
async def update_task(task_id: int, task: schemas.TaskCreate, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(models.Task).where(models.Task.id == task_id))
    db_task = query.scalar_one_or_none()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.title = task.title
    db_task.completed = task.completed
    await db.commit()
    await db.refresh(db_task)
    return db_task

# DELETE
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(models.Task).where(models.Task.id == task_id))
    db_task = query.scalar_one_or_none()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(db_task)
    await db.commit()
    return {"message": "Task deleted"}
