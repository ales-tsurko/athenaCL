# Evolving African Drum Patterns with a GA: Combinations of Rests and Silences


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

 
cmd = [        
'emo mp',

'tmo lg',
'tin a 61',

# kagan line, set to loop
'tie r l,[(4,2,0),(4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1),(4,2,0), (4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1)]',

# accent the first of each articulation
'tie a bg,oc,(.5,1,.5, .5,.5,.5, .5,.5,.5, .5,.5,.5)',

# turning on silence mode will use parameters even for rests
'timode s on',
'tin b 68',

# create genetic variations using a high crossover, no mutation
'tie r gr,[(4,2,0),(4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1),(4,2,0), (4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1)],1,0,0',

'tie a bg,oc,(.5,1,.5, .5,.5,.5, .5,.5,.5, .5,.5,.5)',

# turning on silence mode will use parameters even for rests

'timode s on',



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







