import os
import sys
import glob 

clipsPath = '/Volumes/SMKMedia/00-MediaWork/Video/DVD/Animaniacs.Clips/'

def getAnimaniacsFiles() :
    for fn in glob.iglob('/Users/paul/Movies/Anim*mp4') :
        baseFn = os.path.basename( fn )[:-4]
        print baseFn
        
        for clipFn in glob.iglob(clipsPath + baseFn + '.*.mp4') :
            clipBaseFn = os.path.basename(clipFn)
            #clipName = clipBaseFn[len(baseFn) + 1 :]
            
            newFn = os.path.join( os.path.dirname(fn),clipBaseFn )
            print fn + " - " + newFn
            os.rename( fn, newFn )                       

try :            
    getAnimaniacsFiles()
except IOError as e :
    print "I/O error({0}): {1}".format(e.errno, e.strerror)
except :
    print "Unexpected error:", sys.exc_info()[0]
    raise

    