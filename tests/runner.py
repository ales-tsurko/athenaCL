import unittest
import importlib

def load_test_cases(module_names):
    """
    Load test case classes from a list of module names.
    """
    suite = unittest.TestSuite()
    for name in module_names:
        # Dynamically import the module
        module = importlib.import_module(name)
        # Assuming the standard naming convention 'Test' for test cases
        test_case = getattr(module, 'Test', None)
        if test_case and issubclass(test_case, unittest.TestCase):
            suite.addTest(unittest.makeSuite(test_case))
    return suite

def run_tests():
    modules_to_test = [
        'athenaCL.libATH.argTools',
        'athenaCL.libATH.athenaObj',
        'athenaCL.libATH.audioTools',
        'athenaCL.libATH.automata',
        'athenaCL.libATH.chaos',
        'athenaCL.libATH.clone',
        'athenaCL.libATH.command',
        'athenaCL.libATH.dialog',
        'athenaCL.libATH.dice',
        'athenaCL.libATH.drawer',
        'athenaCL.libATH.envelope',
        'athenaCL.libATH.error',
        'athenaCL.libATH.eventList',
        'athenaCL.libATH.faq',
        'athenaCL.libATH.feedback',
        'athenaCL.libATH.fileTools',
        'athenaCL.libATH.fontLibrary',
        'athenaCL.libATH.genetic',
        'athenaCL.libATH.grammar',
        'athenaCL.libATH.help',
        'athenaCL.libATH.htmlTools',
        'athenaCL.libATH.imageTools',
        'athenaCL.libATH.interpolate',
        'athenaCL.libATH.ioTools',
        'athenaCL.libATH.language',
        'athenaCL.libATH.markov',
        'athenaCL.libATH.midiTools',
        'athenaCL.libATH.multiset',
        'athenaCL.libATH.ornament',
        'athenaCL.libATH.osTools',
        'athenaCL.libATH.outFormat',
        'athenaCL.libATH.permutate',
        'athenaCL.libATH.pitchPath',
        'athenaCL.libATH.pitchTools',
        'athenaCL.libATH.prefTools',
        'athenaCL.libATH.quantize',
        'athenaCL.libATH.rhythm',
        'athenaCL.libATH.setTables',
        'athenaCL.libATH.sieve',
        'athenaCL.libATH.spectral',
        'athenaCL.libATH.table',
        'athenaCL.libATH.temperament',
        'athenaCL.libATH.typeset',
        'athenaCL.libATH.unit',
        'athenaCL.libATH.xmlTools',

        'athenaCL.libATH.libOrc.orc',
        'athenaCL.libATH.libPmtr.parameter',
        'athenaCL.libATH.libTM.texture',
        'athenaCL.libATH.omde.bpf',
        'athenaCL.libATH.omde.miscellaneous',
        'athenaCL.libATH.omde.rand',
        
    ]
    suite = load_test_cases(modules_to_test)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


run_tests()
