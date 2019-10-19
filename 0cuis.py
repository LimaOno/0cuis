import errno
import os
import shutil
import sys
import glob
import re
import subprocess
import platform

def die(msg):
	print(msg, file=sys.stderr)
	sys.exit(1)

def usage():
	die(sys.argv[0] + """ [OPTIONS] ([ImageFileName] | --) [arguments]
    
    Requires the squeak vm installed and CUISPATH to point to the
    Cuis-Smalltalk-Dev base repository.
    
    OPTIONS are the squeak command options.""")

def writePatch(patch, filename):
	f = open(filename, "w")
	f.write(patch)
	f.close

def getCuisPaths(path):
	if platform.architecture()[0] == '32bit':
		baseName = 'Cuis5.0-????-32'
	else:
		baseName = 'Cuis5.0-????'
	imagePaths = glob.glob(os.path.join(path, baseName + '.image'))
	len(imagePaths) == 1 or die('Error: missing or multiple entry for ' + baseName + '.image')
	changesPaths = glob.glob(os.path.join(path, baseName + '.changes'))
	return ([imagePaths[0], changesPaths[0]])

cuisPatch = """'From Cuis 5.0 of 7 November 2016 [latest update: #3665] on 7 October 2019 at 7:32:57 pm'!
'Description This package contains support for dependencies injection via an appropriate environment variable, and offloading of version numbering in packages to an external tool.'!
!provides: '0cuis' 1 1!
!FeatureRequirement methodsFor: 'private' stamp: 'lo 10/7/2019 15:54:52'!
placesToLookForPackagesDo: aBlock
		"Look into local and environment defined paths to search for packages"
		
	pathName ifNotNil: [ aBlock value: pathName asFileEntry parent ].
	(self primEnvironmentAt: #CUISPATH)
		ifNotNil: [:aString |
			aString asDirectoryEntry allDirectoriesDo: aBlock ].
	(self primEnvironmentAt: #CUISPACKAGESPATH)
		ifNotNil: [:aString |
			(aString findTokens: ':')
				do: [:each |
					| d |
					d := each asDirectoryEntry.
					aBlock value: d.
					d allDirectoriesDo: aBlock ] ].
! !

!FeatureRequirement methodsFor: 'private' stamp: 'lo 10/7/2019 19:32:45'!
primEnvironmentAt: aSymbol
	"Answer the environment string at aSymbol in the OS process environment list.
	This returns a string or nil."

	<primitive: 'primitiveEnvironmentAtSymbol' module: 'UnixOSProcessPlugin'>
	^ nil! !"""

options1 = """-nomixer -vtlock -vtswitch -compositioninput -fullscreen -fullscreenDirect
-headless -iconic -lazy -mapdelbs -nointl -notitle -noxdnd -swapbtn -xasync -xshm -help
-timephases -noevents -nohandlers -pollpip -checkpluginwrites -version -warnpid -tracestores
-reportheadroom -logscavenge -blockonerror -blockonwarn -exitonwarn -notimer -headless
-nodisplay -nomixer -nosound -quartz""".split()

options2 = """-display -maxoldspace -cogminjumps -cogmaxlits -tracestores -codesize -
pathenc -plugins -textenc -stackpages -leakcheck -eden -breakmnu -breaksel -mmap -memory
-encoding -xicfont -optmod -ldtoms -title -glxdebug -display -cmdmod -browserWindow
-msproto -msdev -kbmap -fbdev""".split()

options3 = "-browserPipes".split()


if not ('CUISPATH' in os.environ): die('Error: CUISPATH not set')
cuisPath = os.environ['CUISPATH']
it = iter(sys.argv)
next(it)
try:
	while True:
		current = next(it)
		if current in options1:
			continue
		if current in options2:
			try:
				next(it)
			except StopIteration: usage()
			continue
		if current in options3:
			try:
				next(it)
				next(it)
			except StopIteration: usage()
			continue
		if current == '--': break
		if current[:1] == '-': usage()
		if not os.path.exists(current):
			targetDir = os.path.dirname(current)
			cuisImagePath, cuisChangesPath = getCuisPaths(cuisPath)
			shutil.copy2(cuisImagePath, current)
			os.chmod(current, 0o664)
			currentChanges = re.sub(r"\.image", ".changes", current)
			shutil.copy2(cuisChangesPath, currentChanges)
			os.chmod(currentChanges, 0o664)
			sourcesFileName = os.path.join(targetDir, 'CuisV5.sources')
			if not os.path.exists(sourcesFileName):
				shutil.copy2(os.path.join(cuisPath, 'CuisV5.sources'), sourcesFileName)
			patchFileName = os.path.join(targetDir, '0cuis.pck.st')
			writePatch(cuisPatch, patchFileName)
			subprocess.run(['0install', 'run', 'https://limaono.github.io/OpenSmalltalk.xml',  '-headless', current, '-r' + patchFileName,  '-dSmalltalk snapshot: true andQuit: true'], check=True)
		break
except StopIteration: usage()
os.execvp('0install', ['0install', 'run', 'https://limaono.github.io/OpenSmalltalk.xml'] + sys.argv[1:])