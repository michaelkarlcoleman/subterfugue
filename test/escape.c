#include <stdio.h>

void
main(void)
{
  FILE *f;
  char buf[4096];

  printf( "%d\n", munmap(0x3f000000, 0x10000));
  f = fopen( "/proc/self/maps", "r" );
  while (fgets(buf, 4000, f))
    printf( "%s", buf);

}
