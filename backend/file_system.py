import ctypes
import json
lib = ctypes.CDLL("./fslib.so")

class FS(ctypes.Structure):
    pass

FS_p = ctypes.POINTER(FS)


lib.load_FS.argtypes = [ctypes.c_char_p]
lib.load_FS.restype = FS_p

lib.make_directory_in_a_directory.argtypes = [FS_p , ctypes.c_char_p]
lib.make_directory_in_a_directory.restype = ctypes.c_int

lib.delete_dir.argtypes = [FS_p , ctypes.c_char_p]
lib.delete_dir.restype = ctypes.c_int

lib.create_file.argtypes = [FS_p , ctypes.c_char_p]
lib.create_file.restype = ctypes.c_int

lib.write_file.argtypes = [FS_p , ctypes.c_char_p, ctypes.c_char_p]
lib.write_file.restype = ctypes.c_int

lib.remove_file.argtypes = [FS_p , ctypes.c_char_p]
lib.remove_file.restype = ctypes.c_int

lib.move.argtypes = [FS_p , ctypes.c_char_p, ctypes.c_char_p]
lib.move.restype = ctypes.c_int

lib.copy.argtypes = [FS_p , ctypes.c_char_p, ctypes.c_char_p]
lib.copy.restype = ctypes.c_int

lib.change_name.argtypes = [FS_p , ctypes.c_char_p , ctypes.c_char_p]
lib.change_name.restype = ctypes.c_int

lib.show_file_content.argtypes = [FS_p , ctypes.c_char_p]
lib.show_file_content.restype = ctypes.c_void_p

lib.delete_dir.argtypes = [FS_p , ctypes.c_char_p]
lib.delete_dir.restype = ctypes.c_int

lib.view_contents.argtypes = [FS_p,ctypes.c_char_p]
lib.view_contents.restype  = ctypes.POINTER(ctypes.c_char_p)

lib.destroy_FS.argtypes = [FS_p]
lib.destroy_FS.restype = None

lib.save_fs.argtypes = [FS_p , ctypes.c_char_p]
lib.save_fs.restype = ctypes.c_int

lib.FS_free.argtypes = [ctypes.c_void_p]
lib.FS_free.restype = None

lib.free_string_array.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
lib.free_string_array.restype = None

class File_System:
    def __init__(self, path : str):
        self.fs = lib.load_FS(path.encode())
        self.load_path = path
        pass
    def make_dir(self, path):
        return lib.make_directory_in_a_directory(self.fs,path.encode())
    def touch(self , path):
        return lib.create_file(self.fs , path.encode())
    def write(self , content , path):
        return lib.write_file(self.fs , content.encode(), path.encode())
    def rm(self , path):
        return lib.remove_file(self.fs, path.encode())
    def file_show(self , path):
        c_content = lib.show_file_content(self.fs, path.encode())
        if(c_content == None):
             return ""
        content = ctypes.string_at(c_content).decode()
        lib.FS_free(c_content)
        return content
   
    def remove_dir(self , path):
        return lib.delete_dir(self.fs , path.encode())
    def cut(self , src_path : str , dest_path : str):
        return lib.move(self.fs, src_path.encode() , dest_path.encode())
    def cp(self , src_path : str , dest_path : str):
        return lib.copy(self.fs , src_path.encode(), dest_path.encode())
    def rename(self , path : str , new_name : str):
        return lib.change_name(self.fs, path.encode(), new_name.encode())
    def get_contents(self,path):
        res = lib.view_contents(self.fs,path.encode())
        i = 0
        contents = []
        while res[i]:
            s = res[i].decode('utf-8')
            contents.append(json.loads(s))
            i += 1
            pass
        lib.free_string_array(res)
        return contents
    def save(self):
        lib.save_fs(self.fs , self.load_path.encode())
    def close(self):
        lib.save_fs(self.fs , self.load_path.encode())
        lib.destroy_FS(self.fs)
        self.fs = None
        pass
    pass
    