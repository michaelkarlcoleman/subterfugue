#
#       Substitute one filename by another in open and stat64 call
#
#       Copyright 2003 Jiri Dobes <dobes@centrum.cz>
#       Can be freely distributed and used under the terms of the GNU GPL.
#
#       Version 0.0.1

from Trick import Trick
from Memory import *

class File(Trick):
    def usage(self):
        return """
This trick substitute one filename by another in calling open or state64.
Usefull to change hardcoded filenames.

Example:

sf --trick=File:\'file=[[\"a\",\"c\"],[\"b\",\"d\"]]\' cp a b

instead of copying \"a\" to \"b\" it copy file \"c\" to file \"d\"
(altrough some warining message is issued).
"""


    def __init__(self, options):
        if options.has_key('file'):
            self.options = options[ 'file' ]
        else:
            self.options = [["",""]] #do nothing by default
            
    def callmask( self ):
        return { 'open' : 1, 'stat64' : 1 }

    def callbefore(self, pid, call, args):
        "Perform argument substitution"
#both calls have same argument structure        
        if( call == "open" or call == "stat64" ): 
            list = self.options
            m = getMemory(pid)
            address = args[0]
            filename = m.get_string(address)
            for x in list:
                if( filename == x[0] ):
                    area, asize = m.areas()[0]
                    m.poke( area , x[1] + '%c' % 0 , self )
                    newargs = ( area , args[ 1 ], args[ 2 ] )
                    return (None, None, None , newargs )
        if( call == "stat" ): #maybe include above?
            print "stat is not yet implemented!"
            
