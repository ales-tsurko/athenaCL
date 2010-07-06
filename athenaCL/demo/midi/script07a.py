# The CA as a Generator of Melodies

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo m')
 
cmd = [

# create a single, large Multiset using a sieve

'pin a 5@0|7@2,c2,c7',

'tmo ha',

'tin a 27',

'tie r pt,(c,8),(ig,(bg,rc,(2,3)),(bg,rc,(3,6,9))),(c,1)',

'tie a ls,e,9,(ru,.2,1),(ru,.2,1)',

# select only Multiset 0

'tie d0 c,0',

# select pitches from Multiset using CaList

'tie d1 cl,f{s}x{20},90,0,fria,oc',

# create only 1 simultaneity from each multiset

'tie d2 c,1',

# create only 1-element simultaneities

'tie d3 c,1',


]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



