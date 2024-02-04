# Evolving African Drum Patterns with a GA: Multiple Rhythmic Values


from athenaCL.libATH import athenaObj

cmd = [
    "emo mp",
    "tmo lg",
    "tin a 45",
    "tie r gr,[(4,4,1),(4,4,1),(4,2,1),(4,4,1),(4,4,1),(4,4,1),(4,2,1)],.7,.15,0",
    "tie a bg,oc,(1,.5,.5,.5,.5,.5,.5)",
    "tin b 60",
    # create genetic variations using a high crossover, no mutation
    "tie r gr,[(4,2,0),(4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1),(4,2,0), (4,2,1),(4,2,1),(4,2,0),(4,2,1),(4,2,1)],1,0,0",
    "tie a bg,oc,(.5,1,.5, .5,.5,.5, .5,.5,.5, .5,.5,.5)",
    # turning on silence mode will use parameters even for rests
    "timode s on",
    "tin c 68",
    # create genetic variations using a high crossover and mutation rate and some elitism
    "tie r gr,[(4,3,1),(4,1,1),(4,2,1),(4,2,1),(4,1,1),(4,1,1),(4,2,1), (4,3,1),(4,1,1),(4,2,1),(4,2,1),(4,1,1),(4,1,1),(4,2,1)],.9,.25,0.1",
    "tie a bg,oc,(1,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5)",
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
