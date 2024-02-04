# Evolving African Drum Patterns with a GA: Two Durations

from athenaCL.libATH import athenaObj

cmd = [
    "emo mp",
    "tmo lg",
    "tin a 61",
    # bell line, set to loop
    "tie r l,[(4,4,1),(4,4,1),(4,2,1),(4,4,1),(4,4,1),(4,4,1),(4,2,1)]",
    # accent the first of each articulation
    "tie a bg,oc,(1,.5,.5,.5,.5,.5,.5)",
    "tin b 68",
    # create genetic variations using a high mutation rate
    "tie r gr,[(4,4,1),(4,4,1),(4,2,1),(4,4,1),(4,4,1),(4,4,1),(4,2,1)],.7,.25,0",
    "tie a bg,oc,(1,.5,.5,.5,.5,.5,.5)",
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
