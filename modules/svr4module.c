/* python interface for a few svr4 system calls (not currently in os) */

/* $Header$ */


#include "Python.h"

#include <unistd.h>


/* these defines are needed if we're compiling under libc5 (ugh) */
#include <features.h>
#ifndef __GLIBC__
#define pid_t int
#endif


static PyObject *ErrorObject;

/* Set a POSIX-specific error from errno, and return NULL */
static PyObject *
posix_error()
{
  return PyErr_SetFromErrno(PyExc_OSError);
}


/* These really belong in the base Python libraries, but for now, it's getting
 * stuffed here.  (FIX)
 */

static char svr4_getpgid__doc__[] =
"getpgid(pid) -> pgid\n\
Get the process group id of the specified process.  If pid is 0, return the\
 pgid of the caller";

static PyObject *
svr4_getpgid(PyObject *self, PyObject *args)
{
  pid_t pid, pgid;

  if (!PyArg_Parse(args, "(i)", &pid))
    return NULL;
  
  pgid = getpgid(pid);

  if (pgid == -1)
    return posix_error();
  return Py_BuildValue("i", pgid);
}


static char svr4_fchdir__doc__[] =
"fchdir(fd) -> None\n\
Change the current working directory to directory opened as fd.";

static PyObject *
svr4_fchdir(PyObject *self, PyObject *args)
{
  int fd;
  long int result;

  if (!PyArg_Parse(args, "(i)", &fd))
    return NULL;
  
  result = fchdir(fd);

  if (result == -1)
    return posix_error();
  Py_INCREF(Py_None);
  return Py_None;
}


/* List of functions defined in the module */

static PyMethodDef svr4_methods[] = {
#define method(x) { #x, svr4_##x, METH_VARARGS, svr4_##x##__doc__ }
	method(getpgid),
	method(fchdir),
	{ NULL }		/* sentinel */
};


/* Initialization function for the module */

DL_EXPORT(void)
initsvr4()
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule("svr4", svr4_methods);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyErr_NewException("svr4.error", NULL, NULL);
  PyDict_SetItemString(d, "error", ErrorObject);
}
