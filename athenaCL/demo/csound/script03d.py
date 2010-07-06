# Polyphonic Sample Grains from a Multiple Audio Files: LineGroove

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo cn')
ath.cmd('apr off')
 
cmd = [

'tmo LineGroove',

# instrument 32 is a fixed playback rate sample player
'tin a 32',

# set a file path to an directory, a file extension, and a selection method
'tie x6 ds,/Volumes/xdisc/_sync/_x/src/martingale/martingale/audio,.aif,rp',

# set a event time between 60 and 120 ms
'tie r cs,(ru,.060,.120)',

# smooth envelope shapes
'tie x0 c,.01',
'tie x1 c,.5',

# start position within audio file in seconds
'tie x5 ru,0,10',

# set random panning
'tie n ru,0,1',

# control a variety of amplitudes
'tie a ru,.2,.4',

# create a few more instances
'ticp a b c',
       
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



