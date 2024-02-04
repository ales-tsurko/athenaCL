import unittest, doctest


def main(*testClasses):
    """ """

    if "noDocTest" in testClasses:
        s1 = unittest.TestSuite()
    else:
        s1 = doctest.DocTestSuite(
            "__main__", optionflags=(doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
        )

    for thisClass in testClasses:
        if isinstance(thisClass, str) and thisClass == "noDocTest":
            pass
        else:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(thisClass)
            s1.addTests(s2)
    runner = unittest.TextTestRunner()
    runner.run(s1)


if __name__ == "__main__":
    main(Test)
