#include <libgen.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    char python_path[PATH_MAX];
    char *new_argv[4 + argc];
    char *app_dir;

    // Get this app bundle directory.
    app_dir = realpath(argv[0], NULL);
    app_dir = dirname(dirname(app_dir));

    // Get path to the Python interpreter.
    snprintf(
      python_path, sizeof (python_path),
      "%s/Frameworks/Python.framework/Versions/Current/bin/python",
      app_dir
    );

    // Build new arguments list, forwarding original arguments.
    new_argv[0] = python_path;
    new_argv[1] = "-s";
    new_argv[2] = "-m";
    new_argv[3] = "plover.scripts.dist_main";
    memcpy(new_argv + 4, argv + 1, argc * sizeof (argv[0]));

    return execv(new_argv[0], new_argv);
}
