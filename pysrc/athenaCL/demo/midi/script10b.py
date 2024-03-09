# Feedback System as Path Index Values

from athenaCL.libATH import athenaObj


cmd = [
    "emo m",
    # create a single, large Multiset using a sieve
    "pin a 5@1|7@4,c2,c7",
    "tmo ha",
    "tin a 107",
    # constant rhythm
    "tie r pt,(c,4),(c,1),(c,1)",
    # select only Multiset 0
    "tie d0 c,0",
    # create only 1 simultaneity from each multiset; create only 1-element simultaneities
    "tie d2 c,1",
    "tie d3 c,1",
    # select pitches from Multiset using Thermostat
    "tie d1 fml,t,(bg,rc,(1,1.5,2)),(c,.7),0,18",
    # select pitches from Multiset using Climate Control
    "tie d1 fml,cc,(bg,rc,(.5,1,1.5)),(c,.7),0,18",
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
