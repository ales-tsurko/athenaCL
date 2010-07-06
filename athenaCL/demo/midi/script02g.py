# Building an Extended Rhythmic Line with Dynamic Tempo Phasing


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [
'tin a 64',
'tie r pt,(bg,oc,(2,4,4)),(bg,oc,(4,1,1,2,1)),(c,1) ',
'tie t 0,60',
'ticp a a1',
'tie i 60',
'tie b ws,t,20,0,115,125',
'ticp a a2',
'tie i 69',
'tie b ws,t,30,0,100,140',
]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



