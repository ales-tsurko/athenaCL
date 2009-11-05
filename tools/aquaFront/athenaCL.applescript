-- athenaCL.applescript
-- athenaCL
-- Created by Christopher Ariza.

property athenaclToolPath : "/usr/local/bin/athenacl"
property pythonPath : "/usr/bin/pythonw" --used as default
property csoundPath : "/usr/local/bin/csound" --used as default in package
property shellPath : "/bin/sh" -- shell to use when passing command to terminal to start ath
-- this is the same for all posix plats
property terminalAppearance : "Custom" -- either Custom or Default
-- /usr/local/bin is created by setup script if needed
property termSetupRow : 10 -- terminal config information
property termSetupCol : 80
property termSetupTitle : "athenaCL setup"
property termLaunchRow : 50
property termLaunchCol : 100
property termLaunchTitle : "athenaCL"
property dirError : "This is not the athenaCL folder. Try again."
property loaderError : "Before athenaCL can be launched, setup must be run. Select the \"Setup\" button and try again."
property csoundError : "There is already a csound in this location. Continue?"

-- ################################################################################
-- ################################################################################

-- #### subroutines
-- #### test if a file exists by couting lines
on checkExtantFile(testPath)
	try
		set dummyStr to do shell script "wc -l " & testPath
	on error
		return 0 -- doesnt exist
	end try
	if dummyStr is not equal to "" then
		return 1
	else
		return 0
	end if
end checkExtantFile


-- #### see if path is to athenaCL directory
-- if setup.py exists, assume this is teh toplevel athenaCL dir
on checkAthDir(pathString)
	if pathString ends with "athenaCL" then
		set testPath to pathString & "/setup.py"
		set resultNum to checkExtantFile(testPath) -- return 1 if file exists, 0, otherwise
		-- dir may be specified with .. folowing the .app
	else if pathString ends with "athenaCL.app/.." then
		set testPath to pathString & "/setup.py"
		set resultNum to checkExtantFile(testPath) -- return 1 if file exists, 0, otherwise
	else
		set resultNum to 0
	end if
	return resultNum
end checkAthDir

--### checks to see if the loader is present
on checkAthShLoader()
	set resultNum to checkExtantFile(athenaclToolPath) -- return 1 if file exists, 0, otherwise
	return resultNum
end checkAthShLoader

--### checks if python is working and extant
on checkPython(pyPath)
	try -- call python with a trivial command
		set testVersionStr to do shell script pyPath & " -c \"print 1\""
		set testVersionStr to testVersionStr as string
	on error
		return 0
	end try
	if testVersionStr starts with "1" then
		return 1
	else
		return 0
	end if
end checkPython

--### gives an error about a bad python
on msgBadPython(pyPath)
	-- call python from cmd line and get verison number
	set msgStr to "There is no Python at " & pyPath & ". Please select a different Python, or install MacPython 2.3 for MacOS X, available for download by clicking \"Get Python\" below."
	display dialog msgStr
end msgBadPython


-- ### gets file paths
on findAthDir()
	--	set theUnixPath to "/Users/Shared/"
	--(POSIX file theUnixPath) as string
	--> "Macintosh HD:Users:Shared:"
	
	--set theMacOSXPath to "Macintosh HD:Users:Shared:"
	--POSIX path of theMacOSXPath
	--> "/Users/Shared/"
	
	-- this gets athenaCL.app parent dir
	set appPath to (path to me from user domain) as text
	set scriptPath to POSIX path of appPath
	if scriptPath ends with "athenaCL.app" then -- as it should
		set scriptPath to scriptPath & "/.."
	else if scriptPath ends with "athenaCL.app/" then
		set scriptPath to scriptPath & ".."
	end if
	return scriptPath
end findAthDir

-- #### open a terminal window and call a command
-- #### uses standard settings, changes size and title
on terminalCmd(cmd, winTitle, winRow, winCol)
	tell application "Terminal"
		activate
		do script with command cmd
		tell window 1
			set number of rows to winRow
			set number of columns to winCol
			set title displays custom title to true
			set custom title to winTitle
		end tell
	end tell
end terminalCmd

-- let user manually select the athenaCL dir
on manualSelectAthDir(startPath)
	-- script path used as init directory
	-- returns a list of theResult, pathNames
	set panelInitDir to startPath -- "~"
	tell open panel
		-- panal data
		set title to "Select the athenaCL folder"
		set prompt to "Select"
		set treat packages as directories to 0
		set can choose directories to 1
		set can choose files to 0
		set allows multiple selection to 0
	end tell
	-- open panel and get dir
	set theResult to display open panel in directory panelInitDir
	-- convert dir to correct format
	if theResult is 1 then -- the user selected a dir
		-- For some unknown (as of yet) you must coerce the 'path names' to a list 
		set the pathNames to (path names of open panel as list)
		-- Convert the list into a list of strings separated by return characters 
		set AppleScript's text item delimiters to return
		set the pathNames to pathNames as string
		set AppleScript's text item delimiters to ""
		-- check if dir is right dir
		set foundAth to checkAthDir(pathNames)
		if foundAth is not equal to 1 then
			set theResult to 0 -- this stops the setup script from running
			display dialog dirError
		end if
	else -- no path gotten from user
		set pathNames to "" -- not used if empty
	end if
	return {theResult, pathNames}
end manualSelectAthDir

-- ################################################################################
-- ################################################################################

-- #### main commands
-- #### install csound lcoated in athenaCL.app/Contents/Rsources/csoundCLI.dmg
-- this is no longer desirable, simply use a link
-- on installCsound()
-- 	set testExtant to checkExtantFile(csoundPath)
-- 	if testExtant is equal to 1 then -- if does exist
-- 		display dialog csoundError -- a cancel selection will fall out of function
-- 	end if
-- 	set testExtant to 0 -- this will overwrite existing csound
-- 	if testExtant is equal to 0 then -- does not exist, install
-- 		set scriptPath to findAthDir()
-- 		set csoundDmgPath to scriptPath & "/athenaCL.app/Contents/Resources/csoundCLI.dmg"
-- 		-- display dialog csoundPath --debug window
-- 		do shell script "hdiutil attach " & csoundDmgPath -- load the disk image
-- 		do shell script "sleep 2; open /Volumes/csoundCLI/csoundCLI.pkg" -- launch installer
-- 	end if
-- end installCsound


-- #### setup script
on setupAth()
	set scriptPath to findAthDir()
	set autoFoundDir to checkAthDir(scriptPath)
	
	set pyStats to checkPython(pythonPath)
	if pyStats is equal to 0 then
		msgBadPython(pythonPath) -- display error message
		set autoFoundDir to -1 -- this overrides the ath dir finding and quits setup
	end if
	
	if autoFoundDir is equal to -1 then -- need to abort completely
		set theResult to 0 -- this stops the setup script from running
	else if autoFoundDir is equal to 0 then -- get dir from user
		-- script path used as init directory
		-- returns a list of theResult, pathNames
		set dataList to manualSelectAthDir(scriptPath)
		set theResult to first item in dataList
		set pathNames to second item in dataList
	else
		set theResult to 1 -- already have dir
		set pathNames to scriptPath
	end if
	
	if theResult is 1 then -- run the setup script, only if ath dir is found
		set setupScript to ("cd " & pathNames & "; " & pythonPath & " setup.py tool; sleep 4; exit")
		terminalCmd(setupScript, termSetupTitle, termSetupRow, termSetupCol)
	end if
end setupAth

-- #### launcher for athenacl
on launchAth(useStartupArgs)
	set launchScript to (shellPath & " " & athenaclToolPath & " " & useStartupArgs & "; exit")
	terminalCmd(launchScript, termLaunchTitle, termLaunchRow, termLaunchCol)
	-- use the custom athenacl.term -- will NOT be able to pass args
end launchAth



-- ################################################################################
-- ################################################################################

-- #### main events
-- #### when an object is clicked
on clicked theObject
	tell window of theObject
		-- set useTermDefault to contents of button "useTermDefault" as boolean
		-- in gui turn off event handlers
		set useStartupArgs to contents of text field "textEntryArgs" as string
	end tell
	if the name of the theObject is "buttonSetup" then -- setup script
		setupAth()
	else if name of the theObject is "buttonStart" then -- startup script
		-- check to see if there is a loader in /usr/local/bin
		set foundLoader to checkAthShLoader()
		if foundLoader is not equal to 1 then -- not found
			display dialog loaderError
		else
			launchAth(useStartupArgs)
		end if
	else if name of the theObject is "buttonInstallCsound" then -- csound installer
		-- installCsound()
		open location "http://sourceforge.net/project/showfiles.php?group_id=81968"
	else if name of the theObject is "buttonInstallPython" then
		open location "http://www.python.org/download/"
	end if
end clicked

-- #### menu items
on choose menu item theObject
	if name of the theObject is "menuWebsiteAthena" then
		open location "http://www.athenacl.org"
	else if name of the theObject is "menuHelp" then
		open location "http://www.flexatone.net/athenaDocs"
	else if name of the theObject is "pythonSelector" then
		set pythonPath to title of popup button "pythonSelector" of (window of theObject)
	end if
end choose menu item

on update menu item theObject
	-- Called periodically when the state of a menu item may need to be updated. 
	-- The handler should return true to enable the menu item or false to disable it
	return true
end update menu item

-- ################################################################################
-- ################################################################################
-- unused events

on action theObject
	(*Add your script here.*)
end action

on closed theObject
	(*Add your script here.*)
end closed

on should close theObject
	(*Add your script here.*)
end should close

on will open theObject
	(*Add your script here.*)
end will open

on opened theObject
	(*Add your script here.*)
end opened

on will resize theObject proposed size proposedSize
	(*Add your script here.*)
end will resize

on will close theObject
	(*Add your script here.*)
end will close

on should open theObject
	(*Add your script here.*)
end should open

on awake from nib theObject
	(*Add your script here.*)
end awake from nib

