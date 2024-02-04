# -----------------------------------------------------------------||||||||||||--
# Name:          __init__.py
# Purpose:       manage starting an interactive session
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--


# this works but has the side effect that other imports, such as
# from athenaCL import libATH
# from importlib import reload
# also start interactive sessions
# thus, this is not used

# print('calling athenaCL/__init__.py')
#
# import sys
#
# # permit import athenaCL to start an interactive session
# # this will only work on first import
# # reload(athenaCL) will restart
#
# # note that this module gets run when this:
# # from athenaCL import libATH
# # is run; this, interactive sessions can be mistakenly started
#
# if 'athenaCL.athenacl' in sys.modules.keys():
#     # force a reload if already in keys; otherwise importing athenaCL will
#     # not start an interactive session
#     reload(athenacl)
# else:
#     from athenaCL import athenacl
