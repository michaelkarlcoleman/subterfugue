

#include <signal.h>
#include <stdio.h>
#include <unistd.h>

void handler(int i) {
  write(2, "handler\n", 8);
}

int main(int argc, char *argv[]) {
  int i=0;

  sigset_t ss;
  struct sigaction sa;

#if 0
  fprintf(stderr, "blocking SIGCONT\n");
  sigemptyset(&ss);
  sigaddset(&ss, SIGCONT);
  if (-1 == sigprocmask(SIG_BLOCK, &ss, 0))
    perror("block failed");
#endif

  fprintf(stderr, "handling SIGCONT\n");
  /* fprintf(stderr, "ignoring SIGCONT\n"); */
  sa.sa_handler = handler;
  /* sa.sa_handler = SIG_IGN; */
  sigemptyset(&sa.sa_mask);
  sa.sa_flags = 0;
  sigaction(SIGCONT, &sa, NULL);


  while (1) {
    i++;
    sleep(10);
    fprintf(stderr, "after pause %d\n", i);
  }
}
