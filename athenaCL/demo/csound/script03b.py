# Polyphonic Sine Grains: DroneArticulate

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo cn')
ath.cmd('apr off')

cmd = [
        
'tmo DroneArticulate',
 
# a very large pitch collection made from a Xenakis sieve
'pin a 5@2|7@6,c1,c9',
'tin a 4',

# set a event time between 60 and 120 ms
'tie r cs,(ru,.060,.120)',

# smooth envelope shapes
'tie x0 c,.1',
'tie x1 c,.5',

# set random panning
'tie n ru,0,1',

# reduce amplitudes
'tie a ru,.6,.8',
        
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



