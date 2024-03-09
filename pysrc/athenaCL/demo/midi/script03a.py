# Grouping Selection

from athenaCL.libATH import athenaObj

ath = athenaObj.Interpreter()


cmd = [
    "emo m",
    "tin a 6",
    "tie r cs,(rb,.2,.2,.02,.25)",
    "tie f ig,(bg,rc,(2,4,7,9,11)),(bg,rp,(2,3,5,8,13))",
    "tie o ig,(bg,oc,(-2,-1,0,1)),(ru,20,30)",
    "ticp a b c d",
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
