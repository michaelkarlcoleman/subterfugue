
#include <stdio.h>

int main(int argc, char *argv[]) {
  fprintf(stderr, "pid is %d\n", getpid());
  sleep(60);
}
