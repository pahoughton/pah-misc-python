import os
import sys
import tempfile
import unittest
import subprocess
import logging
import shutil
import textwrap

CVS_MODULES_FN = 'modules'
CVS_ROOT_FN = 'Root'
CVS_REPOS_FN = 'Repository'
CVS_REPO_ROOT = 'CVSROOT'
TEST_WORKING_GOOD_DIR = 'workingGood'

def fix_dir_root_and_repos(dir,origCvsRootDir,newCvsRootDir):
    '''Modify CVS/Root and CVS/Repository files for newCvsRootDir
    
    the CVS/Repository file may or may not have the full path.
    When it does, remove the cvs root directory component,
    leaving just the relative path
    '''
    rootFn = os.path.join(dir,'CVS', CVS_ROOT_FN)
    reposFn = os.path.join(dir, 'CVS', CVS_REPOS_FN)
    
    with open( rootFn,'w') as f:
        f.write(newCvsRootDir + '\n')
    
    # Older Repository files may have full path
    reposPath = ''
    with open(reposFn,'r') as f:
        reposPath = f.readline()
    
    if reposPath.startswith(origCvsRootDir):
        with open(reposFn,'w') as f:
            newReposPath = reposPath[len(origCvsRootDir) + 1:]
            f.write( newReposPath + '\n')
    
    
def change_cvs_root(newCvsRootDir):
    '''Modify CVS/Root file to point to my new CVSROOT value
    
    Find each CVS/Root file in the current directory and modify it's single
    line contents to point to the directory given as newCvsRootDir 
    '''
    if not os.path.isfile(os.path.join('CVS',CVS_ROOT_FN)):
        raise Exception('Current dir %s is not a cvs working directory'
                        % os.getcwd() )
    
    if subprocess.call(['cvs','-d',newCvsRootDir,'log','-l']):
        raise Exception('current dir not in '+newCvsRootDir+' repository')
    
    origCvsRootDir = ''
    with open(os.path.join('CVS',CVS_ROOT_FN)) as f:
        origCvsRootDir = f.readline().rstrip('\n')
    
    # the last string after the colon is the root full path
    # for non directory cvs root values
    colonPos = origCvsRootDir.rfind(':')    
    if colonPos != -1:
        origCvsRootDir = origCvsRootDir[colonPos + 1:]
    
    logging.debug('origCvsRootDir: ' + origCvsRootDir)
    # fix this dir's CVS/Root and CVS/Repository
    fix_dir_root_and_repos('.',origCvsRootDir,newCvsRootDir)
    # now change all sub directory CVS/Roots
    for rootDir, dirList, fileList in os.walk('.'):
        rootFn = os.path.join(rootDir, 'CVS', CVS_ROOT_FN)
        if os.path.isfile(rootFn):
            fix_dir_root_and_repos(rootDir, origCvsRootDir, newCvsRootDir)
                    
    return 0
        
        
class TestAll(unittest.TestCase):
    '''
    '''
    cvsRootFn = 'Root'
    goodCvsRepos = [':pserver:anonymous@emacs-templates.cvs.sourceforge.net:/cvsroot/emacs-templates',]
    
    def setUp(self):
        '''Create files and directories needed for testing
        
        Make valid and invalid repository directories
        Create a working directory with CVS/Root files
        Create an invalid working directory structure
        '''
        self.initialCurrentDir = os.getcwd()
        self.testTempDir = tempfile.mkdtemp()
        print "Created Tmpdir: " + self.testTempDir
        try:
            # see next method comment
            self.utilsetUpAfterTmpDir()
        except Exception as e:
            logging.exception("FAILED: Setup!")
            if self.testTempDir:
                print "Removing Tempdir: "+self.testTempDir
                shutil.rmtree(self.testTempDir)
            raise e;
                
    def utilsetUpAfterTmpDir(self):
        """utility function, only created to reduce indentation within
        my try: block in the setUp function
        """
            
        del os.environ['CVSROOT']
        del os.environ['CVS_RSH']

        self.cvsReposBad = os.path.join(self.testTempDir,
                                          'cvsReposBad')
        self.cvsReposGood = os.path.join(self.testTempDir,
                                          'cvsReposGood')
        self.newRepos = os.path.join(self.testTempDir,
                                      'newCvsRepos')
        self.workingBad = os.path.join(self.testTempDir,
                                          'workingBad')
        self.workingGood = os.path.join(self.testTempDir,
                                        TEST_WORKING_GOOD_DIR )
                                          
        self.cvsReposGoodCvsRoot = os.path.join(self.cvsReposGood, CVS_REPO_ROOT) 
        self.cvsReposModulesFn = os.path.join(self.cvsReposGoodCvsRoot,
                                               CVS_MODULES_FN)
        # make the test directory structures
        testDirs = [os.path.join(self.cvsReposBad,'notcvsroot'),
                     self.cvsReposGoodCvsRoot,
                     os.path.join(self.workingBad,'nocvs'),
                     os.path.join(self.workingBad,'sub/CVS'),
                     ]
        #logging.debug('dirlist: %r', testDirs)
        for tdir in testDirs:
            os.makedirs( tdir )
            
        # create the test files needed
        os.chdir(self.cvsReposGood)
        if subprocess.call(['cvs', '-d', self.cvsReposGood, 'init']):
            raise Exception( 'cvs init failed in test setUp')
        if not os.path.isfile(os.path.join(self.cvsReposGood,
                                           CVS_REPO_ROOT, 
                                           CVS_MODULES_FN)):
            raise Exception('cvs init failed to create modules file')
        
        os.makedirs(TEST_WORKING_GOOD_DIR)
        os.chdir(self.testTempDir)
        if subprocess.call(['cvs', '-d', self.cvsReposGood, 
                            'co', TEST_WORKING_GOOD_DIR]):
            raise Exception( 'cvs co failed in test setUp')
        if not os.path.isfile( os.path.join(self.workingGood, 'CVS', CVS_ROOT_FN)):
            raise Exception('cvs co failed')
        
        # add some subdirs and files
        os.chdir(TEST_WORKING_GOOD_DIR)
        os.makedirs("Subdir/sub")
        with open('Subdir/test1.txt','w') as f:
            f.write('just some text for testing\n')
        with open('test2.txt','w') as f:
            f.write('more testing stuff')
     
        # add to cvs        
        if subprocess.call(['cvs', '-d', self.cvsReposGood, 
                            'add','-m','testing',
                            'Subdir',
                            'Subdir/test1.txt',
                            "test2.txt"
                            ]):
            raise Exception('cvs add failed')
        
        if subprocess.call(['cvs', '-d', self.cvsReposGood, 
                            'ci','-m','ci testing']):
            raise Exception('cvs ci failed')
        
        # now for an uncommited change
        with open('test2.text','a') as f:
            f.write('not checked in text\n')        
        
        
    def test_change_cvs_root(self):
        '''Verify valid and invalid input values.
        
        A CVSROOT value can be either a regular directory or a remote location
        both can be verified before the program modifies the current directories 
        CVS/Root files. If the CVSROOT value given is not a valid CVS repository
        the application should terminate with a description of why it did not 
        proceed
        '''
        os.chdir(self.testTempDir)
        os.chdir(self.workingBad)
        self.assertRaises(Exception, change_cvs_root, self.cvsReposGood)
        self.assertRaises(Exception, change_cvs_root, self.cvsReposBad)
        os.chdir(self.workingGood)
        self.assertRaises(Exception, change_cvs_root, self.cvsReposBad)
        
        os.rename(self.cvsReposGood, self.newRepos)
        self.assertEqual(change_cvs_root(self.newRepos), 0)
        
        # all Root files should now contain the new cvs root
        for dir in ['.', 'Subdir']:
            rootFileContent = ''
            with open(os.path.join(dir,"CVS",CVS_ROOT_FN)) as f:
                rootFileContent = f.readline()
                
            self.assertEqual(rootFileContent,self.newRepos + '\n')
        
        self.assertEqual(subprocess.call(['cvs','ci','-m','test ci']), 0)
        os.chdir(self.initialCurrentDir)
        
    def tearDown(self):
        print 'In tearDown ',self.testTempDir
        os.chdir(self.initialCurrentDir)
        if os.path.isdir(self.testTempDir):
            shutil.rmtree(self.testTempDir)
        if os.path.isdir(self.testTempDir):
            raise Exception(self.testTmpDir +' was not removed!')

def main(argv):
    if (len(argv) != 2
        or argv[1] in ['-h', '-help', '--help', 'help']) :
        usage = '''
              Usage: %s CvsRoot|test (use test to run selftest)
        
              Change the CVS/Root files under the current CVS working directory
              to point to the CvsRoot value provided.
              
              so if you:
              bash$ cvs -d /oldrepo co stuff
              bash$ mv /oldrepo /newrepo
              bash$ cd stuff
              bash$ %s /newrepo
              bash$ cvs log # will work again.
              
              Useful if you have to move your cvs repository when you have 
              items checked out.
              ''' % (argv[0], argv[0])
              
        print textwrap.dedent(usage)
        print "Command: "+", ".join(argv)
        sys.exit( 2 )
        
    newRepos = sys.argv.pop()
    
    if newRepos == 'test':
        unittest.main()                
    else:
        change_cvs_root(newRepos)
        print "Changed CVS/Root files to point to",newRepos
        sys.exit(0)
            
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv)
    