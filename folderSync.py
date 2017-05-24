#! python3

'''Program that can sync all files and folders between two chosen folders. 
	I need it to keep my photo-backup updated. 
	But script should be able to sync in both ways. 
	And keep track of changes in both folders.'''

import logging, math, os, platform, time, send2trash, re

logFile = logging.getLogger('fs1') 
#create logger for this specific module for logging to file

logFile.setLevel(logging.DEBUG)
#set level of messages to be logged to file

logConsole = logging.getLogger('fs2')
logConsole.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s %(asctime)s line %(lineno)s: %(message)s') 
#define format of logging messages

if os.path.exists('.\log'):
	''' create new log every time when script starts instead of writing in the same file '''
	timestr = time.strftime('%Y-%m-%d__%Hh%Mm')
	newLogName = os.path.join('log', 'log_' + timestr + '.txt')
	if os.path.exists(newLogName):
		i = 2
		while os.path.exists(os.path.join('log', 'log ' + timestr + 
			'(' + str(i) + ').txt')):
			i += 1
			continue
		file_handler = logging.FileHandler(os.path.join('log', 'log ' + timestr + '(' + str(i) + ').txt'), encoding='utf8')	
	else:
		file_handler = logging.FileHandler(newLogName, encoding='utf8')
else:
	os.mkdir('.\log')
	timestr = time.strftime('%Y-%m-%d__%H-%M-%S')
	file_handler = logging.FileHandler(os.path.join(newLogName, encoding='utf8'))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
#set format to both handlers


logFile.addHandler(file_handler)
logConsole.addHandler(stream_handler)
#apply handler to this module (folderSync.py)


# def prlog(level, message):
# 	#both print and log messages
# 	print(message)
# 	getattr(logFile, level)(message)
# 	#what is above means "logFile.level(message)" where level is method's name which is known only by runtime. For example "logFile.info(message)" where 'info' is coming from variable 

def chooseFolder():
	# used to check validity of file's path given by user
	while True:
		pathToFolder = input('Path: ')
		if not os.path.exists(pathToFolder):
			prlog('This folder doesn\'t exist. Write another one.')
			continue
		if not os.path.isdir(pathToFolder):
			prlog('You should denote path to folder, not to file. Try again.')
			continue	
		elif os.path.exists(pathToFolder) and os.path.isdir(pathToFolder):
			print('Got it!')
			return pathToFolder

def menuChooseFolders():
	# let user choose folders and check them not to have the same path
	while True:
		print('Please, choose first folder to sync.')
		loggerFile.info('Please, choose first folder to sync.')
		firstFolder = chooseFolder()
		print('Please, choose second folder to sync.')
		logFile.info('Please, choose second folder to sync.')
		secondFolder = chooseFolder()
		if firstFolder == secondFolder:
			print('\nPaths can\'t be equal. Start over')
			logFile.info('\nPaths can\'t be equal. Start over')
			continue
		else:
			print('\nPaths accepted. Start analyzing...\n')
			logFile.info('\nPaths accepted. Start analyzing...\n')
			break

	return firstFolder, secondFolder			

def hasItEverBeenSynced(rootFolder):
	# check if there is already snapshot from previous sync
	if os.path.exists(os.path.join(rootFolder, '.folderSync')):
		return True
	else:
		return False	

def getSnapshot(rootFolder):
	# get all file and folder paths, 
	# and collect file size and file time of modification
	print('Getting snapshot of ' + rootFolder + '...')
	logFile.info('Getting snapshot of ' + rootFolder + '...')

	foldersNumber = 0
	filesNumber = 0
	totalSize = 0

	currentSnapshot = {}

	for root, folders, files in os.walk(rootFolder):
		# files = [x for x in files if not x[0] == '.']
		# folders[:] = [x for x in folders if not x[0] == '.']
		
		for folder in folders:
			folderPath = os.path.relpath(os.path.join(root, folder))
			currentSnapshot[folderPath] = ['folder']
			foldersNumber += 1
		
		for file in files:
			filePath = os.path.relpath(os.path.join(root, file))
			sizeOfCurrentFile = os.path.getsize(filePath)
			totalSize += sizeOfCurrentFile
			currentSnapshot[filePath] = ['file', sizeOfCurrentFile, math.ceil(os.path.getmtime(filePath))]
			#math.ceil for rounding float
			filesNumber += 1

	print('There are ' + str(foldersNumber) + ' folders and ' + 
		str(filesNumber) + ' files in ' + rootFolder)
	logFile.info('There are ' + str(foldersNumber) + ' folders and ' + 
		str(filesNumber) + ' files in ' + rootFolder)
	print('Total size of ' + rootFolder + ' is ' + 
		str("{0:.0f}".format(totalSize / 1024 /1024)) + ' MB.\n')
	logFile.info('Total size of ' + rootFolder + ' is ' + 
		str("{0:.0f}".format(totalSize / 1024 /1024)) + ' MB.\n')

	return currentSnapshot


def compareSnapshots(snapA, rootA, snapB, rootB):
	#check A against B

	notExistInB = []
	samePathAndName = []
	sameNameAndTimeItems = []
	toBeCopiedFromBtoA = []
	toBeCopiedFromAtoB = []
	
	pathsOfSnapB = [] 
	for key in snapB.keys():
		#create list of paths from second folder's snapshot
		path_B_File_wo_Root = re.search(r'^([^\\]*)(\\.*)', key).group(2)
		#get rid of name of root folder in the path to compare only what is inside folders: get '\somefolder\somefile.ext' instead of 'rootfolder\somefolder\somefile.ext'

		pathsOfSnapB.append(path_B_File_wo_Root)

	for key in snapA:
		path_A_File_wo_Root = re.search(r'^([^\\]*)(\\.*)', key).group(2)
		#get rid of root folder in path

		if path_A_File_wo_Root in pathsOfSnapB:
			
			if snapA[key][0] == 'file': #compare time of creation of same files
				samePathAndName.append(key)
				correspondigFileInB = rootB + path_A_File_wo_Root
				
				if snapA[key][2] == snapB[correspondigFileInB][2]:
					#if files has the same time of modification
					sameNameAndTimeItems.append(key)
					# logFile.info(key + ' and ' + correspondigFileInB + ' are the same.')
					if snapA[key][1] != snapB[correspondigFileInB][1]:
						raise RuntimeError('File ' + key + ' and file ' + correspondigFileInB + ' have same name and same modification time, but different size. It is impossible to figure out which one is newer automatically.')

				elif snapA[key][2] < snapB[correspondigFileInB][2]:
					#file in A newer than file in B -> add it to list to be copied from A to B
					
					toBeCopiedFromAtoB.append(key)
				elif snapA[key][2] > snapB[correspondigFileInB][2]:
					#file in A older than file in B -> add it to list to be copied from B to A
					toBeCopiedFromBtoA.append(key)	
		else:
			# if file doesn't exist in B -> add it in list to be copied from A
			notExistInB.append(key)

	######### result messages ########## 		

	#show files that don't exist in A but exists in B
	print('')
	print('###########################')
	print(firstFolder)
	logFile.info(firstFolder)
	print('###########################')
	
	print(str(len(samePathAndName)) + ' equal files.')
	logFile.info(str(len(samePathAndName)) +  ' equal files.')
	for path in samePathAndName:
		logFile.info(path)
	logFile.info('\n')	

	print(str(len(sameNameAndTimeItems)) + ' files don\'t need update.')
	logFile.info(str(len(sameNameAndTimeItems)) + ' files don\'t need update.')
	for path in sameNameAndTimeItems:
		logFile.info(path)
	logFile.info('\n')	

	print(str(len(notExistInB)) + ' files from  ' + firstFolder + ' don\'t exist in ' + secondFolder)
	logFile.info(str(len(notExistInB)) + ' files from  ' + firstFolder + ' don\'t exist in ' + secondFolder)
	for path in notExistInB:
		logFile.info(path)
	logFile.info('\n')	

	print(str(len(toBeCopiedFromAtoB)) + ' files need to update in ' + secondFolder)
	logFile.info(str(len(toBeCopiedFromAtoB)) + ' files need to update in ' + secondFolder)
	for path in toBeCopiedFromAtoB:
		logFile.info(path)
	logFile.info('\n')	

	print(str(len(toBeCopiedFromBtoA)) + ' files need to update in ' + firstFolder)
	logFile.info(str(len(toBeCopiedFromBtoA)) + ' files need to update in ' + firstFolder)
	for path in toBeCopiedFromBtoA:
		logFile.info(path)
	logFile.info('\n')		

# logFile = makeLogFile()

#paths hardcoded for the sake of speed of testing
# Scrip gets the name of PC in order to work on my several laptops without
# typing paths for folders to sync

def devLap():
	logConsole.debug('You are on dev laptop. Using default adressess for test.')
	logFile.debug('You are on dev laptop. Using default adressess for test.')

if platform.node() == 'ZenBook3':
	devLap()
	firstFolder = 'D:\\YandexDisk\\Studies\\Python\\folderSync\\A'
	secondFolder = 'D:\\YandexDisk\\Studies\\Python\\folderSync\\B'
elif platform.node() == 'AcerVNitro':
	devLap()
	firstFolder = 'C:\\yandex.disk\\Studies\\Python\\folderSync\\A'
	secondFolder = 'C:\\yandex.disk\\Studies\\Python\\folderSync\\B'
elif platform.node() == 'ASUSG751':
	devLap()
	firstFolder = 'C:\\YandexDisk\\Studies\\Python\\folderSync\\A'
	secondFolder = 'C:\\YandexDisk\\Studies\\Python\\folderSync\\B'
else:
	logConsole.debug('Unknown computer.')
	logFile.debug('Unknown computer.')
	firstFolder, secondFolder = menuChooseFolders()

firstFolderSynced = hasItEverBeenSynced(firstFolder)
logFile.debug(firstFolder + ' Has been synced before? ' + str(firstFolderSynced))
logConsole.debug(firstFolder + ' Has been synced before? ' + str(firstFolderSynced))

secondFolderSynced = hasItEverBeenSynced(secondFolder)
logFile.debug(secondFolder + ' Has been synced before? ' + str(secondFolderSynced))
logConsole.debug(secondFolder + ' Has been synced before? ' + str(secondFolderSynced))


snapshostFirstFolder = getSnapshot(firstFolder)
snapshostSecondFolder = getSnapshot(secondFolder)
rootFirstFolder = re.search(r'(\w+$)', firstFolder).group(0)
rootSecondFolder = re.search(r'(\w+$)', secondFolder).group(0)
compareSnapshots(snapshostFirstFolder, rootFirstFolder, snapshostSecondFolder, rootSecondFolder)



#TODO make menu to let user choose folders to sync
# until then I am gonna set it manually at code to save some time while checking



