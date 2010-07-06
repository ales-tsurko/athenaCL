# Configuring Time Range

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()


cmd = [
'emo mp',
 
'tin a 45', 
'tie t 0,20', 
'tie a rb,.3,.3,.4,.8', 
'tie r pt,(c,4),(bg,oc,(3,3,2)),(c,1)', 

'tin b 65', 
'tie t 10,20', 
'tie a re,15,.3,1', 
'tie r pt,(bg,rp,(2,1,1,1)),(c,1),(c,1)', 

'tin c 67', 
'tie t 15,25', 
'tie a rb,.1,.1,.4,.6', 
'tie r cs,(rb,.2,.2,.01,1.5)', 

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




