# Grammar States as Path Index Values

from athenaCL.libATH import athenaObj

cmd = [
    "emo m",
    # create a single, large Multiset using a sieve
    "pin a 5@0|7@2,c2,c7",
    "tmo ha",
    "tin a 6",
    # constant rhythm
    "tie r pt,(c,4),(c,1),(c,1)",
    # select only Multiset 0
    "tie d0 c,0",
    # select pitches from Multiset using accumulated deterministic grammar starting at 12
    "tie d1 a,12,(gt,a{1}b{-1}c{2}d{-2}@a{ab}b{cd}c{ad}d{bc}@ac,10,oc)",
    # create only 1 simultaneity from each multiset; create only 1-element simultaneities
    "tie d2 c,1",
    "tie d3 c,1",
    # four state deterministic applied to amplitude with different start string
    "tie a gt,a{.25}b{.5}c{.75}d{1}@a{ab}b{cd}c{aadd}d{bc}@bbc,6,oc",
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
