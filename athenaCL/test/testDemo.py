import copy, types, random, sys, imp, os
import doctest, unittest

_MOD = "testDemo.py"
from athenaCL.libATH import prefTools

environment = prefTools.Environment(_MOD)


def test():
    """Doctest placeholder

    >>> True
    True
    """
    pass


# -------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testDemoWriteMIDI(self):
        from athenaCL.libATH import athenaObj

        ao = athenaObj.AthenaObject()

        for fp in ao.external.getFilePathDemo(["midi"], [".py"]):
            environment.printDebug(["processing:", fp])

            fpDir, fn = os.path.split(fp)
            modName = fn.replace(".py", "")
            file, pathname, description = imp.find_module(modName, [fpDir])
            module = imp.load_module(modName, file, pathname, description)
            # pass command lines to main function

            fpDst = os.path.join(fpDir, modName + ".xml")
            module.main(module.cmd, fp=fpDst, hear=False)

    def testDemoWriteCsound(self):
        from athenaCL.libATH import athenaObj

        ao = athenaObj.AthenaObject()

        for fp in ao.external.getFilePathDemo(["csound"], [".py"]):
            environment.printDebug(["processing:", fp])

            fpDir, fn = os.path.split(fp)
            modName = fn.replace(".py", "")
            file, pathname, description = imp.find_module(modName, [fpDir])
            module = imp.load_module(modName, file, pathname, description)
            # pass command lines to main function

            fpDst = os.path.join(fpDir, modName + ".xml")
            # remove midi file
            module.main(
                ["eorm mf", "eoo cd"] + module.cmd, fp=fpDst, render=True, hear=False
            )


# -------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDemoMIDI(self):
        "test all midi demos, without writing event lists"
        from athenaCL.libATH import athenaObj

        ao = athenaObj.AthenaObject()

        for fp in ao.external.getFilePathDemo(["midi", "csound"], [".py"]):
            # ath = athenaObj.Interpreter()
            # ao = ath.ao
            # ath.cmd('aorm confirm')
            # ath.proc_AOrm(None) # for now, need to manually call aorm

            # best to get a new interpreter
            ath = athenaObj.Interpreter()
            ath.cmd("apr off")

            fpDir, fn = os.path.split(fp)
            modName = fn.replace(".py", "")
            environment.printDebug(["processing:", fp])

            file, pathname, description = imp.find_module(modName, [fpDir])
            module = imp.load_module(modName, file, pathname, description)
            # pass command lines to main function

            for line in module.cmd:
                # environment.printDebug(['line:', line])
                ath.cmd(line)

            # break


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    from athenaCL.test import baseTest

    if len(sys.argv) == 1:  # normal conditions
        baseTest.main(Test)

    elif len(sys.argv) > 1:
        a = TestExternal()

        # a.testDemoWriteMIDI()
        a.testDemoWriteCsound()
        # a.runTest()
