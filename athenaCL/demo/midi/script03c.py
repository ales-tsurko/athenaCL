# Tendency Mask: Random Values between Triangle Generators

from athenaCL.libATH import athenaObj

cmd = [
    "emo m",
    "pin a d,e,g,a,b",
    "tin a 107  ",
    "tie r pt,(c,16),(ig,(bg,rc,(1,2,3,5,7)),(bg,rc,(3,6,9,12))),(c,1)",
    "tie o ru,(wt,t,25,0,-2,4),(wt,t,20,0,-3,1)",
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
