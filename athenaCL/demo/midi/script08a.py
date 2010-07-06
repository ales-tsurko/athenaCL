# Evolving African Drum Patterns with a GA: Two Durations

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [        
'tmo lg',
'tin a 61',

# bell line, set to loop
'tie r l,[(4,4,1),(4,4,1),(4,2,1),(4,4,1),(4,4,1),(4,4,1),(4,2,1)]',

# accent the first of each articulation
'tie a bg,oc,(1,.5,.5,.5,.5,.5,.5)',

'tin b 68',

# create genetic variations using a high mutation rate
'tie r gr,[(4,4,1),(4,4,1),(4,2,1),(4,4,1),(4,4,1),(4,4,1),(4,2,1)],.7,.25,0',


'tie a bg,oc,(1,.5,.5,.5,.5,.5,.5)',
        

]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



