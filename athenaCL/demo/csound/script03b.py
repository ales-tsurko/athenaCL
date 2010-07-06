# Polyphonic Sine Grains: DroneArticulate

from athenaCL.libATH import athenaObj

cmd = [
'emo cn',
'apr off',

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




def main(cmdList=[], fp=None, hear=True, render=True):
    ath = athenaObj.Interpreter()

    for line in cmdList:
        ath.cmd(line)

    if fp == None:
        ath.cmd('eln') 
    else:
        ath.cmd('eln %s' % fp)

    if render:
        ath.cmd('elr') 

    if hear:
        ath.cmd('elh') 


if __name__ == '__main__':
    main(cmd)




