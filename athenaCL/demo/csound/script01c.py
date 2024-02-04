# A Sample Playback Instrument

from athenaCL.libATH import athenaObj

cmd = [
    "emo cn",
    "tin a 32",
    # set a file path to an audio file
    "tie x6 cf,/Volumes/xdisc/_sync/_x/src/martingale/martingale/audio/29561.aif",
    # line segment absolute rhythm durations
    "tie r cs,(ls,e,(ru,5,30),(ru,.03,.15),(ru,.03,.15))",
    # start position within audio file in seconds
    "tie x5 ru,0,40",
    "tie a ls,e,(bg,rc,(3,5,20)),.1,1",
    "tie x2 whps,e,(bg,rp,(5,10,20,2,10)),0,100,10000",
]


def main(cmdList=[], fp=None, hear=True, render=True):
    ath = athenaObj.Interpreter()

    for line in cmdList:
        ath.cmd(line)

    if fp == None:
        ath.cmd("eln")
    else:
        ath.cmd("eln %s" % fp)

    if render:
        ath.cmd("elr")

    if hear:
        ath.cmd("elh")


if __name__ == "__main__":
    main(cmd)
