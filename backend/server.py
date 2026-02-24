from file_system import File_System
from fastapi import FastAPI
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import threading
import asyncio
class PathRequest(BaseModel):
    userId : str
    path : str
    pass
class DoublePathRequest(BaseModel):
    userId : str
    src_path : str
    dest_path : str
class fileContentRequest(BaseModel):
    userId : str
    path : str
    content : str
class itemRenameRequest(BaseModel):
    userId : str
    path : str
    new_name : str
class User(BaseModel):
    username : str
    email : str
    password : str
class UserLogin(BaseModel):
    email : str
    password : str
class UserIdRequest(BaseModel):
    userId : str
fs_lock = threading.Lock()
app = FastAPI()
user_fs = {}
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
        if userid in user_fs:
            return {"status" : "OK" , "result" : {"username" : user["username"],"userId" : userid}}
        user_fs[userid] = File_System(f"data/{userid}_fs.dump")
        print(user_fs[userid])
        return {"status" : "OK" , "result" : {"username" : user["username"],"userId" : userid}}

    except Exception as e:
        return {"status" : "FAILURE" , "message" : str(e)}
@app.post("/api/signout")
def signout(req : UserIdRequest):
    if req.userId in user_fs:
        user_fs[req.userId].close()
        del user_fs[req.userId]
        return {"status" : "OK"}
    return {"status" : "FAILURE"}

@app.post("/api/get_dir_contents/")
def get_dir_contents(req : PathRequest):
    if not req.userId or not req.path or len(req.userId.strip()) == 0 or len(req.path.strip()) == 0:
        return {"status" : "FAILURE" , "message" : "empty field"}
    with fs_lock:
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        res = user_fs[req.userId].get_contents(req.path)
        return {"result" : res,"status" : "OK"}

@app.post("/api/get_file_content/")
def read_item(req : PathRequest):
    if not req.userId or not req.path or len(req.userId.strip()) == 0 or len(req.path.strip()) == 0:
        return {"status" : "FAILURE" , "message" : "empty field"}
    with fs_lock:
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        return {"content": user_fs[req.userId].file_show(req.path)}


@app.post("/api/mkdir/")
def mkdir(req : PathRequest):
    with fs_lock:
        if not req.path or not req.userId or len(req.path.strip()) == 0 or len(req.userId.strip()) == 0:
            return {"status" : "FAILURE" , "message" : "directory can not be creted by an name"}
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        status = user_fs[req.userId].make_dir(req.path)
        if status == 10:
            return {"status" : "FAILURE" , "message" : "Directory already exists"}
        res_list = req.path.split("/")
        res_list.pop()

        return {"status" : "OK" , "result" : user_fs[req.userId].get_contents("/".join(res_list))}

@app.post("/api/create_file/")
def create_file(req : PathRequest):
    with fs_lock:
        if not req.path or not req.userId or len(req.path.strip()) == 0 or len(req.userId.strip()) == 0:
            return {"status" : "FAILURE" , "message" : "Can not create a file of empty name"}
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        status = user_fs[req.userId].touch(req.path)
        if status == 6:
            return {"status" : "FAILURE" , "message" : "File already exist"}
        if status == 14:
            return {"status" : "FAILURE" , "message" : "File creation failed"}
        res_list = req.path.split("/")
        res_list.pop()
        return {"status" : "OK" , "result" : user_fs[req.userId].get_contents("/".join(res_list))}

@app.post("/api/write_file_content/")
def write_file_content(req : fileContentRequest):
    with fs_lock:
        if (req.path and req.content ) and (len(req.path.strip()) != 0 and len(req.content.strip()) != 0):
            if req.userId not in user_fs:
                return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
            status = user_fs[req.userId].write(req.content,req.path)
            if status == 5:
                return {"status": "FAILURE" , "message":"File not found"}
            return {"status" : "OK" , "message" : "success"}
        
@app.post("/api/remove_dir/")
def remove_dir(req : PathRequest):
    with fs_lock:
        if req.path and len(req.path.strip()) != 0:
            if req.userId not in user_fs:
                return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
            status = user_fs[req.userId].remove_dir(req.path)

            if status == 9:
                return {"status" : "FAILURE" , "message" : "directory not found"}
            if status == 18:
                return {"status" : "FAILURE" , "message" : "Root directory can not be deleted"}
            res_list = req.path.split("/")
            res_list.pop()
            return {"status" : "OK" , "result" : user_fs[req.userId].get_contents("/".join(res_list))}
@app.post("/api/remove_file/")
def remove_file(req : PathRequest):
    with fs_lock:
        if req.userId and req.path and len(req.path.strip()) != 0 and len(req.userId.strip()) != 0:
            status = user_fs[req.userId].rm(req.path)

            if status == 9:
                return {"status" : "FAILURE" , "message" : "directory not found"}
            if status == 5:
                return {"status" : "FAILURE" , "message" : "File not found"}
            res_list = req.path.split("/")
            res_list.pop()
            return {"status" : "OK" , "result" : user_fs[req.userId].get_contents("/".join(res_list))}
@app.post("/api/move/")
def move(req : DoublePathRequest):
    with fs_lock:
        if (not req.src_path or not req.dest_path ) or (len(req.src_path.strip()) == 0 or len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "missing field"}
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        status = user_fs[req.userId].cut(req.src_path , req.dest_path)
        if status == 9:
            return {"status" : "FAILURE" , "message" : "Directory not found"}
        if status == 21:
            return {"status" : "FAILURE" , "message" : "Directory can not move to itself"}
        if status == 22:
            return {"status" : "FAILURE" , "message" : "It already exists so can not move"}
        return {"status" : "OK" , "result" : user_fs[req.userId].get_contents(req.dest_path)}
@app.post("/api/copy/")
def copy(req : DoublePathRequest):
    with fs_lock:
        if (not req.src_path or not req.dest_path ) or (len(req.src_path.strip()) == 0 or len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "empty field"}
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        status = user_fs[req.userId].cp(req.src_path , req.dest_path)
        if status == 9:
            return {"status" : "FAILURE" , "message" : "Directory not found"}
        if status == 25:
            return {"status" : "FAILURE" , "message" : "Directory can not copy to itself"}
        if status == 22:
            return {"status" : "FAILURE" , "message" : "It already exists so can not copy"}
        return {"status" : "OK" , "result" : user_fs[req.userId].get_contents(req.dest_path)}

@app.post("/api/rename/")
def rename_item(req : itemRenameRequest):
    with fs_lock:
        if (not req.path and not req.new_name) and (len(req.path.strip()) == 0 and len(req.new_name.strip()) == 0):
            return {"status" : "FAILURE" , "message" : "empty field"}
        if req.userId not in user_fs:
            return {"status" : "FAILURE" , "message" : "you havn't signedin yet."}
        status = user_fs[req.userId].rename(req.path, req.new_name)
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
        return {"status" : "OK" ,"result": user_fs[req.userId].get_contents("/".join(res_list))}

@app.on_event("shutdown")
def shutdown():
    client.close()
    for keys in list(user_fs.keys()):
        print(user_fs[keys].load_path)
        user_fs[keys].close()
