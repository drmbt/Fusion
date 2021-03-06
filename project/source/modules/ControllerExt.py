System = iop.Modules.op('system').module.System

class ControllerExt(System):
	"""
	ControllerExt description
	"""
	def __init__(self, ownerComp):	
		System.__init__(self, ownerComp)
		self.ownerComp = ownerComp
		self.Remote = ownerComp.op('remote')
		self.sync = self.Remote.op('sync')
		self.Sync = self.sync.op('sync')
		self.Cross = ownerComp.op('cross')
		self.Sequencer = ownerComp.op('sequencer')
		self.UI = ownerComp.op('ui')
		self.UI_Playlists = self.UI.op('playlists')
		self.UI_Playlist =  self.UI.op('playlist')
		self.UI_Sequencer = self.UI.op('masterControls/sequencer')

		controlModeLookup = {'LOCAL': 0, 'LOCAL_CONTROL_EXTERNAL': 1, 
							'CONTROL_EXTERNAL': 2, 'EXTERNAL': 3, 'BACKUP_UI': 4}

		self.SetCtrlInternalExternal()

	# Cue Functions
	########################################################################
	def CueParChange(self, cue, par):
		pass

	def CueSelect(self, cue):
		if cue:	
			self.ownerComp.CurrentPlaylist.CueSelect(cue)
			if self.ownerComp.Startcueonselect and self.MasterCtrl:	
				run("args[0].GetAttr('CueStart')", self.ownerComp, delayFrames=6)
			
			elif self.ownerComp.Startcueonselect and self.NODE.Ispreviewrender:
				run("args[0].CueStart()", self.ownerComp, delayFrames=6)
				pass

	def CueStart(self):
		if self.Ismastersync:
			self.sync.par.Cuestart = True
			run("args[0].par.Cuestart = False", self.sync, delayFrames=5)

		elif self.NODE.Ismaster:
			self.ownerComp.CurrentPlaylist.CurrentCue = self.SelectedCue
			
	def CueStartSync(self):
		# called by chopexec looking at sync source
		# debug("start cue from sync")
		cue = self.ownerComp.SelectedCue
		self.ownerComp.CurrentPlaylist.CurrentCue = cue
		cue.Start()	

		if self.ownerComp.Usecuecrossdur:
			self.Cross.Crossduration = cue.Crossduration

		if self.ownerComp.NODE.Ismastersync:	
			self.Cross.CrossFade(cue)
		elif self.RemoteCtrl:
			self.Cross.CrossFadeRemote(cue)

	def CueSetLabel(self, cue, label):
		cue.Label = label

	# Playlist Functions
	########################################################################	
	def PlaylistReorder(self, cuesIndices):
		self.ownerComp.CurrentPlaylist.Reorder(cuesIndices)

	def PlaylistOnDrop(self, dropData):
		#print('Playlist On Drop:', dropData)
		dragItems = dropData['dragItems']
		row = dropData['row']
		insert = -1
		if row != -1:
			insert = row - 1

		for item in dropData['dragItems']:
			if type(item) == str:
				self.ownerComp.CurrentPlaylist.ParseDropString(item, insert)		
			elif item.isTOP:
				self.ownerComp.CurrentPlaylist.LoadOP(item, insert=insert)
			elif item.isCOMP:
				if type(item) == listCOMP:
					row = dropData['fromListerInfo'][0]
					obj = item.Data[row]['rowObject']
					item = obj[1]
				
				self.ownerComp.CurrentPlaylist.LoadCOMP(item, insert)
			if row != -1:
				insert += 1

	def CueDelete(self, cue):
		if cue and self.ownerComp.NODE.Ismaster:
			self.ownerComp.CurrentPlaylist.CueDelete(cue)

	def CueCreate(self):
		label = 'Empty Cue'
		self.ownerComp.CurrentPlaylist.CueCreate(label=label)

	# Playlists Set Functions
	########################################################################		
	def PlaylistsReorder(self, playistIndices):
		self.ownerComp.Playlists.Reorder(playistIndices)

	def PlaylistSelect(self, playlist):
		self.ownerComp.Playlists.CurrentPlaylist = playlist
		self.CueSelect(self.ownerComp.Playlists.CurrentPlaylist.SelectedCue)

	def PlaylistInitialize(self):
		self.ownerComp.CurrentPlaylist.Initialize()

	def PlaylistSetLabel(self, playlist, label):
		playlist.Label = label

	def PlaylistDelete(self, playlist):
		if playlist and self.ownerComp.NODE.Ismaster:
			self.ownerComp.Playlists.PlaylistDelete(playlist)	

	def PlaylistCreate(self):	
		self.ownerComp.Playlists.PlaylistCreate()

	def PlaylistLoad(self, path):
		self.ownerComp.Playlists.PlaylistLoad(path)

	# Sequencer 
	########################################################################
	def SequencerStart(self):
		if self.Ismastersync:
			self.Sequencer.Start()

	def SequencerPlay(self, value):
		if self.Ismastersync and not self.NODE.Ismaster:
			self.Sequencer.Play(value)
	
	def SequencerInitialize(self):
		if self.Ismastersync:
			self.Sequencer.Initialize()

	def SequencerEndAction(self, value):
		if self.Ismastersync and not self.NODE.Ismaster:
			self.Sequencer.OnDone(value)

	# Sync 
	########################################################################
	def SetSyncSelects(self):
			top1 = self.Cross.Select1.par.top.eval()
			if top1:
				comp1 = top1.parent()
			else:
				comp1 = self.ownerComp.MasterCue

			top2 = self.Cross.Select2.par.top.eval()
			if top2:
				comp2 = top2.parent()
			else:
				comp2 = self.ownerComp.MasterCue

			self.sync.SetCrossComps(comp1, comp2)

	def SetCtrlInternalExternal(self):
		self.MasterCtrl = tdu.Dependency(self.Controlmode in ['LOCAL', 
															'LOCAL_CONTROL_EXTERNAL', 
															'CONTROL_EXTERNAL'])
		self.CtrlInt = tdu.Dependency(self.Controlmode in ['LOCAL', 'LOCAL_CONTROL_EXTERNAL'])
		self.CtrlExt = tdu.Dependency(self.Controlmode in ['LOCAL_CONTROL_EXTERNAL', 
											'CONTROL_EXTERNAL', 'BACKUP_UI'])
		self.RemoteUI = tdu.Dependency(self.Controlmode in ['BACKUP_UI'])
		self.RemoteCtrl = tdu.Dependency(self.Controlmode == 'EXTERNAL')


	# System Functions
	########################################################################

	# located in inherited System module/class


	# System Wrapper Functions
	########################################################################
	def GetAttr(self, attribute, *args, **kwargs):
		if self.CtrlInt:
			getattr(self.ownerComp, attribute)(*args, **kwargs)
		if self.CtrlExt:
			self.Remote.GetAttr(self.ownerComp, attribute, *args, **kwargs)
		
	def SetAttr(self, comp, attribute, value):
		if self.CtrlInt:
			setattr(comp, attribute, value)
		if self.CtrlExt:
			self.Remote.SetAttr(comp, attribute, value)

	def SetPar(self, comp, parName, value, internal=False, external=True):
		if internal:
			setattr(comp.par, parName, value)

		if self.CtrlExt and external:
			self.Remote.SetPar(comp, parName, value)

	@property
	def Controlmode(self):
		return self.ownerComp.par.Controlmode.eval()

	@Controlmode.setter
	def Controlmode(self, value):
		self.ownerComp.par.Controlmode = value
		self.SetCtrlInternalExternal()
		self.Remote.SetMode(value)

	@property
	def Ismastersync(self):
		return self.ownerComp.par.Ismastersync.eval()

	@Ismastersync.setter
	def Ismastersync(self, value):
		self.ownerComp.par.Ismastersync = value
		self.SetCtrlInternalExternal()
		self.Remote.SetMode(self.ownerComp.par.Controlmode.eval())

	




	

