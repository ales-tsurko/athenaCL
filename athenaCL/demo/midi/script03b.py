# Tendency Mask: Random Values between Breakpoint Functions


from athenaCL.libATH import athenaObj
 
cmd = [
'emo m',
'tin a 15',
'tie r cs,(ig,(ru,.01,.25),(ru,4,12))',
'tie a ru,.2,(cg,u,.3,.9,.005)',
'tie f rb,.2,.2,(bpl,t,l,((0,-12),(30,12))),(ws,t,29,0,0,24)',
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






