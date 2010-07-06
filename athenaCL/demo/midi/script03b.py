# Tendency Mask: Random Values between Breakpoint Functions


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo m')
 
cmd = [
'tin a 15',
'tie r cs,(ig,(ru,.01,.25),(ru,4,12))',
'tie a ru,.2,(cg,u,.3,.9,.005)',
'tie f rb,.2,.2,(bpl,t,l,((0,-12),(30,12))),(ws,t,29,0,0,24)',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



