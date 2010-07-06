# Composing with Densities using TM TimeFill and a Noise Instrument


from athenaCL.libATH import athenaObj

 
cmd = [
'emo cn',
'tmo tf',
'tin a 80',
'tie t 0,30',
# total event count is defined as static texture parameter, not a ParameterObject
'tie s3 600',
# start position within texture normalized within unit interval
'tie d0 rb,.3,.3,0,1',
# durations are independent of start time
'tie r cs,(mv,a{.01}b{1.5}c{3}:{a=20|b=1|c=1})',
'tie a ru,.5,.9',

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





