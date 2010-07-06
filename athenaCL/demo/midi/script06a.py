# Deploying Pitch Sieves with HarmonicAssembly

from athenaCL.libATH import athenaObj
 
cmd = [
'emo m',

'pin a 11@1|13@2|23@5|25@6,c1,c7',
'tmo ha',

'tin a 0',

'tie t 0,30',

'tie a rb,.2,.2,.6,1',

'tie b c,120',

#zero-order Markov chains building pulse triples
'tie r pt,(c,4),(mv,a{1}b{3}:{a=12|b=1}),(mv,a{1}b{0}:{a=9|b=1}),(c,.8)',

#index position of multiset: there is only one at zero
'tie d0 c,0',

#selecting pitches from the multiset (indices 0-15) with a tendency mask
'tie d1 ru,(bpl,t,l,[(0,0),(30,12)]),(bpl,t,l,[(0,3),(30,15)])', 
#repetitions of each chord
'tie d2 c,1',

#chord size
'tie d3 bg,rc,(2,3)',
]





def main(cmdList=[], fp=None, hear=True):
    ath = athenaObj.Interpreter()

    for line in cmdList:
        ath.cmd(line)

    if fp == None:
        ath.cmd('eln') 
    else:
        ath.cmd('eln %s' % fp)

    if hear:
        ath.cmd('elh') 


if __name__ == '__main__':
    main(cmd)






