from file_system import File_System
from fastapi import FastAPI
from fastapi import Header
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from jose import jwt , JWTError
from datetime import datetime, timedelta
import threading
import asyncio
class PathRequest(BaseModel):
    path : str
    pass
class DoublePathRequest(BaseModel):
    src_path : str
    dest_path : str
class fileContentRequest(BaseModel):
    path : str
    content : str
class itemRenameRequest(BaseModel):
    path : str
    new_name : str
class User(BaseModel):
    username : str
    email : str
    password : str
class UserLogin(BaseModel):
    email : str
    password : str
fs_lock = threading.Lock()
app = FastAPI()
user_fs = {}

SECRET_KEY = "Jai_shree_ram"
EXPIRE_IN_MINUTES = 7200
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
uri = "mongodb://127.0.0.1:27017/"
client = MongoClient(uri)
async def autosavehandler():
    while True:
        await asyncio.sleep(30)
        for key in list(user_fs.keys()):
            await asyncio.to_thread(user_fs[key].save)

@app.on_event("startup")
async def autosave():
    asyncio.create_task(autosavehandler())

def createToken(data : dict):
    payload = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes= EXPIRE_IN_MINUTES
    )

    payload.update({"exp" : expire})

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm= "HS256"
    )
    return token

def reloadUserFs(userId : str):
    if userId not in user_fs:
        user_fs[userId] = File_System(f"data/{userId}_fs.dump")
@app.post("/api/signup")
def signup(req : User):
    if not req.username or not req.email or not req.password or (len(req.username.strip()) == 0 or len(req.email.strip()) == 0 or len(req.password.strip()) == 0):
        return {"status" : "FAILUIRE" , "message" : "empty field"}
    try:
        database = client.get_database("fs_user_db")
        users = database.get_collection("User")
        # Check if user exists
        if users.find_one({"email": req.email}):
            return {"status": "FAILURE", "message": "User already exists"}
        query = {"username" : req.username , "email" : req.email, "password" : req.password}

        users.insert_one(query)
        return {"status" : "OK"}
    except Exception as e:
        return {"status" : "FAILURE" , "message" : str(e)}

@app.post("/api/signin")
def signin(req : UserLogin):
    if not req.email or not req.password:
        return {"status" : "FAILURE" , "message" : "empty field"}
    try:
        database = client.get_database("fs_user_db")
        users = database.get_collection("User")
        user = users.find_one({"email" : req.email})
        if(user == None):
            return {"status" : "FAILURE" , "message" : "user not found"}
        if(user["password"] != req.password):
            return {"status" : "FAILURE" , "message" : "wrong password"}
        
        userid = str(user["_id"])
        token = createToken({"username" : user["username"],"userId" : userid})
        if userid in user_fs:
            return {"status" : "OK" ,
                    "access_token": token,
                    "token_type" : "bearer",
                    "result" : {"username" : user["username"]}}
        user_fs[userid] = File_System(f"data/{userid}_fs.dump")
        print(user_fs[userid])
        return {"status" : "OK" ,
                "access_token": token,
                "token_type" : "bearer",
                "result" : {"username" : user["username"]}}

    except Exception as e:
        return {"status" : "FAILURE" , "message" : str(e)}
@app.delete("/api/signout")
def signout(authorization : str = Header(None)):
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )
        userId = payload["userId"]
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    if userId in user_fs:
        user_fs[userId].close()
        del user_fs[userId]
    return {"status" : "OK"}

@app.post("/api/get_dir_contents/")
def get_dir_contents(req : PathRequest, authorization : str = Header(None)):
    if not req.path or len(req.path.strip()) == 0:
        return {"status" : "FAILURE" , "message" : "empty field"}
    
    try:
        if authorization == None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        userId = payload["userId"]
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "token error"
        }
    with fs_lock:
        reloadUserFs(userId)
        res = user_fs[userId].get_contents(req.path)
        return {"result" : res,"status" : "OK"}

@app.post("/api/get_file_content/")
def read_file(req : PathRequest, authorization : str = Header(None)):
    if not req.path or len(req.path.strip()) == 0:
        return {"status" : "FAILURE" , "message" : "empty field"}
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        
        token = authorization.split(" ")[1]
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )
        userId = payload["userId"]
    except JWTError:
        return{
           "status" : "FAILURE",
           "message" : "token missing"
        }
    with fs_lock:
        reloadUserFs(userId)
        return {
            "status" : "OK",
            "content": user_fs[userId].file_show(req.path)
        }


@app.post("/api/mkdir/")
def mkdir(req : PathRequest, authorization : str = Header(None)):
    if not req.path or len(req.path.strip()) == 0:
            return {"status" : "FAILURE" , "message" : "directory can not be creted by an name"}
    try:
        if authorization == None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        userId = payload["userId"]
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "token error"
        }
    with fs_lock:
        
        reloadUserFs(userId)
        status = user_fs[userId].make_dir(req.path)
        if status == 10:
            return {"status" : "FAILURE" , "message" : "Directory already exists"}
        res_list = req.path.split("/")
        res_list.pop()

        return {"status" : "OK" , "result" : user_fs[userId].get_contents("/".join(res_list))}

@app.post("/api/create_file/")
def create_file(req : PathRequest, authorization : str = Header(None)):
    if not req.path or len(req.path.strip()) == 0:
            return {"status" : "FAILURE" , "message" : "Can not create a file of empty name"}
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    
    with fs_lock:
        reloadUserFs(userId)
        status = user_fs[userId].touch(req.path)
        if status == 6:
            return {"status" : "FAILURE" , "message" : "File already exist"}
        if status == 14:
            return {"status" : "FAILURE" , "message" : "File creation failed"}
        res_list = req.path.split("/")
        res_list.pop()
        return {"status" : "OK" , "result" : user_fs[userId].get_contents("/".join(res_list))}

@app.post("/api/write_file_content/")
def write_file_content(req : fileContentRequest, authorization : str = Header(None)):

    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    with fs_lock:
        if (req.path and req.content ) and (len(req.path.strip()) != 0 and len(req.content.strip()) != 0):
            reloadUserFs(userId)
            status = user_fs[userId].write(req.content,req.path)
            if status == 5:
                return {"status": "FAILURE" , "message":"File not found"}
            return {"status" : "OK" , "message" : "success"}
        
@app.post("/api/remove_dir/")
def remove_dir(req : PathRequest, authorization : str = Header(None)):
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    
    with fs_lock:
        if req.path and len(req.path.strip()) != 0:
            reloadUserFs(userId)
            status = user_fs[userId].remove_dir(req.path)

            if status == 9:
                return {"status" : "FAILURE" , "message" : "directory not found"}
            if status == 18:
                return {"status" : "FAILURE" , "message" : "Root directory can not be deleted"}
            res_list = req.path.split("/")
            res_list.pop()
            return {"status" : "OK" , "result" : user_fs[userId].get_contents("/".join(res_list))}
@app.post("/api/remove_file/")
def remove_file(req : PathRequest, authorization : str = Header(None)):
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    
    with fs_lock:
        if req.path and len(req.path.strip()) != 0:
            status = user_fs[userId].rm(req.path)

            if status == 9:
                return {"status" : "FAILURE" , "message" : "directory not found"}
            if status == 5:
                return {"status" : "FAILURE" , "message" : "File not found"}
            res_list = req.path.split("/")
            res_list.pop()
            return {"status" : "OK" , "result" : user_fs[userId].get_contents("/".join(res_list))}
@app.post("/api/move/")
def move(req : DoublePathRequest, authorization : str = Header(None)):
    if (not req.src_path or not req.dest_path ) or (len(req.src_path.strip()) == 0 or len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "missing field"}
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    
    with fs_lock:
        if (not req.src_path or not req.dest_path ) or (len(req.src_path.strip()) == 0 or len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "missing field"}
        reloadUserFs(userId)
        status = user_fs[userId].cut(req.src_path , req.dest_path)
        if status == 9:
            return {"status" : "FAILURE" , "message" : "Directory not found"}
        if status == 21:
            return {"status" : "FAILURE" , "message" : "Directory can not move to itself"}
        if status == 22:
            return {"status" : "FAILURE" , "message" : "It already exists so can not move"}
        return {"status" : "OK" , "result" : user_fs[userId].get_contents(req.dest_path)}
@app.post("/api/copy/")
def copy(req : DoublePathRequest, authorization : str = Header(None)):
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    
    with fs_lock:
        if (not req.src_path or not req.dest_path ) or (len(req.src_path.strip()) == 0 or len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "empty field"}
        reloadUserFs(userId)
        status = user_fs[userId].cp(req.src_path , req.dest_path)
        if status == 9:
            return {"status" : "FAILURE" , "message" : "Directory not found"}
        if status == 25:
            return {"status" : "FAILURE" , "message" : "Directory can not copy to itself"}
        if status == 22:
            return {"status" : "FAILURE" , "message" : "It already exists so can not copy"}
        return {"status" : "OK" , "result" : user_fs[userId].get_contents(req.dest_path)}

@app.post("/api/rename/")
def rename_item(req : itemRenameRequest , authorization : str = Header(None)):
    if (not req.path and not req.new_name) and (len(req.path.strip()) == 0 and len(req.new_name.strip()) == 0):
            return {"status" : "FAILURE" , "message" : "empty field"}
    try:
        if authorization is None:
            return {
                "status" : "FAILURE",
                "message" : "Token missing"
            }
        token = authorization.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms= ["HS256"]
        )

        userId = payload["userId"]
    
    except JWTError:
        return {
            "status" : "FAILURE",
            "message" : "Token error"
        }
    
    with fs_lock:
        
        reloadUserFs(userId)
        status = user_fs[userId].rename(req.path, req.new_name)
        if status == 23:
            return {"status" : "FAILURE" ,"message": "Item is not file or a directory"}
        if status == 9:
            return {"status" : "FAILURE" ,"message": "Directory not found"}
        if status == 10:
            return {"status" : "FAILURE" ,"message": "Directory already exists"}
        if status == 5:
            return {"status" : "FAILURE" ,"message": "File not found"}
        if status == 6:
            return {"status" : "FAILURE" ,"message": "File already exists"}
        res_list = req.path.split("/")
        res_list.pop()
        return {"status" : "OK" ,"result": user_fs[userId].get_contents("/".join(res_list))}

@app.on_event("shutdown")
def shutdown():
    client.close()
    for keys in list(user_fs.keys()):
        print(user_fs[keys].load_path)
        user_fs[keys].close()
