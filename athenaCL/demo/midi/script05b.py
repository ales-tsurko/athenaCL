# Markov-Based Proportional Rhythm Generation

from athenaCL.libATH import athenaObj

cmd = [
'emo mp',

'tin a 64',
# simple zero-order selection
'tie r mp,a{4,1}b{4,3}c{4,5}d{4,7}:{a=4|b=3|c=2|d=1}',

# first order generation that encourages movement toward the shortest duration
'tie r mp,a{8,1}b{4,3}c{4,7}d{4,13}a:{a=9|d=1}b:{a=5|c=1}c:{b=1}d:{c=1},(c,1)',
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






