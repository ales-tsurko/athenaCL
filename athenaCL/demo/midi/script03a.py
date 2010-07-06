# Grouping Selection

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo m')
 
cmd = [
'tin a 6', 
'tie r cs,(rb,.2,.2,.02,.25)', 
'tie f ig,(bg,rc,(2,4,7,9,11)),(bg,rp,(2,3,5,8,13))', 
'tie o ig,(bg,oc,(-2,-1,0,1)),(ru,20,30)', 
'ticp a b c d', 
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



