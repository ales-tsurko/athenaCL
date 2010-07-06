# Building a Basic Beat with a Complex Snare Part

from athenaCL.libATH import athenaObj
 
cmd = [
'emo mp',
'tin a 36',
'tie r pt,(c,2),(bg,oc,(7,5,2,1,1)),(c,1)',
'tin b 37',
'tie r pt,(c,4),(bg,rp,(3,3,5,4,1)),(bg,oc,(0,1,1))',
'tin c 42',
'tie r pt,(c,2),(c,1),(bg,oc,(0,1))',
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




