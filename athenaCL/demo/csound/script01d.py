# A Sample Playback Instrument with Variable Playback Rate


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo cn')
 
cmd = [

'tin a 230',
'tie x6 cf,/Volumes/xdisc/_sync/_x/src/martingale/martingale/audio/32673.aif ',

# line segment absolute rhythm durations
'tie r cs,(ls,e,(ru,10,30),(ru,.05,.25),(ru,.05,.25))',
'tie x5 ru,0,10',

# initial and final audio playback rate
'tie x7 mv,a{1}b{.75}c{.5}d{.2}e{2}:{a=6|b=3|c=2|d=1|e=1}',
'tie x8 mv,a{1}b{.75}c{.5}d{.2}e{2}:{a=6|b=3|c=2|d=1|e=1}',

# panning controlled by fractional noise with infrequent zero-order Markov controlled jumps out of 1/f2 to 1/f0
'tie n n,100,(mv,a{2}b{0}:{a=12|b=1}),0,1',

'ticp a b',

]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



