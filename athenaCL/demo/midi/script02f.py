# Building an Extended Rhythmic Line with Fixed Tempo Phasing

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [
'tin a 70',
'tie r pt,(bg,oc,(2,4,4)),(bg,oc,(4,1,1,2,1)),(c,1) ',
'tie t 0,60',
'ticp a a1',
'tie b c,124',
'ticp a a2',
'tie b c,128',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



