# Markov-Based Value Generation

from athenaCL.libATH import athenaObj

cmd = [
    "emo m",
    "tin a 26",
    # rhythm generated with absolute values via ConvertSecond and a dynamic WaveHalfPeriodSine generator
    "tie r cs,(whps,e,(bg,rp,(5,10,15,20)),0,.200,.050)",
    # first-order selection
    #'tie f mv,a{2}b{4}c{7}d{9}e{11}:{a=1|b=3|c=1|d=3|e=1}a:{a=9|e=1}b:{a=3|c=1}c:{b=3|d=1}d:{c=3|e=1}e:{d=1},(c,1)',
    # dynamic first and zero order selection
    "tie f mv,a{2}b{4}c{7}d{9}e{11}:{a=1|b=3|c=1|d=3|e=1}a:{a=9|e=1}b:{a=3|c=1}c:{b=3|d=1}d:{c=3|e=1}e:{d=1},(wp,e,100,0,1,0)",
    # zero-order Markov amplitude values
    #'tie a mv,a{.4}b{.6}c{.8}d{1}:{a=6|b=4|c=3|d=1}',
    # amplitude values scaled by a dynamic WaveHalfPeriodPulse
    "tie a om,(mv,a{.4}b{.6}c{.8}d{1}:{a=6|b=4|c=3|d=1}),(whpp,e,(bg,rp,(5,15,10)))",
    # octave values are provided by a first-order Markov chain
    "tie o mv,a{0}b{-1}c{-2}d{-3}a:{a=9|d=1}b:{a=3|b=1}c:{b=3|c=1}d:{c=1},(c,1)",
    "tie t 0,60",
]


def main(cmdList=[], fp=None, hear=True):
    ath = athenaObj.Interpreter()

    for line in cmdList:
        ath.cmd(line)

    if fp == None:
        ath.cmd("eln")
    else:
        ath.cmd("eln %s" % fp)

    if hear:
        ath.cmd("elh")


if __name__ == "__main__":
    main(cmd)
