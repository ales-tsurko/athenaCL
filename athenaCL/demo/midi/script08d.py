# Evolving African Drum Patterns with a GA: Multiple Rhythmic Values


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [        

'tmo lg',

'tin a 45',
'tie r gr,[(4,4,1),(4,4,1),(4,2,1),(4,4,1),(4,4,1),(4,4,1),(4,2,1)],.7,.15,0',
'tie a bg,oc,(1,.5,.5,.5,.5,.5,.5)',

'tin b 60',
# create genetic variations using a high crossover, no mutation
'tie r gr,[(4,2,0),(4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1),(4,2,0), (4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1)],1,0,0',

'tie a bg,oc,(.5,1,.5, .5,.5,.5, .5,.5,.5, .5,.5,.5)',

# turning on silence mode will use parameters even for rests
'timode s on',


'tin c 68',  
# create genetic variations using a high crossover and mutation rate and some elitism

'tie r gr,[(4,3,1),(4,1,1),(4,2,1),(4,2,1),(4,1,1),(4,1,1),(4,2,1), (4,3,1),(4,1,1),(4,2,1),(4,2,1),(4,1,1),(4,1,1),(4,2,1)],.9,.25,0.1',


'tie a bg,oc,(1,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5)',

   


]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



