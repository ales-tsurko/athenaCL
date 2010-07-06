# Testing Csound

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()
ath.cmd('emo cn')
 
cmd = [
'tin a 82',
'tie x6 ws,e,14,0,200,16000',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



