# Large Scale Amplitude Behavior with Operators

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [
'tin a 64',
'tie r pt,(bg,rp,(16,16,8)),(bg,rp,(2,2,1,4)),(c,1)',
'tie a om,(ls,e,9,(ru,.2,1),(ru,.2,1)),(wp,e,23,0,0,1)',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



