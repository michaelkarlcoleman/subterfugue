

#include <signal.h>
#include <stdio.h>
#include <unistd.h>
#include <wait.h>

int main(int argc, char *argv[]) {
  int pid, wpid;
  int status;

  sigset_t ss;
  struct sigaction sa;

  if (pid = fork()) {
    while (!(wpid = wait4(pid, &status, 0, 0))) {
      fprintf(stderr, "parent: continuing to wait...\n");
      sleep(3);
    }
    if (wpid == pid) {
      fprintf(stderr, "parent: waited on kid\n");
      fprintf(stderr, "parent: status = 0x%x\n", status);
      if (WIFSIGNALED(status))
	fprintf(stderr, "parent: signaled with %d\n", WTERMSIG(status));
      else if (WIFEXITED(status))
	fprintf(stderr, "parent: exited with status %d\n",
		WEXITSTATUS(status));
      else if (WIFSTOPPED(status))
	fprintf(stderr, "parent: stopped with %d\n", WSTOPSIG(status));
      else
	fprintf(stderr, "parent: bad status\n");

      exit(0);
    } else {
      perror("wait4 failed");
      exit(1);
    }
  } else {
    fprintf(stderr, "child: I'm here\n");

#if 0
    fprintf(stderr, "blocking SIGTERM\n");
    sigemptyset(&ss);
    sigaddset(&ss, SIGTERM);
    if (-1 == sigprocmask(SIG_BLOCK, &ss, 0))
      perror("block failed");
#endif

    fprintf(stderr, "ignoring SIGTERM\n");
    sa.sa_handler = SIG_IGN;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGTERM, &sa, NULL);

    sleep(10);
    fprintf(stderr, "child: exiting\n");
    exit(7);
  }
}
