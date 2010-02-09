
import os
from athenaCL.libATH.libAS import script
from athenaCL.libATH import osTools # needed for scratch dirs


class Script(script.AthenaScript):

    def __init__(self, scriptArgs):
        script.AthenaScript.__init__(self, scriptArgs)
        self.cmdList = self._buildCmdList(self.scriptArgs)

    def _buildCmdList(self, scriptArgs):    
        testAo  = os.path.join(drawer.tempDir(), '__test__.xml')
        testSco = testAo # use same name
        setMeasureNames = scriptArgs['setMeasureNames']
        textureNames = scriptArgs['textureNames']
        textureNames.sort()
        cmdsDoc, cmdsUndoc, helpTopics = scriptArgs['allCmds']
        
        cmdListA = []
        for cmd in (cmdsDoc + helpTopics):
            cmdListA.append('? %s' % cmd)
    
        # test all commands
        cmdListB = (

        'PIn test1  5-4  3-4     2-5',
        'PIn test2  (3,4,4,4,4) (3,3,3) (1,1,2,3)',
        'PIn test3  8-3  (3,4,3)  7-5',
        'PIv',
        'PIcp test1  test4',
        'PIrm test4',
        'PIls',
        'PIo test1',
        )
            
        
        cmdListD = (
        'PIret test1retro',
        'PIrot test1retroRot     2',
        'PIslc test1retroRotSlc  2,3',
        'PIo test2',
        # pvn
        )

        cmdListE = []
        for texture in textureNames:
            cmdListE.append('EMo cn')
            cmdListE.append('TMo %s' % texture)
            cmdListE.append('TMv ')
            cmdListE.append('TMls ')
            cmdListE.append('TIn test1 3')
            cmdListE.append('TIn test2 80')
            cmdListE.append('TIn test3 22')
            cmdListE.append('TIcp test3  test4 test5 test6')
            cmdListE.append('TIrm test4 test5 test6')
            cmdListE.append('TIls ')
            cmdListE.append('TIo test2')
            cmdListE.append('TIv ')
            cmdListE.append('TIv test3')
            cmdListE.append('TImute test1 test3')
            cmdListE.append('TImode p   pcs')
            cmdListE.append('TImode y   set')
            cmdListE.append('TIe t  1.5, 3')
            cmdListE.append('TIe r  l, ((4,1,1),(8,1,1),(8,3,1))')
            cmdListE.append('TIrm test1 test2 test3')

        cmdListF = (
        'TIn test1 3',
        'TIn test2 80',
        'TIn test3 22',
        'TEe b  "c", 120',
        'TEe a  "cg", "lu", .6, .7, .01',
        'TEv beat',
        'TEv a',
        'TIdoc test1',
        'TIdoc test2',
        'TTls ',
        'TTo NoiseLight',
        'TCn echoA',
        'TCn echoB',
        'TCn echoC',
        'TCn echoD',
        'TCcp echoD echoE',
        'TCls ',
        'TCrm echoC echoB',
        'TCe t fa,(c,10)',
        'TEmap ',
        'EMi ',
        'TPls ',
        'TPv sieve ',
        'ELauto' ,
        #'APa ch 2',
        'CPff a',
        'EOo af,at,cb,cd,co,cs,mc,mf,ts,tt,xao',
        'ELn %s' % testSco,
        'ELw %s' % testSco,
        # remove
        'EOrm af,at,cb,cd,co,cs,mc,mf,ts,tt,xao',
        # do all test load files
        'AOl test01.xml',
        'AOl test02.xml',
        'AOl test03.xml',
        'AOl test04.xml',
        'AOl test05.xml',
        'AOl test06.xml',
        'AOl test07.xml',
        'AOl test08.xml',
        'AOl test09.xml',
        # load each demo and make a score
        'EOo at,cb,cd,co,cs,mc,mf,ts,tt,xao',
        'AOl demo01.xml',
        'ELn %s' % testSco,
        'AOl demo02.xml',
        'ELn %s' % testSco,
        'AOl demo03.xml',
        'ELn %s' % testSco,
        'AOl demo04.xml',
        'ELn %s' % testSco,
        'AOl demo05.xml',
        'ELn %s' % testSco,
        'AOl demo06.xml',
        'ELn %s' % testSco,
        'AOmg demo01.xml',
        'AOmg demo02.xml',
        'AOmg demo03.xml',
        'AOmg demo04.xml',
        'AOmg demo05.xml',
        'AOmg demo06.xml',
        'ELn %s' % testSco,
        'AOw %s' % testAo,
        'EOrm at,cb,cd,co,cs,mc,mf,ts,tt,xao',
        #AOdlg    
        'APwid 80',
        'APcurs',
        'APcurs',
        'cmd',
        'help',
        'AUsys',
        'AUca f{f}x{101}y{100} .89124 .01',
        'AUca x{20} ru,0,20 ru,0,0.04',
        'AUma 4 9 2 9 3 9 3 8 3 9 3 8 4 8 3 9 3 8 3 4 9 2 3 8 4 9',
        'AUmg 120 0 a{0}b{1}:{a=3|b=8}',
        )
        
        
        cmdList = (list(cmdListA) + list(cmdListB) + list(cmdListC) + 
                     list(cmdListD) + list(cmdListE) + list(cmdListF))
        return cmdList
    




