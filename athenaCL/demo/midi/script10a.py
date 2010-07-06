# Feedback System as Dynamic Contour

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

 
cmd = [        
'emo mp',
'tmo lg',

'tin a 66',

# constant pulse
'tie r pt,(c,8),(c,1),(c,1)',

# amplitude controlled by Thermostat feedback
'tie a fml,t,(bg,rc,(1,1.5,2))',

# using convert second to set durations
'tie r cs,(fml,t,(c,1),(c,.7),.001,.400)',

# amplitude controlled by Climate Control feedback
'tie a fml,cc,(bg,rc,(.5,1,1.5)),(c,.7),0,1',

     
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






