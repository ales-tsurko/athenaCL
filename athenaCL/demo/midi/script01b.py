# Configuring Time Range

from athenaCL.libATH import athenaObj
ath = athenaObj.Interpreter()


ath.cmd('emo mp')
 
ath.cmd('tin a 45') 
ath.cmd('tie t 0,20') 
ath.cmd('tie a rb,.3,.3,.4,.8') 
ath.cmd('tie r pt,(c,4),(bg,oc,(3,3,2)),(c,1)') 

ath.cmd('tin b 65') 
ath.cmd('tie t 10,20') 
ath.cmd('tie a re,15,.3,1') 
ath.cmd('tie r pt,(bg,rp,(2,1,1,1)),(c,1),(c,1)') 

ath.cmd('tin c 67') 
ath.cmd('tie t 15,25') 
ath.cmd('tie a rb,.1,.1,.4,.6') 
ath.cmd('tie r cs,(rb,.2,.2,.01,1.5)') 

ath.cmd('eln') 
ath.cmd('elh') 