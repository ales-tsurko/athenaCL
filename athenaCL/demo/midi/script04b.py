# 1/f Noise in Melodic Generation: LineGroove


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo m')
 
cmd = [
'tmo lg',
'tin a 108',
'tie r cs,(ls,e,10,(ru,.01,.2),(ru,.01,.2))',
'tie f bs,(2,4,7,9,11,14,16,19,21,23),(n,100,1,0,1)',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



