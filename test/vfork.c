

#include <stdio.h>
#include <unistd.h>

char* args[] = { "/bin/sleep", "2", NULL };

int main(int argc, char *argv[]) {
  int pid;
  int result;

  if (pid = vfork())
    fprintf(stderr, "parent: I see kid with pid = %d\n", pid);
  else {
    sleep(5);
    result = execl("/bin/sh", "/bin/sh", "-c", "sleep 10; date", 0);
    fprintf(stderr, "result: %d\n", result);
    _exit(1);
  }
  
  sleep(5);
  fprintf(stderr, "parent exit\n");
}
