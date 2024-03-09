# Building an Extended Rhythmic Line with Canonic Imitation


from athenaCL.libATH import athenaObj

cmd = [
    "emo mp",
    "tin a 77",
    "tie r pt,(c,1),(c,1),(c,1)",
    "tin b 67",
    "tie r pt,(bg,oc,(2,4,1)),(bg,oc,(3,5,1,7,1,3)),(c,1) ",
    "ticp b b1",
    "tie t 0.125,20.125",
    "tie i 60",
    "ticp b b2",
    "tie t 0.25,20.25",
    "tie i 68",
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
