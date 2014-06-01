import sys
import string
import random

print ''.join(random.choice(string.ascii_letters + string.digits) for x in range(int(sys.argv[1])));
