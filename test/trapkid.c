/* child for trap */

#include <signal.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  sigset_t ss;
  struct sigaction sa;

  fprintf(stderr, "starting kid\n");
  sleep(5);

#if 0
  fprintf(stderr, "ignoring SIGTRAP\n");
  sa.sa_handler = SIG_IGN;
  sigemptyset(&sa.sa_mask);
  sa.sa_flags = 0;
  sigaction(SIGTRAP, &sa, NULL);
  sleep(5);
#endif

  fprintf(stderr, "unblocking SIGTRAP\n");
  sigemptyset(&ss);
  sigaddset(&ss, SIGTRAP);
  if (-1 == sigprocmask(SIG_UNBLOCK, &ss, 0))
    perror("block failed");
  sleep(5);

  fprintf(stderr, "kid exiting\n");
}
