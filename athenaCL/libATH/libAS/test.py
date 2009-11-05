
from athenaCL.libATH.libAS import script

class Script(script.AthenaScript):

    def __init__(self, scriptArgs):
        script.AthenaScript.__init__(self, scriptArgs)
        
        # import all modules
        from athenaCL.libATH.libAS import testGeneral
        from athenaCL.libATH.libAS import testClone
        
        # pack all cmds together
        self.cmdList = []
        # thist test consists fo multiple tests
        for mod in [testGeneral, testClone]:
            obj = mod.Script(scriptArgs)
            self.cmdList = self.cmdList + list(obj.cmdList)
