from file_system import File_System
from fastapi import FastAPI
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading

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
fs_lock = threading.Lock()
app = FastAPI()
fs = File_System("fs.dump")
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

@app.post("/api/get_dir_contents/")
def get_dir_contents(dir_path : PathRequest):
    with fs_lock:
        if(not dir_path.path or len(dir_path.path.strip()) == 0):
            return {"status" : "FAILURE" , "message": "path is empty"}
        res = fs.get_contents(dir_path.path)
        return {"result" : res,"status" : "OK"}

@app.post("/api/get_file_content/")
def read_item(req : PathRequest):
    return {"content": fs.file_show(req.path)}


@app.post("/api/mkdir/")
def mkdir(req : PathRequest):
    with fs_lock:
        if not req.path or len(req.path.strip()) == 0:
            return {"status" : "FAILURE" , "message" : "directory can not be creted by an name"}
        status = fs.make_dir(req.path)
        if status == 10:
            return {"status" : "FAILURE" , "message" : "Directory already exists"}
        res_list = req.path.split("/")
        res_list.pop()

        return {"status" : "OK" , "result" : fs.get_contents("/".join(res_list))}

@app.post("/api/create_file/")
def create_file(req : PathRequest):
    with fs_lock:
        if not req.path or len(req.path.strip()) == 0:
            return {"status" : "FAILURE" , "message" : "Can not create a file of empty name"}
        status = fs.touch(req.path)
        if status == 6:
            return {"status" : "FAILURE" , "message" : "File already exist"}
        if status == 14:
            return {"status" : "FAILURE" , "message" : "File creation failed"}
        res_list = req.path.split("/")
        res_list.pop()
        return {"status" : "OK" , "result" : fs.get_contents("/".join(res_list))}

@app.post("/api/write_file_content/")
def write_file_content(req : fileContentRequest):
    with fs_lock:
        if (req.path and req.content ) and (len(req.path.strip()) != 0 and len(req.content.strip()) != 0):
            status = fs.write(req.content,req.path)
            if status == 5:
                return {"status": "FAILURE" , "message":"File not found"}
            return {"status" : "OK" , "message" : "success"}
        
@app.post("/api/remove_dir/")
def remove_dir(req : PathRequest):
    with fs_lock:
        if req.path and len(req.path.strip()) != 0:
            status = fs.remove_dir(req.path)

            if status == 9:
                return {"status" : "FAILURE" , "message" : "directory not found"}
            if status == 18:
                return {"status" : "FAILURE" , "message" : "Root directory can not be deleted"}
            res_list = req.path.split("/")
            res_list.pop()
            return {"status" : "OK" , "result" : fs.get_contents("/".join(res_list))}
@app.post("/api/remove_file/")
def remove_file(req : PathRequest):
    with fs_lock:
        if req.path and len(req.path.strip()) != 0:
            status = fs.rm(req.path)

            if status == 9:
                return {"status" : "FAILURE" , "message" : "directory not found"}
            if status == 5:
                return {"status" : "FAILURE" , "message" : "File not found"}
            res_list = req.path.split("/")
            res_list.pop()
            return {"status" : "OK" , "result" : fs.get_contents("/".join(res_list))}
@app.post("/api/move/")
def move(req : DoublePathRequest):
    with fs_lock:
        if (not req.src_path and not req.dest_path ) and (len(req.src_path.strip()) == 0 and len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "empty field"}
        status = fs.cut(req.src_path , req.dest_path)
        if status == 9:
            return {"status" : "FAILURE" , "message" : "Directory not found"}
        if status == 21:
            return {"status" : "FAILURE" , "message" : "Directory can not move to itself"}
        if status == 22:
            return {"status" : "FAILURE" , "message" : "It already exists so can not move"}
        return {"status" : "OK" , "result" : fs.get_contents(req.dest_path)}
@app.post("/api/copy/")
def copy(req : DoublePathRequest):
    with fs_lock:
        if (not req.src_path and not req.dest_path ) and (len(req.src_path.strip()) == 0 and len(req.dest_path.strip()) == 0 ):
            return {"status" : "FAILURE" , "message" : "empty field"}
        status = fs.cp(req.src_path , req.dest_path)
        if status == 9:
            return {"status" : "FAILURE" , "message" : "Directory not found"}
        if status == 25:
            return {"status" : "FAILURE" , "message" : "Directory can not copy to itself"}
        if status == 22:
            return {"status" : "FAILURE" , "message" : "It already exists so can not copy"}
        return {"status" : "OK" , "result" : fs.get_contents(req.dest_path)}

@app.post("/api/rename/")
def rename_item(req : itemRenameRequest):
    with fs_lock:
        if (not req.path and not req.new_name) and (len(req.path.strip()) == 0 and len(req.new_name.strip()) == 0):
            return {"status" : "FAILURE" , "message" : "empty field"}
        status = fs.rename(req.path, req.new_name)
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
        return {"status" : "OK" ,"result": fs.get_contents("/".join(res_list))}

@app.on_event("shutdown")
def shutdown():
    fs.close()