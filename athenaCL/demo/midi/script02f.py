# Building an Extended Rhythmic Line with Fixed Tempo Phasing

from athenaCL.libATH import athenaObj

cmd = [
    "emo mp",
    "tin a 70",
    "tie r pt,(bg,oc,(2,4,4)),(bg,oc,(4,1,1,2,1)),(c,1) ",
    "tie t 0,60",
    "ticp a a1",
    "tie b c,124",
    "ticp a a2",
    "tie b c,128",
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
