

#include <stdio.h>
#include <wait.h>

int main(int argc, char *argv[]) {
  int wpid;

  fprintf(stderr, "wait on init\n");
  while (!(wpid = wait4(1, 0, WNOHANG, 0)))
    sleep(2);
  if (wpid == 1)
    fprintf(stderr, "parent: waited on init\n");
  else
    perror("wait4 failed");
}
