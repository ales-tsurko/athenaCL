# Tendency Mask: Random Values between Triangle Generators

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo m')
 
cmd = [
'pin a d,e,g,a,b',
'tin a 107  ',
'tie r pt,(c,16),(ig,(bg,rc,(1,2,3,5,7)),(bg,rc,(3,6,9,12))),(c,1)',
'tie o ru,(wt,t,25,0,-2,4),(wt,t,20,0,-3,1)',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



