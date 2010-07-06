# Creating Mensural Canons

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [
'tin a 77', 
'tie r pt,(c,1),(c,1),(c,1)', 
'tin b 67', 
'tie r pt,(bg,oc,(2,4,1)),(bg,oc,(3,5,1,7,1,3)),(c,1) ', 
'ticp b b1', 
'tie t 0.125,20.125', 
'tie i 60', 
'ticp b b2', 
'tie t 0.25,20.25', 
'tie i 68', 
'tio b1', 
'tie b c,90',
'tio b2', 
'tie b c,180',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



