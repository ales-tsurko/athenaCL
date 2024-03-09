# The CA as a Generator of Rhythms


from athenaCL.libATH import athenaObj

cmd = [
    "emo mp",
    "tin a 47",
    # set the multiplier to the integer output of CaList
    "tie r pt,(c,4),(cl,f{s}k{2}r{1}x{81}y{120}w{6}c{0}s{0},109,.05,sumRowActive,oc),(c,1)",
    # set the amplitude to the floating point output of CaValue
    "tie a cv,f{s}k{2}r{1}x{81}y{120}w{6}c{8}s{0},109,.05,sumRowActive,.2,1",
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
