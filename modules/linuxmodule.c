/* python interface for a few linux system calls (not currently in os) */

/* $Header$ */


#define _LARGEFILE64_SOURCE 1

#include "Python.h"

#include <unistd.h>
#include <linux/unistd.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>



static PyObject *ErrorObject;

/* Set a POSIX-specific error from errno, and return NULL */
static PyObject *
posix_error(void)
{
  return PyErr_SetFromErrno(PyExc_OSError);
}


/* These really belong in the base Python libraries, but for now, it's getting
 * stuffed here.  (FIX)
 */

static char linux_lseek__doc__[] =
"lseek(fd, offset, whence) -> new_offset\n\
Reposition file fd to the position specified by offset according to whence.\
  Returns the new position.  (Same as os.lseek except that it handles absolute\
 seeks >2^31 correctly.)";

/* This implementation is good enough for our purposes, on a 32-bit platform,
 * but it needs FIXing for other platforms.
 */

static PyObject *
linux_lseek(PyObject *self, PyObject *args)
{
  int fd, whence, offset;
  off64_t result;
  off64_t offset64;

  if (!PyArg_ParseTuple(args, "iii", &fd, &offset, &whence))
    return NULL;

  offset64 = (off64_t) offset;
  if (whence == 0 && offset < 0)
    offset64 = (off64_t) (unsigned int) offset;

  /* fprintf(stderr, "lseek: %llu\n", offset64); */

  result = lseek64(fd, offset64, whence);

  if (result == -1)
    return posix_error();
  return Py_BuildValue("l", (long) result);
}


/* List of functions defined in the module */

static PyMethodDef linux_methods[] = {
#define method(x) { #x, linux_##x, METH_VARARGS, linux_##x##__doc__ }
	method(lseek),
	{ NULL }		/* sentinel */
};


/* Initialization function for the module */

DL_EXPORT(void)
initlinux(void)
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule("linux", linux_methods);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyErr_NewException("linux.error", NULL, NULL);
  PyDict_SetItemString(d, "error", ErrorObject);
}
