<script>
import fileImg from '@/assets/file-2127833_1920.png'
import dirImg from '@/assets/folder-2695046_1920.png'
import axios from 'axios';
export default {
  data() {
    return {
      fileImg,
      dirImg,
      
      items:[],
      path_arr:[],
      src_path : "",
      move_item : "",
      show_move_button : false,
      show_to_move_button : false,
      displayDirCreation:false,
      displayFileCreation : false,
      displayDirDeletion : false,
      displayFileDeletion : false,
      dirname : "",
      filename : "",
      activefile : "",
      fileContent : "",
      showEditor : false
    }
  },
  mounted : async function (){
    this.path_arr.push("root");
    const res = await this.get_dir_contents(this.path_arr[0]);
    if(res[0] === "FAILURE"){
        alert("Failed to load contents");
    }
    else{
      this.items = res[1];
    }
  },
  methods: {
    async item_on_click(item) {
       if(item.type === 'dir'){
          const res_list =  await this.get_dir_contents(this.path_arr.join("/") + `/${item.name}`);
          
          if(res_list[0] === "OK") {
            this.path_arr.push(item.name);
            this.items = res_list[1];
          }
          else {alert(res_list[1]);}
      }
      else{
        const res = await axios.post("http://localhost:8000/api/get_file_content/",
            {path : this.path_arr.join("/") + `/${item.name}`}
        );

        this.activefile = item.name;
        this.fileContent = res.data.content;
        this.showEditor = true;
      }
         
    }
    ,
    async get_dir_contents(dir_path){
       const res = await axios.post(`http://localhost:8000/api/get_dir_contents/`,
          {path : dir_path}
        );
        
        if(res.data.status === "FAILURE"){
            return [res.data.status, res.data.message];
        }
        else{
          this.items = res.data.result;
          return [res.data.status , res.data.result];
          
        }
    },
    async go_back(){
       const temp_path_arr = [...this.path_arr];
       if(temp_path_arr.length <= 1){
           alert("can not go back from root directory");
           return;
       }
       temp_path_arr.pop();

       const res_list = await this.get_dir_contents(temp_path_arr.join("/"))

       if(res_list[0] === "OK"){
          this.path_arr.pop();
          this.items = res_list[1];
          
       }
       else{
          alert(res_list[1]);
       }

    },
    async create_dir(){
        if(this.dirname.length !== 0){
            const res = await axios.post(`http://localhost:8000/api/mkdir/`,
              {path : this.path_arr.join("/") + `/${this.dirname}`}
            );
            if(res.data.status === "FAILURE"){
                alert(res.data.message);
                this.dirname = "";
            }
            else{
              this.items = res.data.result;
              this.dirname = ""
            }
        }
        else{
           alert("directory can not be created by an empty name");
        }
    },
    async create_file(){
      const res = await axios.post("http://localhost:8000/api/create_file/",{path : this.path_arr.join("/") + `/${this.filename}`});
      if(res.data.status === "FAILURE"){
        alert(res.data.message);
      }
      else{
        this.items = res.data.result;
      }
    },
    async saveFile(){
         const res =  await axios.post("http://localhost:8000/api/write_file_content/",{path : this.path_arr.join("/") + `/${this.activefile}`
         , content : this.fileContent})

         if(res.data.status === "FAILURE"){
             alert(res.data.message)
         }
    },
    async del_dir(){
      const res = await axios.post("http://localhost:8000/api/remove_dir/",
        {path : this.path_arr.join("/") + `/${this.dirname}`});
        if(res.data.status === "FAILURE"){
             alert(res.data.message);
        }
        else{
           this.items = res.data.result;
        }
    },
     async del_file(){
      const res = await axios.post("http://localhost:8000/api/remove_file/",
        {path : this.path_arr.join("/") + `/${this.filename}`});
        if(res.data.status === "FAILURE"){
             alert(res.data.message);
        }
        else{
           this.items = res.data.result;
           this.displayFileDeletion = false;
        }
    },
    async mv(){
        const s_path = this.src_path.split("/");
        const item = s_path[s_path.length-1];

        for(let i = this.path_arr.length-2 ; i >= 0; --i){
            if(item === this.path_arr[i]){
                 
                 alert("lllDirectory can not move it to itself");
                 return;
            }
        }

        const res = await axios.post("http://localhost:8000/api/move/",
          {src_path : this.src_path , dest_path : this.path_arr.join("/")}
        );
        console.log(this.src_path);
        console.log(this.path_arr.join("/"));
        this.show_move_button = false;
        this.move_item = "";
        if(res.data.status === "FAILURE"){
             alert(res.data.message);
        }
        else{
           this.items = res.data.result;
        }
    },
    save_to_src_path(){
         this.src_path = this.path_arr.join("/") + `/${this.move_item}`;
         this.show_move_button = true;
    },


  }
  
}
</script>

<template>
  <div class = "nav_bar">
      <h1>{{ path_arr[path_arr.length-1]}}</h1>
      <v-btn @click="go_back" color="primary" variant="outlined"><</v-btn>
    <v-btn @click = "displayDirCreation = !displayDirCreation">Create Directory</v-btn>
    <div v-if = "displayDirCreation">
       <input type="text" placeholder="Directory Name" v-model = "dirname">
       <v-btn @click = "create_dir">Create</v-btn>
    </div>

    <v-btn @click = "displayDirDeletion = !displayDirDeletion">Delete Directory</v-btn>
    <div v-if = "displayDirDeletion">
       <input type="text" placeholder="Directory Name" v-model = "dirname">
       <v-btn @click = "del_dir">Remove</v-btn>
    </div>
    <v-btn @click = "displayFileCreation = !displayFileCreation">Create File</v-btn>
    <div v-if = "displayFileCreation">
       <input type="text" placeholder="File Name" v-model = "filename">
       <v-btn @click = "create_file">Create</v-btn>
    </div>
     <v-btn @click = "displayFileDeletion = !displayFileDeletion">Delete File</v-btn>
    <div v-if = "displayFileDeletion">
       <input type="text" placeholder="File Name" v-model = "filename">
       <v-btn @click = "del_file">Remove</v-btn>
    </div>
    <v-btn @click = "show_to_move_button = !show_to_move_button">To move</v-btn>
    <div v-if = "show_to_move_button">
       <input type="text" placeholder="Item Name" v-model = "move_item">
       <v-btn @click = "save_to_src_path">To Move</v-btn>
    </div>
    <v-btn v-if = "show_move_button" @click = "mv">Move</v-btn>
  </div>
  
  <h1 v-if = "!items || items.length === 0" class = "dir_empty">directory is empty</h1>
     
     <v-container v-else>
    <v-row>
      <v-col cols="12" md="3" v-for = "item in items" :key = "item.name">
        <div @click = "item_on_click(item)" class = "icon">
             <img :src= "dirImg" alt="file img" width="80" v-if = "item.type === 'dir'"/>
             <img :src= "fileImg" alt="file img" width="80" v-if = "item.type === 'file'"/>
             <div>{{ item.name }}</div>
        </div>
      </v-col>
    </v-row>
  </v-container>
  <v-dialog v-model="showEditor" max-width="700">
  <v-card>
    <v-card-title>
      {{ activefile }}
    </v-card-title>

    <v-card-text>
      <v-textarea
        v-model="fileContent"
        rows="15"
        auto-grow
        outlined
        label="File content"
      />
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn color="primary" @click="saveFile">
        Save
      </v-btn>
      <v-btn color="error" @click="showEditor = !showEditor">
        Close
      </v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>

</template>

<style >
/* ===== Global layout ===== */
body {
  background: #f6f8fb;
}

/* ===== Top navigation bar ===== */
.nav_bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 10;
}

/* Current directory name */
.nav_bar h1 {
  margin-right: auto;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

/* ===== Buttons ===== */
.v-btn {
  margin: 0;
}

/* ===== Inline input blocks (create/delete) ===== */
.nav_bar > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===== Inputs ===== */
input[type="text"] {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  outline: none;
  min-width: 180px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

input[type="text"]:focus {
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.15);
}

/* ===== File grid container ===== */
.v-container {
  padding-top: 24px;
}

/* ===== File / Folder card ===== */
.icon {
  background: #ffffff;
  border-radius: 14px;
  padding: 18px 10px;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  user-select: none;
}

/* Hover & active feel */
.icon:hover {
  background: #e3f2fd;
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.icon:active {
  transform: translateY(-1px);
}

/* ===== File / Folder icons ===== */
.icon img {
  width: 64px;
  height: 64px;
  margin-bottom: 10px;
}

/* ===== File / Folder name ===== */
.icon div {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  word-break: break-word;
}

/* ===== Empty directory text ===== */
h1 {
  text-align: center;
  margin-top: 60px;
  color: #888;
  font-size: 18px;
  font-weight: 500;
}

/* ===== Editor dialog tweaks ===== */
.v-card-title {
  font-weight: 600;
  font-size: 18px;
}

.v-textarea textarea {
  font-family: "JetBrains Mono", monospace;
  font-size: 14px;
}
.dir_empty {
  margin: 120px auto 0;
  max-width: 420px;
  padding: 32px 24px;
  text-align: center;

  font-size: 20px;
  font-weight: 500;
  color: #6b7280; /* soft gray */

  background: #ffffff;
  border-radius: 16px;
  border: 1px dashed #d1d5db;

  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  letter-spacing: 0.3px;
}


</style>