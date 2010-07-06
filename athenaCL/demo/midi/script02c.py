# Building a Basic Beat with Canonic Snare Imitation

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [
'tin a 36',
'tie r pt,(c,2),(bg,oc,(7,5,2,1,1)),(c,1)',
'tin b 37',
'tie r pt,(c,4),(bg,rp,(3,3,5,4,1)),(bg,oc,(0,1,1))',
'tin c 42',
'tie r pt,(c,2),(c,1),(bg,oc,(0,1))',

'tio b',
'ticp b b1',
'tie t .25, 20.25',
'tie i 76',
'ticp b b2',
'tie t .5, 20.5',
'tie i 77',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



