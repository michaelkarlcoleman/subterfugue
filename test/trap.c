/* try blocking/ignoring SIGTRAP */

#include <signal.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  sigset_t ss;
  struct sigaction sa;

  fprintf(stderr, "starting\n");
  sleep(5);

  fprintf(stderr, "blocking SIGTRAP\n");
  sigemptyset(&ss);
  sigaddset(&ss, SIGTRAP);
  if (-1 == sigprocmask(SIG_BLOCK, &ss, 0))
    perror("block failed");
  sleep(5);

  fprintf(stderr, "unblocking SIGTRAP\n");
  if (-1 == sigprocmask(SIG_UNBLOCK, &ss, 0))
    perror("unblock failed");
  sleep(5);

  fprintf(stderr, "ignoring SIGTRAP\n");
  sa.sa_handler = SIG_IGN;
  sigemptyset(&sa.sa_mask);
  sa.sa_flags = 0;
  sigaction(SIGTRAP, &sa, NULL);
#if 0
  sleep(5);
#else
  pause();
#endif

  fprintf(stderr, "doing exec\n");

  fprintf(stderr, "before exec\n");
  execl("test/trapkid", "trapkid", 0);
  perror("badexec");
  fprintf(stderr, "after exec\n");
}
