# A Sample Playback Instrument

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()


ath.cmd('emo cn')
 
cmd = [

'tin a 32',
# set a file path to an audio file
'tie x6 cf,/Volumes/xdisc/_sync/_x/src/martingale/martingale/audio/29561.aif',
# line segment absolute rhythm durations
'tie r cs,(ls,e,(ru,5,30),(ru,.03,.15),(ru,.03,.15))',
# start position within audio file in seconds
'tie x5 ru,0,40',
'tie a ls,e,(bg,rc,(3,5,20)),.1,1',
'tie x2 whps,e,(bg,rp,(5,10,20,2,10)),0,100,10000',

]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



