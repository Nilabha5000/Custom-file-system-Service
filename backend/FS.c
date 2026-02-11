#include "FS.h"
#include "queue.h"
#include "obj_map.h"
#include "path.h"
#include <errno.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#define Dir 1
#define File 2
int is_modified = 0;
struct file{
    char *file_name;
    char content_buffer[MAX_CONTENT_LEN];
};
struct dir{
     struct obj_table *files;
     char *dir_name;
     struct obj_table *child;
     struct dir *parent;
};

struct FS{
    struct dir root_parent;
    struct dir *root;
    pthread_mutex_t lock;
};
void save_dir(struct dir *d, FILE *fp);
struct FS *initFS();
int belongs_to(struct dir *src_dir, struct path *p);
int is_descendant(struct dir *src , struct dir *dest);
struct file *clone_file(struct file *);
struct dir *clone_dir_tree(struct dir *);
struct dir *make_directory(const char *);

struct file *clone_file(struct file *f){
    if(!f) return NULL;
     
    struct file *new_file = (struct file*)malloc(sizeof(struct file));
    if(!new_file) return NULL;
    char *name = strdup(f->file_name);

    if(!name){
        free(new_file);
        return NULL;
    }
    name[strlen(name)] = '\0';
    new_file->file_name = name;

    strcpy(new_file->content_buffer, f->content_buffer);

    return new_file;
    
}

struct dir *clone_dir_tree(struct dir *root){

    if(!root) return NULL;

    struct queue *q1 = q_init();
    struct queue *q2 = q_init();
    int clonned_failed = 0; 
    struct dir *clone_root = make_directory(root->dir_name);
    if(clone_root == NULL){
          clonned_failed = 1;
          goto cleanup;
    }
    
    q_push(q1,root);
    q_push(q2,clone_root);
    while(!q_empty(q1) && !q_empty(q2)){
        struct dir *temp_dir = q_front(q1);
        struct dir *clonned_dir = q_front(q2);
        
        q_pop(q1);
        q_pop(q2);
       
        //clonning logic for files 
        struct bucket_list *file_iterartor = temp_dir->files->begin;
        for(; file_iterartor != NULL; file_iterartor = file_iterartor->next){
            struct bucket *file_bucktes = file_iterartor->start;

            for(; file_bucktes != NULL; file_bucktes = file_bucktes->next){
                 struct file *f = (struct file*)file_bucktes->value;
                 struct file *clonned_f = clone_file(f);
                if(clonned_f == NULL){
                    clonned_failed = 1;
                    goto cleanup;
                }
                if(clonned_dir->files == NULL){
                    clonned_failed = 1;
                    goto cleanup;
                }

                if(!insert_obj(clonned_dir->files,clonned_f->file_name,clonned_f)){
                    clonned_failed = 1;
                    goto cleanup;
                }

            }

        }
        
        struct bucket_list *dir_iterartor = temp_dir->child->begin;
        for(; dir_iterartor != NULL; dir_iterartor = dir_iterartor->next){
            struct bucket *dir_bucktes = dir_iterartor->start;

            for(; dir_bucktes != NULL; dir_bucktes = dir_bucktes->next){
                 struct dir *d = (struct dir*)dir_bucktes->value;
                 struct dir *clonned_d = make_directory(d->dir_name);
                if(clonned_d == NULL){
                    clonned_failed = 1;
                    goto cleanup;
                }
                if(clonned_dir->child == NULL){
                    clonned_failed = 1;
                    goto cleanup;
                }

                if(!insert_obj(clonned_dir->child,clonned_d->dir_name,clonned_d)){
                    clonned_failed = 1;
                    goto cleanup;
                }
                
                clonned_d->parent = clonned_dir;
                q_push(q1,d);
                q_push(q2,clonned_d);
            }

        }


    }
    cleanup:
    if(clonned_failed){
        delete_dir_tree(clone_root);
        clone_root = NULL;
    }
    q_destroy(q1);
    q_destroy(q2);
    return clone_root;
}
struct FS *initFS(){
     struct FS *fs = (struct FS*)malloc(sizeof(struct FS));
     if(fs == NULL) return NULL;
     fs->root = make_directory("root");
     if(fs->root == NULL) return NULL;
     fs->root_parent.child = create_table();
     fs->root_parent.files = NULL;
     insert_obj(fs->root_parent.child,fs->root->dir_name, fs->root);
     
     return fs;
}

struct dir *get_dest_dir(struct FS *fs, struct path *p){

     struct dir *dest_dir = &fs->root_parent;
      for(struct path_node *i = p->begin; i != p->end; i = i->next){
          dest_dir = (struct dir*)get_obj(dest_dir->child,i->name);
          if(dest_dir == NULL){
               return NULL;
          }
      }
     return dest_dir;
}
char *get_slashed_path(const char *path){
      char *slash_path = (char*)malloc(strlen(path)+2);
      if(path[0] != '/'){
          slash_path[0] = '/';
          strcpy(slash_path+1,path);
      }
      else{
          strcpy(slash_path,path);
      }
      slash_path[strlen(slash_path)] = '\0';
     return slash_path;
}
struct dir *make_directory(const char *dir_name){
    struct dir *d = (struct dir*)malloc(sizeof(struct dir));
    if(d == NULL) return NULL;
    d->dir_name = (char*)malloc(strlen(dir_name)+2);
    if(d->dir_name == NULL){
        free(d);
        return NULL;
    }
    int start_from = 0;
    if(dir_name[0] != '/'){
        d->dir_name[0] = '/';
        d->dir_name[1] = '\0';
        start_from = 1;
    }
    strcpy(d->dir_name+start_from , dir_name);
    d->child = create_table();
    if(d->child == NULL){
         free(d->dir_name);
         free(d);
         return NULL;
    }
    // initailizing all file as NULL means no file
      d->files = create_table();
     if(d->files == NULL){
         free(d->dir_name);
         d->dir_name = NULL;
         destroy_obj_table(d->child);
         free(d);
         return NULL;
     }
     d->parent = NULL;
    return d;
}

void FS_free(void *ptr){
     if(ptr == NULL) return;
     free(ptr);
}
void free_string_array(char **arr) {
    if (!arr) return;
    for (int i = 0; arr[i]; i++) {
        free(arr[i]);
    }
    free(arr);
}

FS_ERROR create_file(struct FS *fs , const char *file_path){
     if(fs == NULL){
           return FS_FAILED;
     }
       char *slash_file_path = get_slashed_path(file_path);
      struct path *p = get_path(slash_file_path);
      free(slash_file_path);
      if(p == NULL){
          return PATH_FAILED;
      }
      //this is reash destination dir where to create file
      struct dir *dest_dir = get_dest_dir(fs,p);
      if(dest_dir == NULL){
          path_destroy(p);
          return 0;
      }
      char *filename = strdup(p->end->name);
      int start_from = 0;
      if(filename[0] == '/'){start_from = 1;}
      if(get_obj(dest_dir->files,filename+start_from)){
          path_destroy(p);
          free(filename);
          return FILE_ALREADY_EXISTS;
      }
      
      
      // Allocate memory for the new file.
      struct file *newfile = (struct file*)malloc(sizeof(struct file));
      // Check if memory allocation was successful
      if(newfile == NULL) {
           return FILE_MEMORY_ALLOCATION_FAILED;
      }
      
      newfile->file_name = (char*)malloc(strlen(filename)+1);
      // Copy the file name into the directory's files array
      strcpy(newfile->file_name, filename+start_from);
      //setting the content buffer with 0.
      memset(newfile->content_buffer , 0 , MAX_CONTENT_LEN);
     //check if the file insertion failed then free the memory of file and filename
     if(!insert_obj(dest_dir->files,filename + start_from, newfile)){
          free(newfile->file_name);
          free(newfile);
          free(filename);
          path_destroy(p);
          return FILE_CREATION_FAILED;
     }

     free(filename);
     path_destroy(p);
     is_modified = 1;
     return FILE_OK;
}

FS_ERROR remove_file(struct FS *fs , const char *file_path){
     if(fs == NULL){
           return FS_FAILED;
     }
      char *slash_file_path = get_slashed_path(file_path);
      struct path *p = get_path(slash_file_path);
      free(slash_file_path);
      if(p == NULL){
          return PATH_FAILED;
      }
      //this is reash destination dir where to create file
      struct dir *dest_dir = get_dest_dir(fs,p);
      if(dest_dir == NULL)
      {
          path_destroy(p);
          return DIR_NOT_FOUND;
      }
     char *filename = strdup(p->end->name);
     int start_from = 0;
     if(filename[0] == '/')
       start_from = 1;
     //search for a filename 
     struct file *getfile = (struct file*)del_obj(dest_dir->files,filename + start_from);
     free(filename);
     if(getfile == NULL){
          return FILE_NOT_FOUND;
     }
     
     free(getfile->file_name);
     free(getfile);
     path_destroy(p);
     is_modified = 1;
     return FILE_OK;
}

FS_ERROR write_file(struct FS *fs , const char *content , const char *file_path){
     if(fs == NULL){
          return FS_FAILED;
     }
     char *slash_file_path = get_slashed_path(file_path);
      struct path *p = get_path(slash_file_path);
      free(slash_file_path);
      if(p == NULL){
          
          return PATH_FAILED;
      }
      //this is reash destination dir where to create file
      struct dir *dest_dir = get_dest_dir(fs,p);
      if(dest_dir == NULL){
          path_destroy(p);
          return DIR_NOT_FOUND;
      }
     char *filename = strdup(p->end->name);
     int start_from = 0;
     if(filename[0] == '/')
       start_from = 1;
     //search for file with a given filename in the current directory.
     struct file *getfile = (struct file*)get_obj(dest_dir->files,filename + start_from);
     free(filename);

     if(getfile == NULL){
          path_destroy(p);
          return FILE_NOT_FOUND;
     }
     path_destroy(p);
     strncpy(getfile->content_buffer,content,MAX_CONTENT_LEN-1);
     is_modified = 1;
     return FILE_OK;
}

char * show_file_content(struct FS *fs , const char *file_path){
     if(fs == NULL){
          return NULL;
     }

     //search for file with a given filename in the current directory.
      char *slash_file_path = get_slashed_path(file_path);
      struct path *p = get_path(slash_file_path);
      free(slash_file_path);
      if(p == NULL){
          return NULL;
      }
      //this is reash destination dir where to create file
      struct dir *dest_dir = get_dest_dir(fs,p);
      if(dest_dir == NULL){
          path_destroy(p);
          return NULL;
      }
      char *filename = strdup(p->end->name);
      int start_from = 0;
     if(filename[0] == '/')
       start_from = 1;
     path_destroy(p);
     struct file *getfile = (struct file*)get_obj(dest_dir->files,filename + start_from);
     free(filename);
     if(getfile == NULL){
          return NULL;
     }
     int n = 0;
     if((n = strlen(getfile->content_buffer)) == 0) return NULL;
     
     char *content = (char*)malloc(n+1);
     strcpy(content,getfile->content_buffer);
     content[n] = '\0';

     return content;

}

FS_ERROR make_directory_in_a_directory(struct FS *fs , const char *dir_path){
     if(fs == NULL){
           return FS_FAILED;
     }
     // Check if the directory name is valid
     if(dir_path == NULL || strlen(dir_path) == 0){
          return INVALID_DIR_NAME;
     }
        
     char *slashed_dir_path = get_slashed_path(dir_path);
     
     struct path *p = get_path(slashed_dir_path);
     free(slashed_dir_path);
     if(p == NULL){
          return PATH_FAILED;
     }

     struct dir *dest_dir = get_dest_dir(fs,p);
     if(dest_dir == NULL){
          path_destroy(p);
          return DIR_NOT_FOUND;
     }
     //check for if current directory has a directory of dir_name.
     if(get_obj(dest_dir->child,p->end->name)){
          path_destroy(p);
          return DIR_ALREADY_EXISTS;
     }

     struct dir *new_dir = make_directory(p->end->name);
     if(dest_dir->child == NULL || new_dir == NULL){
          path_destroy(p);
          return DIR_MEMORY_ALLOCATION_FAILED;
     }
     new_dir->parent = dest_dir;
     insert_obj(dest_dir->child,new_dir->dir_name,new_dir);

     path_destroy(p);
     is_modified = 1;
     return DIR_OK;
}
//It returns an Int.
//Returns 1 when dest is a dencendent of src.
//Returns 0 when dest is not a decendent of src.
int is_descendant(struct dir *src , struct dir *dest){
     
     if (!src || !dest) return 0;

    struct dir *curr = dest;

    while (curr)
    {
        if (curr == src)
            return 1;

        // protection against corrupted parent loop
        if (curr == curr->parent)
            break;

        curr = curr->parent;
    }

    return 0;
}
//It returns an int that tells the path belongs to a file or a directory.
//returns 1 when it belongs to directory.
//returns 2 when it belongs to file.
//returns 0 when it belongs to nothing.
int belongs_to(struct dir *src_dir , struct path *p){
        
     if(get_obj(src_dir->child,p->end->name) != NULL)
         return Dir;
     if(get_obj(src_dir->files, p->end->name+1) != NULL)
        return File;
     return 0;
}
FS_ERROR move(struct FS *fs,
              const char *src_path,
              const char *dest_path)
{
    if (!fs || !src_path || !dest_path)
        return FS_FAILED;

    FS_ERROR ret = MOVE_FAILED;

    struct path *src = NULL;
    struct path *dest = NULL;

    char *s_src = get_slashed_path(src_path);
    char *s_dest = get_slashed_path(dest_path);

    if (!s_src || !s_dest)
        goto cleanup;

    src = get_path(s_src);
    dest = get_path(s_dest);

    if (!src || !dest)
        goto cleanup;

    /* Get parent directories */
    struct dir *src_parent = get_dest_dir(fs, src);
    struct dir *dest_parent = get_dest_dir(fs, dest);

    if (!src_parent || !dest_parent)
    {
        ret = DIR_NOT_FOUND;
        goto cleanup;
    }

    /* Final destination dir */
    struct dir *dest_dir =
        (struct dir *)get_obj(dest_parent->child,
                              dest->end->name);

    if (!dest_dir)
    {
        ret = DIR_NOT_FOUND;
        goto cleanup;
    }

    /* What are we moving? */
    int type = belongs_to(src_parent, src);

    /* ========== MOVE DIRECTORY ========== */

    if (type == Dir)
    {
        struct dir *src_dir =
            (struct dir *)get_obj(src_parent->child,
                                  src->end->name);

        if (!src_dir)
        {
            ret = DIR_NOT_FOUND;
            goto cleanup;
        }

        /* Prevent self / descendant move */
        if (is_descendant(src_dir, dest_dir))
        {
            ret = CANNOT_MOVE_TO_IT_SELF;
            goto cleanup;
        }

        /* Check overwrite */
        if (get_obj(dest_dir->child, src_dir->dir_name))
        {
            ret = DEST_ALREADY_EXISTS;
            goto cleanup;
        }

        /* Detach */
        del_obj(src_parent->child, src->end->name);

        /* Attach */
        if (!insert_obj(dest_dir->child,
                        src_dir->dir_name,
                        src_dir))
        {
            /* rollback */
            insert_obj(src_parent->child,
                       src_dir->dir_name,
                       src_dir);

            ret = MOVE_FAILED;
            goto cleanup;
        }

        /* Fix parent */
        src_dir->parent = dest_dir;

        ret = MOVE_OK;
        is_modified = 1;
        goto cleanup;
    }

    /* ========== MOVE FILE ========== */

    if (type == File)
    {
        struct file *f =
            (struct file *)get_obj(src_parent->files,
                                   src->end->name + 1);

        if (!f)
        {
            ret = FILE_NOT_FOUND;
            goto cleanup;
        }

        if (get_obj(dest_dir->files, f->file_name))
        {
            ret = DEST_ALREADY_EXISTS;
            goto cleanup;
        }

        /* Detach */
        del_obj(src_parent->files, src->end->name + 1);

        /* Attach */
        if (!insert_obj(dest_dir->files,
                        f->file_name,
                        f))
        {
            /* rollback */
            insert_obj(src_parent->files,
                       f->file_name,
                       f);

            ret = MOVE_FAILED;
            goto cleanup;
        }

        ret = MOVE_OK;
        is_modified = 1;
        goto cleanup;
    }

    ret = MOVE_FAILED;

cleanup:

    if (s_src) free(s_src);
    if (s_dest) free(s_dest);

    if (src) path_destroy(src);
    if (dest) path_destroy(dest);
    
    return ret;
}

FS_ERROR copy(struct FS *fs,
              const char *src_path,
              const char *dest_path)
{
    if (!fs || !src_path || !dest_path)
        return FS_FAILED;

    FS_ERROR ret = COPY_FAILED;

    struct path *src = NULL;
    struct path *dest = NULL;

    char *s_src = get_slashed_path(src_path);
    char *s_dest = get_slashed_path(dest_path);

    if (!s_src || !s_dest)
        goto cleanup;

    src = get_path(s_src);
    dest = get_path(s_dest);

    if (!src || !dest)
        goto cleanup;

    /* Get parent directories */
    struct dir *src_parent = get_dest_dir(fs, src);
    struct dir *dest_parent = get_dest_dir(fs, dest);

    if (!src_parent || !dest_parent)
    {
        ret = DIR_NOT_FOUND;
        goto cleanup;
    }

    /* Final destination dir */
    struct dir *dest_dir =
        (struct dir *)get_obj(dest_parent->child,
                              dest->end->name);

    if (!dest_dir)
    {
        ret = DIR_NOT_FOUND;
        goto cleanup;
    }

    /* What are we moving? */
    int type = belongs_to(src_parent, src);

    /* ========== COPY DIRECTORY ========== */

    if (type == Dir)
    {
        struct dir *src_dir =
            (struct dir *)get_obj(src_parent->child,
                                  src->end->name);

        if (!src_dir)
        {
            ret = DIR_NOT_FOUND;
            goto cleanup;
        }

        /* Prevent self / descendant copy */
        if (is_descendant(src_dir, dest_dir))
        {
            ret = CANNOT_COPY_TO_IT_SELF;
            goto cleanup;
        }

        /* Check overwrite */
        if (get_obj(dest_dir->child, src_dir->dir_name))
        {
            ret = DEST_ALREADY_EXISTS;
            goto cleanup;
        }

        
        struct dir *clonned_src_dir = clone_dir_tree(src_dir);
        if(clonned_src_dir == NULL){
            ret = COPY_FAILED;
            goto cleanup;
        }
        /* Attach */
        if (!insert_obj(dest_dir->child,
                        clonned_src_dir->dir_name,
                        clonned_src_dir))
        {

            ret = COPY_FAILED;
            goto cleanup;
        }

        /* Fix parent */
        clonned_src_dir->parent = dest_dir;

        ret = COPY_OK;
        is_modified = 1;
        goto cleanup;
    }

    /* ========== COPY FILE ========== */

    if (type == File)
    {
        struct file *f =
            (struct file *)get_obj(src_parent->files,
                                   src->end->name + 1);

        if (!f)
        {
            ret = FILE_NOT_FOUND;
            goto cleanup;
        }

        if (get_obj(dest_dir->files, f->file_name))
        {
            ret = DEST_ALREADY_EXISTS;
            goto cleanup;
        }

        struct file *clonned_f = clone_file(f);
        if(clonned_f == NULL){
            ret = COPY_FAILED;
            goto cleanup;
        }

        /* Attach */
        if (!insert_obj(dest_dir->files,
                        clonned_f->file_name,
                        clonned_f))
        {
            ret = COPY_FAILED;
            goto cleanup;
        }

        ret = COPY_OK;
        is_modified = 1;
        goto cleanup;
    }

    ret = COPY_FAILED;

cleanup:

    if (s_src) free(s_src);
    if (s_dest) free(s_dest);

    if (src) path_destroy(src);
    if (dest) path_destroy(dest);

    return ret;
}
FS_ERROR change_name(struct FS *fs , const char *path , const char *new_name){
    if(fs == NULL)
      return FS_FAILED;
    
    char *slash_path = get_slashed_path(path);
    if(slash_path == NULL)
        return PATH_FAILED;
   
    struct path *p = get_path(slash_path);
    free(slash_path);
    if(p == NULL)
      return PATH_FAILED;
    
    struct dir *dest_parent = get_dest_dir(fs,p);
    if(dest_parent == NULL)
    {
        path_destroy(p);
        return PATH_FAILED;
    }

    int type = belongs_to(dest_parent , p);
    FS_ERROR ret = ITEM_IS_NOT_FILE_OR_DIR;
    if(type == Dir){
         struct dir *dest = (struct dir *)get_obj(dest_parent->child,p->end->name);

        if(dest == NULL){
            ret = DIR_NOT_FOUND;
            goto cleanup;
        }

        int len = strlen(new_name)+2;
        int start_with = 0;
        char *s_new_name = malloc(len);
        
        if(new_name[0] != '/'){
            s_new_name[0] = '/';
            start_with = 1;
        }
        strcpy(s_new_name + start_with , new_name);
        s_new_name[strlen(s_new_name)] = '\0';
        if(get_obj(dest_parent->child,s_new_name) != NULL){
            ret = DIR_ALREADY_EXISTS;
            free(s_new_name);
            goto cleanup;
        }
        del_obj(dest_parent->child, p->end->name);
        free(dest->dir_name);
        dest->dir_name = s_new_name;
        
        insert_obj(dest_parent->child,dest->dir_name, dest);

        ret = DIR_OK;
        is_modified = 1;
    }
    else if(type == File){
        struct file *dest_file = (struct file *)get_obj(dest_parent->files,p->end->name+1);

        if(dest_file == NULL){
            ret = FILE_NOT_FOUND;
            goto cleanup;
        }
        if(get_obj(dest_parent->files,new_name) != NULL){
            ret = FILE_ALREADY_EXISTS;
            goto cleanup;
        }
        del_obj(dest_parent->files,p->end->name+1);
        free(dest_file->file_name);
        dest_file->file_name = strdup(new_name);
        dest_file->file_name[strlen(dest_file->file_name)] = '\0';
        
        insert_obj(dest_parent->files, dest_file->file_name, dest_file);
        ret = FILE_OK;
        is_modified = 1;
    }
    cleanup:
    path_destroy(p);

    return ret;
}
void delete_dir_tree(struct dir *root){
       if(root == NULL){
           return;
       }
       if(root->child == NULL) return;
       struct queue *q = q_init();
       q_push(q,root);
       while(!q_empty(q)){
          struct dir *temp = q_front(q);
          q_pop(q);
          if(temp->child){
               for(struct bucket_list *i = temp->child->begin; i != NULL; i = i->next){
                  struct bucket *curr = i->start;
                  while(curr){
                      q_push(q,(struct dir*)curr->value);
                      curr = curr->next;
                  }
               }
          }
          
            free(temp->dir_name);
            temp->dir_name = NULL;
            for(struct bucket_list* i = temp->files->begin; i != NULL; i = i->next){
                  struct bucket *curr1 = i->start;
                  while(curr1){
                     struct file *getfile = (struct file*)curr1->value;
                     free(getfile->file_name);
                     free(getfile);
                    curr1 = curr1->next;
                  }
                  
            }
            destroy_obj_table(temp->child);
            destroy_obj_table(temp->files);
            free(temp);
       }
       
       q_destroy(q);
}

FS_ERROR delete_dir(struct FS *fs , char *dir_path){
     if(fs == NULL){
         return FS_FAILED;
     }
     // check if the directory name is valid
     if(dir_path == NULL || strlen(dir_path) == 0){
        return INVALID_DIR_NAME;
     }
     char *slashed_dir_path = get_slashed_path(dir_path);

     struct path *p = get_path(slashed_dir_path);
     free(slashed_dir_path);
     if(p == NULL){
          return PATH_FAILED;
     }
     // search for the directory name
     struct dir *dest_dir = get_dest_dir(fs,p);
     if(dest_dir == NULL ){
          path_destroy(p);
          return DIR_NOT_FOUND;
     }
     if(dest_dir == &fs->root_parent){
          path_destroy(p);
          return DELETING_ROOT_DIR_ERROR;
     }
     struct dir *recieved_dir = (struct dir*)del_obj(dest_dir->child,p->end->name);

     if(recieved_dir == NULL){
           path_destroy(p);
           return DIR_NOT_FOUND;
     }
     delete_dir_tree(recieved_dir);
     path_destroy(p);
     is_modified = 1;
     return DIR_OK;
}
char** view_contents(struct FS *fs , const char *dir_path){
     if(fs == NULL){
          char **res = (char**)calloc(1,sizeof(char*));
          res[0] = NULL;
          return res;
     }
     char *slashed_path = get_slashed_path(dir_path);
     struct path *p = get_path(slashed_path);
     struct dir *dest_dir = get_dest_dir(fs,p);
     if(dest_dir == NULL){
           char **res = (char**)calloc(1,sizeof(char*));
           res[0] = NULL;
           return res;
     }
     struct dir *final_dir = (struct dir*)get_obj(dest_dir->child,p->end->name);
      if(final_dir == NULL){
          char **res = (char**)calloc(1,sizeof(char*));
          res[0] = NULL;
           return res;
     }
      dest_dir = (struct dir*)get_obj(dest_dir->child,p->end->name);
      int jsons_size = dest_dir->child->count + dest_dir->files->count;
      int json_index = 0;
      char **json_res = (char**)calloc(jsons_size+1, sizeof(char*));
      json_res[jsons_size] = NULL;

     //first showing all the directories in current directory;
     for(struct bucket_list* i = dest_dir->child->begin; i != NULL; i = i->next){
          struct bucket *node1 = i->start;
          while(node1){
               struct dir *d = (struct dir*)node1->value;
               int len = snprintf(NULL, 0,"{\"name\":\"%s\",\"type\":\"dir\"}",d->dir_name+1);
               json_res[json_index] = (char*)malloc(len+1);
               snprintf(json_res[json_index], len+1,"{\"name\":\"%s\",\"type\":\"dir\"}",d->dir_name+1);
               json_index++;
               node1 = node1->next;
          }
         
     }
     //first showing all the files in current directory;
     for(struct bucket_list* i = dest_dir->files->begin; i != NULL; i = i->next){
          struct bucket *node2 = i->start;
          while(node2){
               struct file *f = (struct file*)node2->value;
               int len = snprintf(NULL, 0,"{\"name\":\"%s\",\"type\":\"file\"}",f->file_name);
               json_res[json_index] = (char*)malloc(len+1);
               snprintf(json_res[json_index], len+1,"{\"name\":\"%s\",\"type\":\"file\"}",f->file_name);
               json_index++;
               node2 = node2->next;
          }
         
     }

     return json_res;
}

void destroy_FS(struct FS *fs){
     if(fs == NULL){
         return;
     }
    destroy_obj_table(fs->root_parent.child);
    delete_dir_tree(fs->root);
    free(fs);

}

int save_fs(struct FS *fs , const char *filename){
     if(!is_modified) return 0;
     FILE *fp = fopen(filename, "wb");
     if(!fp) return 0;
     
     save_dir(fs->root,fp);
     fclose(fp);
     is_modified = 0;
     return 1;
}
void save_dir(struct dir *d , FILE *fp){
       
     int n = strlen(d->dir_name);
     fwrite(&n,sizeof(n), 1 , fp);
     fwrite(d->dir_name,1,n,fp);
     
     int file_count = d->files->count;
     fwrite(&file_count,sizeof(file_count), 1 , fp);
     for(struct bucket_list *i = d->files->begin; i != NULL; i = i->next){
          struct bucket *b = i->start;
          while(b != NULL){
               struct file *f = (struct file *)b->value;
               int file_name_len = strlen(f->file_name);
               fwrite(&file_name_len, sizeof(file_name_len), 1 , fp);
               fwrite(f->file_name,1,file_name_len,fp);

               int content_len = strlen(f->content_buffer);
               fwrite(&content_len,sizeof(content_len), 1 , fp);
               fwrite(f->content_buffer, 1 , content_len, fp);
               b = b->next;
          }
          
     }
     int dir_count = d->child->count;
     fwrite(&dir_count,sizeof(dir_count), 1 , fp);
      for(struct bucket_list *i = d->child->begin; i != NULL; i = i->next){
          struct bucket *b = i->start;
          while(b != NULL){
               struct dir *directory = (struct dir *)b->value;
               save_dir(directory,fp);
               b = b->next;
          }
          
     }

}
struct dir *create_fs_tree(FILE *fp){
     int len;
    fread(&len, sizeof(len), 1, fp);

    char *name = malloc(len + 1);
    fread(name, 1, len, fp);
    name[len] = '\0';

    struct dir *d = make_directory(name);
    free(name);

    int file_count;
    fread(&file_count, sizeof(file_count), 1, fp);
    //retriving all the files and its content 
    for(int i = 0; i < file_count; i++){
        //recreating a file of file name and file content
        struct file *f = (struct file *)malloc(sizeof(struct file));
        int file_name_len;
        fread(&file_name_len,sizeof(file_name_len), 1 , fp);
        f->file_name = (char*)malloc(file_name_len + 1);
        memset(f->file_name , 0,file_name_len);
        fread(f->file_name,1,file_name_len,fp);
        f->file_name[file_name_len] = '\0';
       // retriving the file content 
       int content_len;
       fread(&content_len,sizeof(content_len), 1, fp);
       memset(f->content_buffer, 0 , MAX_CONTENT_LEN);
       fread(f->content_buffer,1,content_len,fp);
       f->content_buffer[content_len] = '\0';
       //inserting the file in a hash_map.
       insert_obj(d->files,f->file_name,f);

    }

    int dir_count;
    fread(&dir_count, sizeof(dir_count), 1, fp);

    for(int i = 0; i < dir_count; i++){
        struct dir *child = create_fs_tree(fp);
        insert_obj(d->child, child->dir_name, child);
    }

    return d;
}
struct FS *load_FS(const char *filename){
    struct FS *fs = initFS();
    FILE *fp = fopen(filename , "rb");
    if(!fp) return fs;
    
    delete_dir_tree(fs->root);
    destroy_obj_table(fs->root_parent.child);
    fs->root = create_fs_tree(fp);
    fs->root_parent.child = create_table();
    insert_obj(fs->root_parent.child , fs->root->dir_name, fs->root);
    fclose(fp);
    pthread_mutex_init(&fs->lock, NULL);
    return fs;
}

