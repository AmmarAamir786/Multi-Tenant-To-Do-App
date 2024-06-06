from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import Annotated
from contextlib import asynccontextmanager
from multi_tenant_to_do_app.auth import EXPIRY_TIME, authenticate_user, create_access_token, create_refresh_token, current_user, validate_refresh_token
from multi_tenant_to_do_app.db import get_session, create_tables
from multi_tenant_to_do_app.models import Todo, Todo_Create, Todo_Edit, Token, User
from multi_tenant_to_do_app.router import user


# create a context manager that will run right as when the app starts up. Here the first thing the app will do is create the tables
@asynccontextmanager
async def lifespan(app:FastAPI, title="Fight Your Dementia", version="1.0.0"):
    print("Creating Tables")
    create_tables()
    print("Tables Created")
    yield

# create desired http methods
app : FastAPI = FastAPI(lifespan=lifespan)

@app.get('/')
async def root():
    return {"message" : "Welcome. This is not your first time here :)"}

@app.post('/todos/', response_model=Todo) #response model is used to validate the data
async def create_todo(current_user: Annotated[User, Depends(current_user)],
                      todo:Todo_Create, 
                      session:Annotated[Session, Depends(get_session)]): #todo is data given by the user. session is where we are injecting our depedency
    
    new_todo = Todo(content=todo.content, user_id=current_user.id)
    
    session.add(new_todo) #saves in memory not in db
    session.commit() #this will create data in db. commit also removes the data from the variables
    session.refresh(new_todo)   
    return new_todo

@app.get('/todos/', response_model=list[Todo])
async def get_all(current_user: Annotated[User, Depends(current_user)], 
                  session:Annotated[Session, Depends(get_session)]):
    
    todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    if todos:
        return todos
    else:
        raise HTTPException (status_code=404, detail="Tasks does not exist.")


@app.get('/todos/{id}', response_model=Todo)
async def get_single_todo(id: int, 
                          current_user:Annotated[User, Depends(current_user)],
                          session: Annotated[Session, Depends(get_session)]):
    
    user_todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    matched_todo = next((todo for todo in user_todos if todo.id == id),None)

    if matched_todo:
        return matched_todo
    else:
        raise HTTPException(status_code=404, detail="No Task found")
        

@app.put('/todos/{id}')
async def edit_todo(id: int, 
                    todo: Todo_Edit,
                    current_user:Annotated[User, Depends(current_user)], 
                    session: Annotated[Session, Depends(get_session)]):
    
    user_todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    existing_todo = next((todo for todo in user_todos if todo.id == id),None)

    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="No task found")


@app.delete('/todos/{id}')
async def delete_todo(id: int,
                      current_user:Annotated[User, Depends(current_user)],
                      session: Annotated[Session, Depends(get_session)]):
    
    user_todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    todo = next((todo for todo in user_todos if todo.id == id),None)
    
    if todo:
        session.delete(todo)
        session.commit()
        # session.refresh(todo)
        return {"message": "Task successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="No task found")


######### Multi Tanant With 0Auth2 #########
app.include_router(router=user.user_router)

#login
@app.post("/token", response_model=Token)
async def login(form_data:Annotated[OAuth2PasswordRequestForm, Depends()],session: Annotated[Session, Depends(get_session)]):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    expire_time = timedelta(minutes=EXPIRY_TIME)
    access_token = create_access_token({"sub":form_data.username}, expire_time)
    return Token(access_token=access_token, token_type="bearer")


@app.post("/token/refresh")
def refresh_token(old_refresh_token:str,
                  session:Annotated[Session, Depends(get_session)]):
    
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token, Please login again",
        headers={"www-Authenticate":"Bearer"}
    )
    
    user = validate_refresh_token(old_refresh_token,
                                  session)
    if not user:
        raise credential_exception
    
    expire_time = timedelta(minutes=EXPIRY_TIME)
    access_token = create_access_token({"sub":user.username}, expire_time)

    refresh_expire_time = timedelta(days=7)
    refresh_token = create_refresh_token({"sub":user.email}, refresh_expire_time)

    return Token(access_token=access_token, token_type= "bearer", refresh_token=refresh_token)