/* SUBTERFUGUE acceleration functions */

/* $Header$ */

/*
 * mainloop speed-up code from Pavel Machek (3/00)
 * added wait channel hack (3/00)
 */

#include <sys/ptrace.h>

#include "Python.h"

#define _USE_BSD
#include <fcntl.h>
#include <signal.h>
#include <sys/reg.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>


#ifdef PAVEL
/* Pavel, I want to know more about why this is needed.  Are these really not
   available on some Linux platform? */
#ifndef PTRACE_PEEKUSER
#define PTRACE_PEEKUSER PTRACE_PEEKUSR
#endif
#ifndef PTRACE_POKEUSER
#define PTRACE_POKEUSER PTRACE_POKEUSR
#endif
#endif

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


/* returns a pointer to a static string with the wait channel, NULL on error
 */
static const char *
waitchannel(int pid) {
  /* Grab the wait channel from /proc/n/stat.  Unfortunately, that file cannot
     be unambiguously parsed, so this may fail if more fields are added in
     future kernels.
  */

#define WAITCHANNELSIZE 20
  static char waitchannel[WAITCHANNELSIZE];
  static char buf[2048];
  char fn[32], *p;
  int fd, result, fcount;

  waitchannel[0] = 0;
  sprintf(fn, "/proc/%d/stat", pid);
  fd = open(fn, O_RDONLY); 
  if (fd == -1)
    return NULL;
  result = read(fd, buf, 2048);
  if (result < 1)
    return NULL;
  close(fd);

#define WCHANFIELD (-5)
  for (fcount = WCHANFIELD, p = buf + result - 1; p >= buf; p--)
    if (*p == ' ')
      if (++fcount == 0)
	break;

  if (fcount)
    return 0;
  p++;
  *(index(p, ' ')) = 0;
  strncpy(waitchannel, p, WAITCHANNELSIZE);
  waitchannel[WAITCHANNELSIZE-1] = 0;
  return waitchannel;
}

/* returns 1 at callstop, 0 at signalstop, and -1 on error */
static int
atcallstop(int pid, int stopsig) {
  /* The heuristic here is that the wait channel always has the same value for
     syscall stops, for any given kernel run.  We learn its value at the first
     stop which is not definitely a non-SIGTRAP signal stop.  This will fail
     if the very first such stop is actually a SIGTRAP stop, but this seems
     very unlikely in practice, and doesn't seem like something a rogue
     program could cause.
  */

  static char waitchannelstop[WAITCHANNELSIZE] = "";
  const char *result;

  stopsig = stopsig & 0x7F;	/* ignore 0x80, if present */
  
  if (stopsig != SIGTRAP)
    return 0;
  if (!(result = waitchannel(pid)))
    return -1;
  /* fprintf(stderr, "waitchannel: %s\n", result); */
  if (waitchannelstop[0] != 0)
    return !strcmp(result, waitchannelstop);
  strcpy(waitchannelstop, result);
  return 1;			/* pretty good guess */
}

static char subterfugue_atcallstop__doc__[] = 
"atcallstop(pid, stopsig) -> boolean\n\
Indicate whether the process pid, which is stopped with stopsig, is at a\n\
 system call stop (as opposed to a signal stop).";

static PyObject *
subterfugue_atcallstop(PyObject *self, PyObject *args)
{
  int pid, stopsig, result;

  if (!PyArg_Parse(args, "(ii)", &pid, &stopsig))
    return NULL;

  result = atcallstop(pid, stopsig);
  if (result == -1)
    return posix_error();
  return Py_BuildValue("i", result);
}


static char subterfugue_mainloop__doc__[] = 
"mainloop(pid) -> (wpid, status, beforecall)\n\
Run the optimized main loop until something interesting happens.\n\
Process 'pid' must already be known (in allflags), and 'insyscall' and\n\
'startup' must be false.";

static PyObject *
subterfugue_mainloop(PyObject *self, PyObject *args)
{
  int pid, wpid, status, scno, eax, waitchannelhack;
  int beforecall = -1;

  if (!PyArg_Parse(args, "(ii)", &pid, &waitchannelhack))
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
    if (!waitchannelhack) {
      if (WSTOPSIG(status) != (SIGTRAP | 0x80))
	goto giveup;
    } else {
      int r = atcallstop(pid, WSTOPSIG(status));
      if (r == -1)
	return posix_error();	/* shouldn't happen, but tell the caller */
      if (!r)
	goto giveup;
    }
      
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

static char subterfugue_setignorecall__doc__[] = 
"setignorecall(callnumber, ignore) -> None\n\
Indicate whether callnumber is to be ignored.  By default, each call is not\n\
ignored."; 

static PyObject *
subterfugue_setignorecall(PyObject *self, PyObject *args)
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

static PyMethodDef subterfugue_methods[] = {
#define method(x) { #x, subterfugue_##x, METH_VARARGS, subterfugue_##x##__doc__ }
	method(atcallstop),
	method(mainloop),
	method(setignorecall),
	{ NULL }		/* sentinel */
};


/* Initialization function for the module */

DL_EXPORT(void)
init_subterfugue()
{
  PyObject *m, *d;

  /* Create the module and add the functions */
  m = Py_InitModule("_subterfugue", subterfugue_methods);

  /* Add some symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = PyErr_NewException("_subterfugue.error", NULL, NULL);
  PyDict_SetItemString(d, "error", ErrorObject);
}
