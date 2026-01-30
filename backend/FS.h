#ifndef FS_H
#define FS_H

#include <stdio.h>
#include <stdlib.h>
#include "fs_error.h"
// Define maximum number of files and directories in a directory
#define MAX_CONTENT_LEN 4007
struct stack;
typedef struct file file;
typedef struct dir dir;
typedef struct  FS FS;
void FS_free(void *);
void free_string_array(char **);
struct FS *load_FS(const char *);
FS_ERROR make_directory_in_a_directory(struct FS* , const char *);
FS_ERROR create_file(struct FS * , const char *);
FS_ERROR write_file(struct FS * , const char *, const char *);
FS_ERROR remove_file(struct FS * , const char *);
FS_ERROR move(struct FS * , const char * , const char *);
char* show_file_content(struct FS *, const char *);
void delete_dir_tree(struct dir *);
FS_ERROR delete_dir(struct FS *, char *);
char** view_contents(struct FS * , const char *);
void destroy_FS(struct FS *);

int save_fs(struct FS * , const char *);

#endif
