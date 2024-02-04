# 1/f Noise in Melodic Generation: LineGroove


from athenaCL.libATH import athenaObj

ath = athenaObj.Interpreter()


cmd = [
    "emo m",
    "tmo lg",
    "tin a 108",
    "tie r cs,(ls,e,10,(ru,.01,.2),(ru,.01,.2))",
    "tie f bs,(2,4,7,9,11,14,16,19,21,23),(n,100,1,0,1)",
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
