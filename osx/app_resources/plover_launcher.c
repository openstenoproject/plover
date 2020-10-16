#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <libgen.h>

#define ARGS_LIST_SIZE sizeof(arg_list) / sizeof(char*)

extern char **environ;
int main(int argc, char *argv[]) {

    // Relative path from this file.
    char python_path[] = "/../Frameworks/pythonexecutable";

    // Get this file's path.
    char path[1048];
    uint32_t size = sizeof(path);
    _NSGetExecutablePath(path, &size);

    // Remove filename from path.
    char * last_slash;
    last_slash = strrchr(path, '/');
    path[last_slash - path] = '\0';

    // Join file path and relative path to file.
    strcat(path, python_path);

    char* arg_list[] = { path, "-s", "-m", "plover.dist_main" };

    char **python_args = malloc((argc + ARGS_LIST_SIZE) * sizeof(char*));

    for (int i = 0; i < ARGS_LIST_SIZE; i++) {
      python_args[i] = arg_list[i];
    }
    for (int i = 1; i < argc; i++) {
      python_args[i + ARGS_LIST_SIZE - 1] = argv[i];
    }
    python_args[argc + ARGS_LIST_SIZE - 1] = NULL;

    execve(python_args[0], python_args, environ);
}
