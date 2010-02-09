
import os
from athenaCL.libATH.libAS import script
from athenaCL.libATH import osTools # needed for scratch dirs


class Script(script.AthenaScript):

    def __init__(self, scriptArgs):
        script.AthenaScript.__init__(self, scriptArgs)
        testPath = os.path.join(drawer.tempDir(), '__test__.xml')
        self.cmdList = (
        'pin a 5|7|11,c1,c8',
        'tmo lh',
        'tin a 1',
        'tie t 0,5',
        'tie r loop,((8,1,+),(9,2,+)),rc',
        
        'tcn a',
        # do a scaling, and a shift, to a part
        'tce t pl,((fa,(c,5)),(fma,l,(c,.5)))',

        'tce s1 ei',
        
        'tcn b',
        'tce t pl,((fa,(c,10)),(fma,l,(c,1.25)))',
        'tce s1 ti',

        'eln /_scratch/a.xml',
        #'elr',
        'elh',
        )
