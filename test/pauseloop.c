

#include <signal.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  int i=0;

  sigset_t ss;
  struct sigaction sa;

  fprintf(stderr, "ignoring SIGTRAP\n");
  sa.sa_handler = SIG_IGN;
  sigemptyset(&sa.sa_mask);
  sa.sa_flags = 0;
  sigaction(SIGTRAP, &sa, NULL);

  while (1) {
    i++;
    pause();
    fprintf(stderr, "after pause %d\n", i);
  }
}
