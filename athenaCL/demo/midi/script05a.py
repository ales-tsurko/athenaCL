# Self Similar Markovian Melody Generation and Transposition

from athenaCL.libATH import athenaObj
 
cmd = [

'emo m',

'tin a 24',
'tie r cs,(n,100,1.5,.100,.180)',
'tie r cs,(om,(n,100,1.5,.100,.180),(ws,t,8,0,.5,1))',

# Markov weighted pitch transposition
'tie f mv,a{2}b{4}c{7}d{9}e{11}:{a=1|b=6|c=1|d=9|e=1}',

# self-similar pitch transposition combing a grouped version of the same Markov generator with OperatorAdd
'tie f oa,(mv,a{2}b{4}c{7}d{9}e{11}:{a=1|b=3|c=1|d=3|e=1}), (ig,(mv,a{2}b{4}c{7}d{9}e{11}:{a=1|b=3|c=1|d=3|e=1}),(ru,10,20))',

# Markov based octave shifting
'tie o mv,a{-2}b{0}c{-2}d{0}e{-1}:{a=1|b=3|c=1|d=3|e=1}',

# A widening beta distribution
'tie a rb,.2,.5,(ls,e,(ru,3,20),.5,1)',

# Modulated with a pulse wave (and random frequency modulation on the PulseWave)
'tie a om,(rb,.2,.5,(ls,e,(ru,3,20),.5,1)),(wp,e,(ru,25,30),0,0,1)',
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






