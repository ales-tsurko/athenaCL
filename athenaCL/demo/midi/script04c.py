# 1/f Noise in Melodic Generation: HarmonicAssembly

from athenaCL.libATH import athenaObj

ath = athenaObj.Interpreter()


cmd = [
    "emo m",
    "pin a d3,e3,g3,a3,b3,d4,e4,g4,a4,b4,d5,e5,g5,a5,b5",
    "tmo ha",
    "tin a 27",
    "tie r pt,(c,16),(ig,(bg,rc,(1,2,3,5,7)),(bg,rc,(3,6,9,12))),(c,1)",
    "tie a om,(ls,e,9,(ru,.2,1),(ru,.2,1)),(wp,e,23,0,0,1)",
    "tie d0 c,0",
    "tie d1 n,100,2,0,14",
    "tie d2 c,1",
    #'tie d3 c,1',
    "tie d3 ru,1,4",
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
