/* try to write a string to each fd */

/* this program can be used to test that program output isn't getting
   unintentionally mixed in with sf output */


int main() {
  int i;
  
  char m[256] = "this is fd ";
  /*             012345678901 */

  for (i=0; i<256; i++) {
    sprintf(&m[11], "%.3d\n    ", i);
    write(i, m, 15);
  }
}
