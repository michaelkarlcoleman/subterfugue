

#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  int result;

  fprintf(stderr, "before exec\n");
  result = execl("/bin/asdfasdfasdf", "/bin/asdfasdfasdf", "first arg", 0);
  perror("badexec");
  fprintf(stderr, "after exec\n");
}
