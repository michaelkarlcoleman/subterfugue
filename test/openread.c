

#include <fcntl.h>

int main() {
  open("/etc/passwd", O_RDONLY);
}
