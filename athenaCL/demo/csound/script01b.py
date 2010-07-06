# A Noise Instrument

from athenaCL.libATH import athenaObj
 
cmd = [
'emo cn',
'tin a 13',
'tie r cs,(whps,e,(bg,rp,(5,10,15,20)),0,.200,.050)',
# set initial low-pass filter cutoff frequency
'tie x2 whps,e,(bg,rp,(5,10,20,2,10)),0,400,18000',
# set final low-pass filter cutoff frequency
'tie x3 whps,e,(bg,rp,(5,10,20,2,10)),0,400,18000',

# panning controlled by fractional noise with infrequent zero-order Markov controlled jumps out of 1/f2 to 1/f0
'tie n n,100,(mv,a{2}b{0}:{a=12|b=1}),0,1',
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




