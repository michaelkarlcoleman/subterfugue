/* SUBTERFUGUE-specific ptrace functions */

/* $Header$ */

/* mainloop speed-up code from Pavel Machek */


#include <sys/ptrace.h>

#include "Python.h"

#define _USE_BSD
#include <signal.h>
#include <sys/reg.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>


//#define DBG(a...) fprintf( stderr, a )
#define DBG(a...)


static PyObject *ErrorObject;

/* Set a POSIX-specific error from errno, and return NULL */
static PyObject *
posix_error()
{
  return PyErr_SetFromErrno(PyExc_OSError);
}


/* if a call is not ignored, we have to let the surrounding Python handle it */
#define MAXCALLNUMBER 256
char call_ignored[MAXCALLNUMBER] = { 0 };

int numignored = 0, numtraced = 0;

static char sfptrace_mainloop__doc__[] = 
"mainloop(pid) -> (wpid, status, beforecall)\n\
Run the optimized main loop until something interesting happens.\n\
Process 'pid' must already be known (in allflags), and 'insyscall' and\n\
'startup' must be false.";

static PyObject *
sfptrace_mainloop(PyObject *self, PyObject *args)
{
  int pid, wpid, status, scno, eax;
  int beforecall = -1;

  if (!PyArg_Parse(args, "(i)", &pid))
    return NULL;

  numtraced++;

  while (1) {
    int result;

#ifndef __WALL
#define __WALL 0x40000000
#endif
    wpid = wait4(-1, &status, WUNTRACED | __WALL, NULL);
    if (wpid == -1)
      return posix_error();

    DBG("Checking pids: %d, %d\n", pid, wpid);
    if (pid != wpid)		/* XXX: could maybe be handled w/o giving up */
      goto giveup;
    DBG("This looks good\n");
    if (!WIFSTOPPED(status)) 
      goto giveup;
    DBG("checking SIGTRAP\n");
    if (WSTOPSIG(status) != (SIGTRAP | 0x80))
      goto giveup;
  
    /* Only check the system call number on the before stop, because some
       calls (e.g., sigreturn) stomp that number.  On the after stop, by the
       time we get here it "must" be okay to ignore this stop.  (Skipping
       these checks also speeds things up a bit.)
    */
    if (beforecall) {
      DBG("getting scno\n");
      scno = ptrace(PTRACE_PEEKUSER, wpid, 4*ORIG_EAX, &scno);
      DBG("scno is %d (%m)\n", scno);
      if (scno < 0 || scno >= MAXCALLNUMBER)
	goto giveup;

      DBG("looking if call_ignored\n");
      if (!call_ignored[scno])
	goto giveup;

      eax = ptrace(PTRACE_PEEKUSER, wpid, 4*EAX, 0);
      if ((eax != -ENOSYS) /* && beforecall */)
	goto giveup;
    }

    DBG("ok, this call is ignored here\n" );
    beforecall = !beforecall;

    result = ptrace(PTRACE_SYSCALL, pid, 0, 0);
    if (result == -1)
      return posix_error();	/* shouldn't happen, but tell the caller */
      
    numignored++;
    if (!(numignored % 1000))
      DBG("numignored = %d, numtraced = %d\n", numignored, numtraced);
  }

giveup:  
  /* if beforecall is nonzero, change 'insyscall' status of _pid_ to that returned */

  //  fprintf( stderr, "Returning %d, %d, %d\n", wpid, status, beforecall );
  return Py_BuildValue("(iii)", wpid, status, beforecall);
}

static char sfptrace_setignorecall__doc__[] = 
"setignorecall(callnumber, ignore) -> None\n\
Indicate whether callnumber is to be ignored.  By default, each call is not\n\
ignored."; 

static PyObject *
sfptrace_setignorecall(PyObject *self, PyObject *args)
{
  int callnumber, ignored;

  if (!PyArg_Parse(args, "(ii)", &callnumber, &ignored))
    return NULL;

  if (callnumber < 0 || callnumber >= MAXCALLNUMBER) {
    PyErr_SetString(PyExc_ValueError, "invalid call number");
    return NULL;
  }
  call_ignored[callnumber] = ignored;
  Py_INCREF(Py_None);
  return Py_None;
}


/* List of functions defined in the module */

static PyMethodDef sfptrace_methods[] = {
#define method(x) { #x, sfptrace_##x, METH_VARARGS, sfptrace_##x##__doc__ }
	method(setignorecall),
	method(mainloop),
	{ NULL }		/* sentinel */
};


/* Initialization function for the module */

DL_EXPORT(void)
     initsfptrace()
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule("sfptrace", sfptrace_methods);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyErr_NewException("sfptrace.error", NULL, NULL);
  PyDict_SetItemString(d, "error", ErrorObject);
}
