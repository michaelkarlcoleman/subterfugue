# clone flags constants

# FIX: figure out something proper to do with these

CSIGNAL = 0x000000ff                    # signal mask to be sent at exit
CLONE_VM = 0x00000100                   # set if VM shared between processes
CLONE_FS = 0x00000200                   # set if fs info shared between processes
CLONE_FILES = 0x00000400                # set if open files shared between processes
CLONE_SIGHAND = 0x00000800              # set if signal handlers shared
CLONE_PID = 0x00001000                  # set if pid shared
CLONE_PTRACE = 0x00002000               # set if we want to let tracing continue on the child too
CLONE_VFORK = 0x00004000                # set if the parent wants the child to wake it up on mm_release
CLONE_PARENT = 0x00008000               # set if we want to have the same parent as the cloner
