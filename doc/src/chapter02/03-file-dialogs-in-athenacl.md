## File Dialogs in athenaCL

The athenaCL system supports a variety of styles of file dialogs, or the interface used to obtain and write files or directories. The default style of file dialog uses a custom text interface that lets the user browse their file system. Alternatively, all commands that require file or directory paths may be executed by supplying the complete file path as a command-line argument.
      
Use of text-base file dialogs, however, may not be convenient for some users. For this reason athenaCL offers GUI-based graphical file dialogs on platforms and environments that support such features. On Python installations that have the Tk GUI library TkInter installed, Tk-based file dialogs are available. On the Macintosh platform (OS9 and OSX) native MacOS file-dialogs are available. To change they athenaCL dialog style, enter the command APdlg:
      

**Changing the file dialog style with APdlg**

```
pi{}ti{} :: apdlg
active dialog visual method: text.
select text, tk, or mac. (t, k, or m): t
dialog visual method changed to text.
```

Note: on some platforms use of GUI windows from inside a text-environment may cause unexpected results. In some cases, the GUI window may appear behind all other windows, in the background.
      
