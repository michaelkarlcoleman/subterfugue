

#include <stdio.h>

int main(int argc, char *argv[]) {
  int pid;

  if (pid = fork())
    fprintf(stderr, "parent: I see kid with pid = %d\n", pid);
  else
    fprintf(stderr, "child: I'm here\n");

  sleep(10);
}
