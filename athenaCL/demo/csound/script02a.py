# Composing with Densities using TM TimeFill and a Noise Instrument


from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()

ath.cmd('emo cn')
 
cmd = [
'tmo tf',
'tin a 80',
'tie t 0,30',
# total event count is defined as static texture parameter, not a ParameterObject
'tie s3 600',
# start position within texture normalized within unit interval
'tie d0 rb,.3,.3,0,1',
# durations are independent of start time
'tie r cs,(mv,a{.01}b{1.5}c{3}:{a=20|b=1|c=1})',
'tie a ru,.5,.9',

]

for line in cmd:
    ath.cmd(line)

ath.cmd('eln') 
ath.cmd('elr') 
ath.cmd('elh') 



