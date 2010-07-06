# Large Scale Amplitude Behavior with Operators

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

 
cmd = [
'emo mp',
'tin a 64',
'tie r pt,(bg,rp,(16,16,8)),(bg,rp,(2,2,1,4)),(c,1)',
'tie a om,(ls,e,9,(ru,.2,1),(ru,.2,1)),(wp,e,23,0,0,1)',
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






