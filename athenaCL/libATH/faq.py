#!/usr/local/bin/python
#-----------------------------------------------------------------||||||||||||--
# Name:          faq.py
# Purpose:       athenaCL frequently asked questions.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
#-----------------------------------------------------------------||||||||||||--

import unittest, doctest




class FaqDictionary:

    def __init__(self):
        """
        >>> a = FaqDictionary()
        """
        self.keyList = range(1,30) # increase number for new entries

        self.groupTitleDict = {'general': 'General Information',
              'install': 'Installing, Starting, and Uninstalling athenaCL',
                                      'usage' : 'Using and Configuring athenaCL',
                                      }
        self.groupList = self.groupTitleDict.keys()

        self.faqDict = {}
        for number in self.keyList:
            self.faqDict[('faq%i' % number)] = eval(('Faq%i()' % number))
            if self.faqDict[('faq%i' % number)].group == '':
                del self.faqDict[('faq%i' % number)] # delete empty entries

    def sortKeys(self):
        keyQuaryList = []
        for entry in self.faqDict.keys():
            keyQuaryList.append((self.faqDict[entry].query, entry))
        keyQuaryList.sort()
        keyIds = []
        for entry in keyQuaryList:
            keyIds.append(entry[1]) # makes list of numbers
        return keyIds

    def searchQuery(self, query):
        for entry in self.faqDict.keys():
            if query.lower() in self.faqDict[entry].query.lower():
                return self.faqDict[entry].query, self.faqDict[entry].answer
        return None, None # if nothing found


    def getLinks(self):
        strGeneral = '\n<B>%s</B><BR>\n'         % self.groupTitleDict['general']
        strInstall = '\n<BR><B>%s</B><BR>\n' % self.groupTitleDict['install']
        faqKeys = self.sortKeys()
        for entry in faqKeys:
            if self.faqDict[entry].group == 'general':
                strGeneral = strGeneral + self.faqDict[entry].getFaqLink()
            elif self.faqDict[entry].group == 'install':
                strInstall = strInstall + self.faqDict[entry].getFaqLink()
        message = strGeneral + strInstall
        message = message + '<BR>'
        return message

    def getBodyHtml(self):
        strGeneral = '\n<B>%s</B><BR>\n'         % self.groupTitleDict['general']
        strInstall = '\n<BR><B>%s</B><BR>\n' % self.groupTitleDict['install']
        faqKeys = self.sortKeys()
        for entry in faqKeys:
            if self.faqDict[entry].group == 'general':
                strGeneral = strGeneral + self.faqDict[entry].getFaqEntryHtml()
            elif self.faqDict[entry].group == 'install':
                strInstall = strInstall + self.faqDict[entry].getFaqEntryHtml()
        message = strGeneral + strInstall
        return message

    def getBodySgml(self):
        strGeneral = '''
    <qandaset defaultlabel='qanda'>
        <title>%s</title>
''' % self.groupTitleDict['general']
        strInstall = '''
    <qandaset defaultlabel='qanda'>
        <title>%s</title>
''' % self.groupTitleDict['install']

        faqKeys = self.sortKeys()
        for entry in faqKeys:
            if self.faqDict[entry].group == 'general':
                strGeneral = strGeneral + self.faqDict[entry].getFaqEntrySgml()
            elif self.faqDict[entry].group == 'install':
                strInstall = strInstall + self.faqDict[entry].getFaqEntrySgml()
        message = strGeneral + '\n    </qandaset>\n' + strInstall + '\n   </qandaset>\n'
        return message


#-----------------------------------------------------------------||||||||||||--
class FaqEntry:
    def __init__(self):
        pass

    def getQuary(self):
        return self.query

    def getAnswer(self):
        return self.answer

    def getHeaderHtml(self):
        refString = 'faq%i' % self.id
        return '<A NAME="%s"></A>\n' % refString
        
    def getQuaryHtml(self):
        return '<B>%s</B><BR>\n' % self.query
        
    def getAnswerHtml(self):
        return self.answer + '<BR>\n'
        
    def getDividerHtml(self):
        return '<A HREF="#top"><IMG SRC="images/top3.gif" ALT="[pageIndex]" BORDER=0 WIDTH=19></A><BR><BR>\n\n'

    def getFaqEntryHtml(self):
        text = self.getHeaderHtml()
        text = text + self.getQuaryHtml()
        text = text + self.getAnswerHtml()
        text = text + self.getDividerHtml()
        return text
        
    def getFaqEntrySgml(self):
        msg = '''
        <qandaentry>
            <question><para>%s</para></question>
            <answer><para>%s</para></answer>
        </qandaentry>
''' % (self.getQuary(), self.getAnswer())
        return msg

    def getFaqLink(self):
        text = '<A HREF="#faq%i">%s</A><BR>\n' % (self.id, self.query)
        return text



#-----------------------------------------------------------------||||||||||||--



class Faq1(FaqEntry):
    id       = 1
    group    = 'general'
    query    = 'What does athenaCL do?'
    answer = "athenaCL is a tool for computer-aided algorithmic composition, producing outputs for Csound, MIDI, and various other formats."

class Faq2(FaqEntry):
    id       = 2
    group    = 'general'
    query    = 'What is an interactive command-line program?'
    answer = 'athenaCL is an interactive command line program, which means that instead of using windows, buttons, and the mouse to get things done, the user enters commands and sees text displays. athenaCL is interactive in that, rather than having to give commands with complicated arguments and flags, users are prompted for each entry needed. Unix programs such as Pine and FTP are also interactive command-line programs. Users of UNIX-like operating systems will be familiar with this interface, whereas users of GUI-based operating systems such as Macintosh and Windows may find this interface challenging at first. The athenaCL system is designed to be as intuitive and user friendly as possible; knowledge of programming, UNIX, or other command-line programs, although helpful, is in no way required.'
    
    
class Faq3(FaqEntry):
    id       = 3
    group    = 'general'
    query    = 'How much does athenaCL cost?'
    answer = 'athenaCL is a free and open source software project. There is no cost or licensing fee associated with this software.'

class Faq4(FaqEntry):
    id       = 4
    group    = 'install'
    query    = 'What platforms does athenaCL run on?'
    answer = 'Because of the cross-platform foundations of the Python programming language, athenaCL runs on every modern platform that Python runs on. This includes Mac OSX, Windows, Linux, BSD and all UNIX-based systems.'

class Faq5(FaqEntry):
    id       = 5
    group    = 'general'
    query    = 'What is Python?'
    answer = 'Python is a programming language. Python is a high-level, object-oriented language that is cross-platform, free, and open source.'

class Faq6(FaqEntry):
    id       = 6
    group    = 'general'
    query    = 'Who is athenaCL designed for?'
    answer = 'athenaCL is designed for use by musicians, composers, sound designers, and programmers. Basic familiarity with stochastics, computer music concepts, and output formats (MIDI, Csound) is helpful.'

class Faq7(FaqEntry):
    id       = 7
    group    = 'general'
    query    = 'Where is the source code?'
    answer = 'Every distribution download of athenaCL comes with a complete copy of the source code. Since Python is an interpreted language, the source code can be run "live": there is no executable or binary of athenaCL, the source-code simply runs in the Python interpreter. Developers can get (with SVN) the most recent source at SourceForge (http://code.google.com/p/athenacl/). An athenaCL.exe installer is available; this installs athenaCL as a Python package, and is not the athenaCL program itself.'

class Faq8(FaqEntry):
    id       = 8
    group    = 'install'
    query    = 'Is Python required to use athenaCL?'
    answer = 'Python is required for athenaCL to run, and is not distributed with athenaCL. Python is free, runs on every platform, and comes in easy-to-use installers. Many advanced operating systems (UNIX-based operating systems including GNU/Linux and MacOS X) ship with Python installed. Visit www.python.org for more information and downloads. '

class Faq9(FaqEntry):
    id       = 9
    group    = 'install'
    query    = 'Is Csound required to use athenaCL?'
    answer = 'Csound is only required for rendering audio with athenaCL\'s built-in library of Csound instrument; MIDI files, as well as other output formats, can always be produced without Csound. Csound is a free, cross-platform tool that renders audio based on instrument definitions in a "orchestra" file and music definitions in a "score" file. As athenaCL provides an integrated library of Csound instruments, no knowledge of Csound is required to use athenaCL.'

class Faq10(FaqEntry):
    id       = 10
    group    = 'general'
    query    = 'Can users add Csound instruments to athenaCL?'
    answer = 'Users can create athenaCL-generated eventLists (scores) with any number of parameter values, allowing the use of external Csound instrument definitions of any complexity.'

class Faq11(FaqEntry):
    id       = 11
    group    = 'usage'
    query    = 'When I use the arrow keys, why do I get strange output (such as "^[[A" or "^[[D"), or why is readline not working?'
    answer = 'On POSIX (UNIX-like) operating systems such as Linux, BSD, and Mac OSX, the readline package is used within athenaCL to provide session command-line history with the keyboard arrow keys. Some Python installations (such as the stock Python at /usr/bin/python shipped with Mac OSX) may not have readline support. The readline package is widely available and can be easily installed.'

class Faq12(FaqEntry):
    id       = 12
    group    = 'general'
    query    = 'How can I contribute to this project?'
    answer = 'If you are a developer and wish to contribute code, add new features, or fix bugs in athenaCL, contact Christopher Ariza via email.'

class Faq13(FaqEntry):
    id       = 13
    group    = 'general'
    query    = 'I have found a bug; what do i do?'
    answer = 'Report it: the athenaCL interpreter features an integrated bug-reporting system. When quitting athenaCL while an internet connection is available, users may anonymously submit the bug-report.'

class Faq14(FaqEntry):
    id       = 14
    group    = 'general'
    query    = 'Where can I ask questions about athenaCL?'
    answer = 'The athenacl-development list is for users and developers of athenaCL, and can be used to ask questions, get help, or discuss issues related to athenaCL. Users can subscribe and un-subscribe from this list here: http://lists.sourceforge.net/lists/listinfo/athenacl-development. To prevent spam, you must join this list to send messages. All questions are welcome. Alternatively, users may contact Christopher Ariza directly.'

class Faq15(FaqEntry):
    id       = 15
    group    = 'install'
    query    = 'Where is the .exe? how do I start a program without a .exe?'
    answer = 'There is no .exe file. Rather than having an executable binary, athenaCL runs in the Python interpreter. Python is a free programming language available at http://www.python.org. After installing Python, you can launch athenaCL simply by double clicking the file "athenaCL.py"; for more information see the file "README.txt" in the athenaCL directory.'

class Faq16(FaqEntry):
    id       = 16
    group    = 'usage'
    query    = 'Can athenaCL produce a Csound CSD XML combined orchestra and score file format?'
    answer = 'Yes. CSD output is activated as an athenaCL EventOutput configuration. Use EOo to select EventOutput "csoundData": this will cause all scores and orchestras to be written as a single, combined CSD XML file.'

class Faq17(FaqEntry):
    id       = 17
    group    = 'install'
    query    = 'How do I uninstall athenaCL?'
    answer = 'To uninstall an athenaCL distribution, in most cases all that is necessary is to delete the athenaCL folder. Windows users who have used an athenaCL installer (athenaCL.exe) will be able to remove athenaCL with the Windows "Add or Remove Programs" Control Panel. On POSIX (UNIX-like) operating systems such as Linux, BSD, and Mac OSX, athenaCL may write a standard configuration file in the user\'s home directory: ~/.athenaclrc; if an error has occurred during an athenaCL session, a log may be stored in the user\'s home directory: ~/.athenacl-log; and if the user selected to install the optional athenaCL launcher tool, a script will be found in /usr/local/bin: /usr/local/bin/athenacl. All of these can be removed py using the setup.py script with the argument "uninstall".'

class Faq18(FaqEntry): # 
    id       = 18
    group    = ''
    query    = ''
    answer = ''

class Faq19(FaqEntry):
    id       = 19
    group    = ''
    query    = ''
    answer = ''

class Faq20(FaqEntry):
    id       = 20
    group    = ''
    query    = ''
    answer = ''

class Faq21(FaqEntry):
    id       = 21
    group    = ''
    query    = ''
    answer = ''

class Faq22(FaqEntry):
    id       = 22
    group    = ''
    query    = ''
    answer = ''

class Faq23(FaqEntry):
    id       = 23
    group    = ''
    query    = ''
    answer = ''

class Faq24(FaqEntry):
    id       = 24
    group    = ''
    query    = ''
    answer = ''

class Faq25(FaqEntry):
    id       = 25
    group    = ''
    query    = ''
    answer = ''

class Faq26(FaqEntry):
    id       = 26
    group    = ''
    query    = ''
    answer = ''

class Faq27(FaqEntry):
    id       = 27
    group    = ''
    query    = ''
    answer = ''

class Faq28(FaqEntry):
    id       = 28
    group    = ''
    query    = ''
    answer = ''

class Faq29(FaqEntry):
    id       = 29
    group    = ''
    query    = ''
    answer = ''



  


#-----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
            
    def testDummy(self):
        self.assertEqual(True, True)


#-----------------------------------------------------------------||||||||||||--



if __name__ == '__main__':
    from athenaCL.test import baseTest
    baseTest.main(Test)

