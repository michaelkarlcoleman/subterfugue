/* clone with CLONE_PARENT */

#include <sched.h>
#include <stdio.h>
#include <stdlib.h>

#ifndef CLONE_PARENT
#define CLONE_PARENT    0x00008000      /* set if we want to have the same paren
t as the cloner */
#endif


int kidfunc(void *arg) {
  fprintf(stderr, "child\n");
  sleep(12);
  fprintf(stderr, "child done\n");
}


int main() {
  void *kidstack = malloc(2 * 1024 * 1024);

  int kid;
  if (kid = __clone(kidfunc, kidstack, CLONE_PARENT, 0)) {
    fprintf(stderr, "parent (child is %d)\n", kid);
    sleep(5);
  }

  fprintf(stderr, "parent done\n");
}
