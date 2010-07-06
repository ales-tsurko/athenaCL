# Polyphonic Sine Grains LineGroove

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo cn')
 
cmd = [
        
'tmo LineGroove',

'tin a 4',

# set a event time between 60 and 120 ms
'tie r cs,(ru,.060,.120)',

# smooth envelope shapes
'tie x0 c,.1',

'tie x1 c,.5',

# set field with a tendency mask converging on a single pitch after 15 seconds
'tie f ru,(ls,t,15,-24,0),(ls,t,15,24,0)',

# set random panning
'tie n ru,0,1',

# create a few more instances
'ticp a b c d e f',
        
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



