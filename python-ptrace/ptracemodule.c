/* python interface to the linux ptrace system call */

/* $Header */


#include <sys/ptrace.h>

#ifndef PTRACE_GETPPID
#define PTRACE_GETPPID 20
#endif

#include "Python.h"

static PyObject *ErrorObject;

/* Set a POSIX-specific error from errno, and return NULL */
static PyObject *
posix_error()
{
  return PyErr_SetFromErrno(PyExc_OSError);
}


static char ptrace_traceme__doc__[] =
"traceme() -> None\n\
Indicate that this process is to be traced by its parent.";

static PyObject *
ptrace_traceme(PyObject *self, PyObject *args)
{
  long int result;

  if (!PyArg_ParseTuple(args, ""))
    return NULL;
  
  result = ptrace(PTRACE_TRACEME, 0, 0, 0);

  if (result == -1)
    return posix_error();
  Py_INCREF(Py_None);
  return Py_None;
}


static inline PyObject *
peek(int request, PyObject *self, PyObject *args)
{
  pid_t pid;
  long int addr, result;

  if (!PyArg_Parse(args, "(il)", &pid, &addr))
    return NULL;
  
  /* perhaps this will block to page? */
  Py_BEGIN_ALLOW_THREADS
  result = ptrace(request, pid, addr, 0);
  Py_END_ALLOW_THREADS

  if (result == -1 && errno)
    return posix_error();
  else
    return Py_BuildValue("l", result);
}

static char ptrace_peektext__doc__[] =
"peektext(pid, address) -> word\n\
Peek at a word in the child's text address space.";

static PyObject *
ptrace_peektext(PyObject *self, PyObject *args)
{
  return peek(PTRACE_PEEKTEXT, self, args);
}

static char ptrace_peekdata__doc__[] =
"peekdata(pid, address) -> word\n\
Peek at a word in the child's data address space.";

static PyObject *
ptrace_peekdata(PyObject *self, PyObject *args)
{
  return peek(PTRACE_PEEKDATA, self, args);
}

static char ptrace_peekuser__doc__[] =
"peekuser(pid, offset) -> word\n\
Peek at a word at the specified offset in the child's user area.";

static PyObject *
ptrace_peekuser(PyObject *self, PyObject *args)
{
  return peek(PTRACE_PEEKUSER, self, args);
}


static inline PyObject *
poke(int request, PyObject *self, PyObject *args)
{
  pid_t pid;
  long int addr, data, result;

  if (!PyArg_Parse(args, "(ill)", &pid, &addr, &data))
    return NULL;
  
  /* perhaps this will block to page? */
  Py_BEGIN_ALLOW_THREADS
  result = ptrace(request, pid, addr, data);
  Py_END_ALLOW_THREADS

  if (result == -1)
    return posix_error();
  Py_INCREF(Py_None);
  return Py_None;
}

static char ptrace_poketext__doc__[] =
"poketext(pid, address, word)\n\
Poke a word to the child's text address space.";

static PyObject *
ptrace_poketext(PyObject *self, PyObject *args)
{
  return poke(PTRACE_POKETEXT, self, args);
}

static char ptrace_pokedata__doc__[] =
"pokedata(pid, address, word)\n\
Poke a word to the child's data address space.";

static PyObject *
ptrace_pokedata(PyObject *self, PyObject *args)
{
  return poke(PTRACE_POKEDATA, self, args);
}

static char ptrace_pokeuser__doc__[] =
"pokeuser(pid, offset, word)\n\
Poke a word at the specified offset in the child's user area.";

static PyObject *
ptrace_pokeuser(PyObject *self, PyObject *args)
{
  return poke(PTRACE_POKEUSER, self, args);
}


static inline PyObject *
proceed(int request, PyObject *self, PyObject *args)
{
  pid_t pid;
  int signal;
  long int result;

  if (!PyArg_Parse(args, "(ii)", &pid, &signal))
    return NULL;
  
  /* possibly should do ALLOW_THREAD here? */
  result = ptrace(request, pid, 0, signal);

  if (result == -1)
    return posix_error();
  Py_INCREF(Py_None);
  return Py_None;
}

static char ptrace_cont__doc__[] =
"cont(pid, signal) -> None\n\
Continue child process, delivering specified signal.";

static PyObject *
ptrace_cont(PyObject *self, PyObject *args)
{
  return proceed(PTRACE_CONT, self, args);
}

static char ptrace_syscall__doc__[] =
"syscall(pid, signal) -> None\n\
Continue child process until next system call entry/exit, delivering specified signal.";

static PyObject *
ptrace_syscall(PyObject *self, PyObject *args)
{
  return proceed(PTRACE_SYSCALL, self, args);
}

static char ptrace_singlestep__doc__[] =
"singlestep(pid, signal) -> None\n\
Single-step child process, delivering specified signal.";

static PyObject *
ptrace_singlestep(PyObject *self, PyObject *args)
{
  return proceed(PTRACE_SINGLESTEP, self, args);
}

static char ptrace_detach__doc__[] =
"detach(pid, signal) -> None\n\
Continue child process and detach, delivering specified signal.";

static PyObject *
ptrace_detach(PyObject *self, PyObject *args)
{
  return proceed(PTRACE_DETACH, self, args);
}


static inline PyObject *
thump(int request, PyObject *self, PyObject *args)
{
  pid_t pid;
  long int result;

  if (!PyArg_Parse(args, "(i)", &pid))
    return NULL;
  
  /* possibly should do ALLOW_THREAD here? */
  result = ptrace(request, pid, 0, 0);

  if (result == -1)
    return posix_error();
  Py_INCREF(Py_None);
  return Py_None;
}

static char ptrace_kill__doc__[] =
"kill(pid) -> None\n\
Kill child process.";

static PyObject *
ptrace_kill(PyObject *self, PyObject *args)
{
  return thump(PTRACE_KILL, self, args);
}

static char ptrace_attach__doc__[] =
"attach(pid) -> None\n\
Attach to a process.";

static PyObject *
ptrace_attach(PyObject *self, PyObject *args)
{
  return thump(PTRACE_ATTACH, self, args);
}


#ifdef PTRACE_GETPPID

static char ptrace_getppid__doc__[] =
"getppid(pid) -> ppid\n\
Get the (original) parent's pid.";

static PyObject *
ptrace_getppid(PyObject *self, PyObject *args)
{
  pid_t pid;
  long int result, data;
  

  if (!PyArg_Parse(args, "(i)", &pid))
    return NULL;
  
  result = ptrace(PTRACE_GETPPID, pid, 0, &data);

  if (result == -1)
    return posix_error();
  return Py_BuildValue("i", data);
}

#endif


/* This really belongs in the base Python libraries, but for now, it's getting
 * stuffed here.  (FIX)
 */

static char ptrace_getpgid__doc__[] =
"getpgid(pid) -> pgid\n\
Get the process group id of the specified process.  If pid is 0, return the\
 pgid of the caller";

static PyObject *
ptrace_getpgid(PyObject *self, PyObject *args)
{
  pid_t pid, pgid;

  if (!PyArg_Parse(args, "(i)", &pid))
    return NULL;
  
  pgid = getpgid(pid);

  if (pgid == -1)
    return posix_error();
  return Py_BuildValue("i", pgid);
}




/* List of functions defined in the module */

static PyMethodDef ptrace_methods[] = {
#define method(x) { #x, ptrace_##x, METH_VARARGS, ptrace_##x##__doc__ }
	method(traceme),
	method(peektext),
	method(peekdata),
	method(peekuser),
	method(poketext),
	method(pokedata),
	method(pokeuser),
	method(cont),
	method(syscall),
	method(singlestep),
	method(detach),
	method(kill),
	method(attach),
#ifdef PTRACE_GETPPID
	method(getppid),
#endif
	method(getpgid),
	{ NULL }		/* sentinel */
};


/* Initialization function for the module */

DL_EXPORT(void)
     initptrace()
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule("ptrace", ptrace_methods);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyErr_NewException("ptrace.error", NULL, NULL);
  PyDict_SetItemString(d, "error", ErrorObject);
}
