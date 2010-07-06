# Grammar States as Pitch Transpositions

from athenaCL.libATH import athenaObj
 
cmd = [        
'emo m',

'tmo lg',

'tin a 15',


#four state deterministic applied to pulse multiplier

'tie r pt,(c,8), (gt,a{1}b{2}c{4}d{8}@a{ab}b{cd}c{aadd}d{bc}@ac,8,oc),(c,1)',

#four state deterministic applied to accumulated transposition with different start string

'tie f a,0,(gt,a{1}b{-1}c{7}d{-7}@a{ab}b{cd}c{ad}d{bc}@ac,10,oc)',

# four state deterministic applied to amplitude with different start string

'tie a gt,a{.25}b{.5}c{.75}d{1}@a{ab}b{cd}c{aadd}d{bc}@bbc,6,oc',

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






