# Testing Csound

from athenaCL.libATH import athenaObj
 
cmd = [
'emo cn',
'tin a 82',
'tie x6 ws,e,14,0,200,16000',
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




