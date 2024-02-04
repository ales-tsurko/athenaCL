import copy, types, random, importlib, sys, os
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
            module_spec = importlib.util.spec_from_file_location(modName, fp)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            # pass command lines to main function

            fpDst = os.path.join(fpDir, modName + ".xml")
            module.main(module.cmd, fp=fpDst, hear=False)

    @unittest.skip("some scripts relies on audio files not presented in the source code")
    def testDemoWriteCsound(self):
        from athenaCL.libATH import athenaObj

        ao = athenaObj.AthenaObject()

        for fp in ao.external.getFilePathDemo(["csound"], [".py"]):
            environment.printDebug(["processing:", fp])

            fpDir, fn = os.path.split(fp)
            modName = fn.replace(".py", "")
            module_spec = importlib.util.spec_from_file_location(modName, fp)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            # pass command lines to main function

            fpDst = os.path.join(fpDir, modName + ".xml")
            # remove midi file
            module.main(["eorm mf", "eoo cd"] + module.cmd, fp=fpDst, render=True, hear=False)


# -------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDemoMIDI(self):
        "test all midi demos, without writing event lists"
        from athenaCL.libATH import athenaObj

        ao = athenaObj.AthenaObject()
        
        for fp in ao.external.getFilePathDemo(["midi"], [".py"]):
            ath = athenaObj.Interpreter()
            ath.cmd("apr off")

            fpDir, fn = os.path.split(fp)
            modName = fn.replace(".py", "")
            environment.printDebug(["processing:", fp])

            module_spec = importlib.util.spec_from_file_location(modName, fp)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)

            for line in module.cmd:
                ath.cmd(line)


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    from athenaCL.test import baseTest

    if len(sys.argv) == 1:  # normal conditions
        baseTest.main(Test)

    elif len(sys.argv) > 1:
        a = TestExternal()

        # a.testDemoWriteMIDI()
        # a.testDemoWriteCsound()
        a.runTest()
