

#include <stdio.h>
#include <sys/wait.h>

int main(int argc, char *argv[]) {
  int pid, wpid, status, i;

  for (i=0; i<10; i++)
    if (pid = fork()) {
      fprintf(stderr, "parent: I see kid with pid = %d\n", pid);
      continue;
    } else {
      fprintf(stderr, "child: %d here\n", getpid());
      sleep(10);
      exit(i);
    }

  /* parent here */
  while (-1 != (wpid = wait4(-1, &status, 0, 0))) {
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
    i--;
  }

  perror("wait4 failed");
  exit(i);
}
