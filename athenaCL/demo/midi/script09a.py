# Grammar States as Accent Patterns

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo mp')
 
cmd = [        

'tmo lg',

'tin a 60',

# non deterministic binary algae generator applied to accent

'tie r pt,(c,8),(c,1),(gt,a{0}b{1}@a{ab}b{a|aaa}@b,10,oc)',

'tie a c,1',

# four state deterministic applied to pulse multiplier

'tie r pt,(c,8), (gt,a{1}b{2}c{4}d{8}@a{ab}b{cd}c{aadd}d{bc}@ac,10,oc),(c,1)',

# four state deterministic applied to amplitude with different start string

'tie a gt,a{.25}b{.5}c{.75}d{1}@a{ab}b{cd}c{aadd}d{bc}@bbc,6,oc',

# four state deterministic applied to transposition with different start string

'tie f gt,a{0}b{1}c{2}d{3}@a{ab}b{cd}c{aadd}d{bc}@dc,6,oc',

# four state non-deterministic applied to transposition with different start string

'tie f gt,a{0}b{1}c{2}d{3}@a{ab}b{cd|aa}c{aadd|cb}d{bc|a}@dc,6,oc',



]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elh') 



