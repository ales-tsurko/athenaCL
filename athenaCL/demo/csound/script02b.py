# Composing with Densities using TM TimeFill and a Single Sample

from athenaCL.libATH import athenaObj
 
cmd = [
'emo cn',
'tmo tf',
'tin a 32',
# set a file path to an audio file
'tie x6 cf,/Volumes/xdisc/_sync/_x/src/martingale/martingale/audio/27980-high-slow.aif',
# start position within audio file in seconds
'tie x5 ru,0,1',
# vary a low pass filter start and end frequencies
'tie x2 mv,a{200}b{1000}c{10000}:{a=6|b=2|c=1}',
'tie x3 mv,a{200}b{1000}c{10000}:{a=6|b=2|c=1}',

# total event count is defined as static texture parameter, not a ParameterObject
'tie s3 500',
# start position within texture normalized within unit interval
'tie d0 ic,(rg,.2,.1,0,1),(rg,.7,.1,0,1),(bg,rc,(0,1))',
# durations are independent of start time
'tie r cs,(whps,e,(bg,rp,(5,10,15)),0,.010,.100)',
# must reduce amplitudes
'tie a ru,.1,.3',
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




