import sys
import PyTango
import threading
import time
import pycats
from pycats import CATS2TANGO, TANGO2CATS

class StatusUpdateThread(threading.Thread):
  def __init__(self, ds):
    threading.Thread.__init__(self)
    self.ds = ds
    self.should_run = True

  def stopRunning(self):
    self.should_run = False

  def run(self):
    while self.should_run:
      try:
        new_status_dict = self.ds.cs8connection.getStatusDict()
        self.ds.processStatusDict(new_status_dict)
      except Exception,e:
        self.ds.notifyNewState(PyTango.DevState.ALARM, 'Exception when getting status from the CATS system:\n%s' % str(e))
      time.sleep(self.ds.update_freq_ms / 1000.)

class CATS(PyTango.Device_4Impl):
  """ A Python Device Server to communicate with the IRELEC's CATS Sample Changer
  """
  def __init__(self, klass, name):
    PyTango.Device_4Impl.__init__(self, klass, name)
    
    self.cs8connection = pycats.CS8Connection()
    self.status_update_thread = None
    self.status_dict = {}
    self.init_device()

    # Tell Tango that the attributes have events
    for attr_name in self.get_device_class().attr_list.keys():
      self.set_change_event(attr_name, True, False)

    self.set_change_event('State', True, False)
    self.set_change_event('Status', True, False)

    print 'Ready to accept requests.'

  def init_device(self):
    self.get_device_properties(self.get_device_class())
    try:
      self.cs8connection.connect(self.host, self.port_operate, self.port_monitor)
      self.status_update_thread = StatusUpdateThread(self)
      self.status_update_thread.start()
      self.notifyNewState(PyTango.DevState.ON, 'Connected to the CATS system.')
    except Exception,e:
      self.notifyNewState(PyTango.DevState.ALARM, 'Exception connecting to the CATS system:\n'+str(e))
  
  def delete_device(self):
    if self.status_update_thread is not None:
       self.status_update_thread.stopRunning()
    self.status_dict = {}
    self.cs8connection.disconnect()

  def notifyNewState(self, state, status=None):
    self.set_state(state)
    if status is None:
      status = 'Device is in %s state.' % state
    self.set_status(status)
    self.push_change_event('State', state)
    self.push_change_event('Status', status)

  def processStatusDict(self, new_status_dict):
    path_changed = False
    for catsk, new_value in new_status_dict.iteritems():
      new_value = new_status_dict[catsk]
      if new_status_dict[catsk] != self.status_dict.get(catsk, None):
        self.status_dict[catsk] = new_value
        # Notify any tango client that the value has changed
        attr_name = CATS2TANGO[catsk]
        self.push_change_event(attr_name, new_value)
        if attr_name == 'Path':
          path_changed = True
    
    new_status = 'Powered(%s)'                % self.status_dict[TANGO2CATS['Powered']]            
    new_status += ' Tool(%s)'                 % self.status_dict[TANGO2CATS['Tool']]                 
    new_status += ' Path(%s)'                 % self.status_dict[TANGO2CATS['Path']]                 
    new_status += ' PathRunning(%s)'          % self.status_dict[TANGO2CATS['PathRunning']]          
    new_status += '\nLidSampleOnTool(%s)'     % self.status_dict[TANGO2CATS['LidSampleOnTool']]      
    new_status += ' NumSampleOnTool(%s)'      % self.status_dict[TANGO2CATS['NumSampleOnTool']]      
    new_status += ' Barcode(%s)'              % self.status_dict[TANGO2CATS['Barcode']]              
    new_status += '\nLidSampleOnDiff(%s)'     % self.status_dict[TANGO2CATS['LidSampleOnDiff']]      
    new_status += ' NumSampleOnDiff(%s)'      % self.status_dict[TANGO2CATS['NumSampleOnDiff']]      
    new_status += '\nNumPlateOnTool(%s)'      % self.status_dict[TANGO2CATS['NumPlateOnTool']]       
    new_status += ' Well(%s)'                 % self.status_dict[TANGO2CATS['Well']]                 
    new_status += '\nLN2Regulating(%s)'       % self.status_dict[TANGO2CATS['LN2Regulating']]        
    new_status += ' LN2Warming(%s)'           % self.status_dict[TANGO2CATS['LN2Warming']]           
    new_status += '\nAutoMode(%s)'            % self.status_dict[TANGO2CATS['AutoMode']]             
    new_status += ' DefaultStatus(%s)'        % self.status_dict[TANGO2CATS['DefaultStatus']]        
    new_status += ' SpeedRatio(%s)'           % self.status_dict[TANGO2CATS['SpeedRatio']]
    new_status += '\nPuckDetectionDewar1(%s)'  % self.status_dict[TANGO2CATS['PuckDetectionDewar1']]
    new_status += ' PuckDetectionDewar2(%s)'  % self.status_dict[TANGO2CATS['PuckDetectionDewar2']]
    new_status += ' PositionNumberDewar1(%s)' % self.status_dict[TANGO2CATS['PositionNumberDewar1']]
    new_status += ' PositionNumberDewar2(%s)' % self.status_dict[TANGO2CATS['PositionNumberDewar2']]

    
    if new_status_dict[TANGO2CATS['Path']] != '':
      self.notifyNewState(PyTango.DevState.RUNNING, new_status)
    else:
      self.notifyNewState(PyTango.DevState.ON, new_status)

  #################################################################
  ######################## READ ATTRIBUTES ########################
  #################################################################

  # STATE PARAMS pycats.state_params
  def read_Powered(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Powered']])
  def read_AutoMode(self, attr): attr.set_value(self.status_dict[TANGO2CATS['AutoMode']])
  def read_DefaultStatus(self, attr): attr.set_value(self.status_dict[TANGO2CATS['DefaultStatus']])
  def read_Tool(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Tool']])
  def read_Path(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Path']])
  def read_LidSampleOnTool(self, attr): attr.set_value(self.status_dict[TANGO2CATS['LidSampleOnTool']])
  def read_NumSampleOnTool(self, attr): attr.set_value(self.status_dict[TANGO2CATS['NumSampleOnTool']])
  def read_LidSampleOnDiff(self, attr): attr.set_value(self.status_dict[TANGO2CATS['LidSampleOnDiff']])
  def read_NumSampleOnDiff(self, attr): attr.set_value(self.status_dict[TANGO2CATS['NumSampleOnDiff']])
  def read_NumPlateOnTool(self, attr): attr.set_value(self.status_dict[TANGO2CATS['NumPlateOnTool']])
  def read_Well(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Well']])
  def read_Barcode(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Barcode']])
  def read_PathRunning(self, attr): attr.set_value(self.status_dict[TANGO2CATS['PathRunning']])
  def read_LN2Regulating(self, attr): attr.set_value(self.status_dict[TANGO2CATS['LN2Regulating']])
  def read_LN2Warming(self, attr): attr.set_value(self.status_dict[TANGO2CATS['LN2Warming']])
  def read_SpeedRatio(self, attr): attr.set_value(self.status_dict[TANGO2CATS['SpeedRatio']])
  def read_PuckDetectionDewar1(self, attr): attr.set_value(self.status_dict[TANGO2CATS['PuckDetectionDewar1']])
  def read_PuckDetectionDewar2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['PuckDetectionDewar2']])
  def read_PositionNumberDewar1(self, attr): attr.set_value(self.status_dict[TANGO2CATS['PositionNumberDewar1']])
  def read_PositionNumberDewar2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['PositionNumberDewar2']])

  # DI PARAMS pycats.di_params
  def read_di_CryoOK(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CryoOK']])
  def read_di_EStopAirpresOK(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_EStopAirpresOK']])
  def read_di_CollisonSensorOK(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CollisonSensorOK']])
  def read_di_CryoHighLevelAlarm(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CryoHighLevelAlarm']])
  def read_di_CryoHighLevel(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CryoHighLevel']])
  def read_di_CryoHighLevel(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CryoHighLevel']])
  def read_di_CryoLowLevelAlarm(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CryoLowLevelAlarm']])
  def read_di_CryoLiquidDetection(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_CryoLiquidDetection']])
  def read_di_PRI1_GFM(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI1_GFM']])
  def read_di_PRI2_API(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI2_API']])
  def read_di_PRI3_APL(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI3_APL']])
  def read_di_PRI4_SOM(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI4_SOM']])
  def read_di_Cassette1Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette1Presence']])
  def read_di_Cassette2Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette2Presence']])
  def read_di_Cassette3Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette3Presence']])
  def read_di_Cassette4Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette4Presence']])
  def read_di_Cassette5Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette5Presence']])
  def read_di_Cassette6Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette6Presence']])
  def read_di_Cassette7Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette7Presence']])
  def read_di_Cassette8Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette8Presence']])
  def read_di_Cassette9Presence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Cassette9Presence']])
  def read_di_Lid1Open(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Lid1Open']])
  def read_di_Lid2Open(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Lid2Open']])
  def read_di_Lid3Open(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_Lid3Open']])
  def read_di_ToolOpen(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_ToolOpen']])
  def read_di_ToolClosed(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_ToolClosed']])
  def read_di_LimSW1RotGripAxis(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_LimSW1RotGripAxis']])
  def read_di_LimSW2RotGripAxis(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_LimSW2RotGripAxis']])
  def read_di_ModbusPLCLifeBit(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_ModbusPLCLifeBit']])
  def read_di_LifeBitFromPLC(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_LifeBitFromPLC']])
  def read_di_ActiveLidOpened(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_ActiveLidOpened']])
  def read_di_NewActiveLidOpened(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_NewActiveLidOpened']])
  def read_di_ToolChangerOpened(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_ToolChangerOpened']])
  def read_di_ActiveCassettePresence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_ActiveCassettePresence']])
  def read_di_NewActiveCassettePresence(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_NewActiveCassettePresence']])
  def read_di_AllLidsClosed(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_AllLidsClosed']])
  def read_di_PRI5(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI5']])
  def read_di_PRI6(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI6']])
  def read_di_PRI7(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI7']])
  def read_di_PRI8(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI8']])
  def read_di_PRI9(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI9']])
  def read_di_PRI10(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI10']])
  def read_di_PRI11(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI11']])
  def read_di_PRI12(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_PRI12']])
  def read_di_VI90(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI90']])
  def read_di_VI91(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI91']])
  def read_di_VI92(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI92']])
  def read_di_VI93(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI93']])
  def read_di_VI94(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI94']])
  def read_di_VI95(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI95']])
  def read_di_VI96(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI96']])
  def read_di_VI97(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI97']])
  def read_di_VI98(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI98']])
  def read_di_VI99(self, attr): attr.set_value(self.status_dict[TANGO2CATS['di_VI99']])
  
  # DO PARAMS pycats.do_params
  def read_do_ToolChanger(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_ToolChanger']])
  def read_do_ToolOpenClose(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_ToolOpenClose']])
  def read_do_FastOutput(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_FastOutput']])
  def read_do_PRO1_MON(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO1_MON']])
  def read_do_PRO2_COL(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO2_COL']])
  def read_do_PRO3_LNW(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO3_LNW']])
  def read_do_PRO4_LNA(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO4_LNA']])
  def read_do_GreenLight(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_GreenLight']])
  def read_do_PilzRelayReset(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PilzRelayReset']])
  def read_do_ServoCardOn(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_ServoCardOn']])
  def read_do_ServoCardRotation(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_ServoCardRotation']])
  def read_do_CryoValveLN2C(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CryoValveLN2C']])
  def read_do_CryoValveLN2E(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CryoValveLN2E']])
  def read_do_CryoValveGN2E(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CryoValveGN2E']])
  def read_do_HeaterOnOff(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_HeaterOnOff']])
  def read_do_OpenCloseLid11(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid11']])
  def read_do_OpenCloseLid12(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid12']])
  def read_do_OpenCloseLid21(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid21']])
  def read_do_OpenCloseLid22(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid22']])
  def read_do_OpenCloseLid31(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid31']])
  def read_do_OpenCloseLid32(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid32']])
  def read_do_RequestDew1PosBit1(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew1PosBit1']])
  def read_do_RequestDew1PosBit2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew1PosBit2']])
  def read_do_RequestDew1PosBit3(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew1PosBit3']])
  def read_do_RequestDew1PosBit4(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew1PosBit4']])
  def read_do_OpenLid(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenLid']])
  def read_do_CloseLid(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CloseLid']])
  def read_do_OpenNewLid(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenNewLid']])
  def read_do_CloseNewLid(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CloseNewLid']])
  def read_do_BarcodeReader(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_BarcodeReader']])
  def read_do_CloseAllLids(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CloseAllLids']])
  def read_do_PRO5_IDL(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO5_IDL']])
  def read_do_PRO6_RAH(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO6_RAH']])
  def read_do_PRO7_RI1(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO7_RI1']])
  def read_do_PRO8_RI2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO8_RI2']])
  def read_do_PRO9_LIO(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO9_LIO']])
  def read_do_PRO10(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO10']])
  def read_do_PRO11(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO11']])
  def read_do_PRO12(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO12']])
  def read_do_RequestDew2PosBit1(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew2PosBit1']])
  def read_do_RequestDew2PosBit2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew2PosBit2']])
  def read_do_RequestDew2PosBit3(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew2PosBit3']])
  def read_do_RequestDew2PosBit4(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RequestDew2PosBit4']])
  def read_do_CryoValveLN2CDew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CryoValveLN2CDew2']])
  def read_do_CryoValveLN2EDew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CryoValveLN2EDew2']])
  def read_do_CryoVavleGN2EDew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_CryoVavleGN2EDew2']])
  def read_do_OpenCloseLid31Dew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid31Dew2']])
  def read_do_OpenCloseLid32Dew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid32Dew2']])
  def read_do_OpenCloseLid41Dew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid41Dew2']])
  def read_do_OpenCloseLid42Dew2(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_OpenCloseLid42Dew2']])
  def read_do_PRO13(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO13']])
  def read_do_PRO14(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO14']])
  def read_do_PRO15(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO15']])
  def read_do_PRO16(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_PRO16']])
  def read_do_RotationDewNewPosWorking(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RotationDewNewPosWorking']])
  def read_do_RotationDewarPosCassLoading(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RotationDewarPosCassLoading']])
  def read_do_RotationDewPosWorking(self, attr): attr.set_value(self.status_dict[TANGO2CATS['do_RotationDewPosWorking']])

  # POSITION PARAMS pycats.position_params
  def read_Xpos(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Xpos']])
  def read_Ypos(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Ypos']])
  def read_Zpos(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Zpos']])
  def read_RXpos(self, attr): attr.set_value(self.status_dict[TANGO2CATS['RXpos']])
  def read_RYpos(self, attr): attr.set_value(self.status_dict[TANGO2CATS['RYpos']])
  def read_RZpos(self, attr): attr.set_value(self.status_dict[TANGO2CATS['RZpos']])

  # MESSAGE
  def read_Message(self, attr): attr.set_value(self.status_dict[TANGO2CATS['Message']])


  #################################################################
  ######################## EXECUTE COMMANDS #######################
  #################################################################

  # 3.6.5.1 General commands
  def powerOn(self): return self.cs8connection.powerOn()
  def powerOff(self): return self.cs8connection.powerOff()
  def panic(self): return self.cs8connection.panic()
  def abort(self): return self.cs8connection.abort()
  def pause(self): return self.cs8connection.pause()
  def reset(self): return self.cs8connection.reset()
  def restart(self): return self.cs8connection.restart()
  def backup(self, usbport): return self.cs8connection.backup(usbport)
  def restore(self, usbport): return self.cs8connection.restore(usbport)

  # 3.6.5.2 Trajectories commands
  def home(self, argin):
    tool = argin
    return self.cs8connection.home(tool)
  def safe(self, argin):
    tool = argin
    return self.cs8connection.safe(tool)
  def put(self, argin):
    tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.put(tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift)
  def put_HT(self, argin):
    tool, sample, type, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.put_HT(tool, sample, type, toolcal, x_shift, y_shift, z_shift)
  def put_bcrd(self, argin):
    tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.put_bcrd(tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift)
  def get(self, argin):
    tool, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.get(tool, toolcal, x_shift, y_shift, z_shift)
  def get_HT(self, argin):
    tool, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.get_HT(tool, toolcal, x_shift, y_shift, z_shift)
  def getput(self, argin):
    tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.getput(tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift)
  def getput_HT(self, argin):
    tool, sample, type, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.getput_HT(tool, sample, type, toolcal, x_shift, y_shift, z_shift)
  def getput_bcrd(self, argin):
    tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
    return self.cs8connection.getput_bcrd(tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift)
  def barcode(self, argin):
    tool, newlid, newsample, type, toolcal = argin
    return self.cs8connection.barcode(tool, newlid, newsample, type, toolcal)
  def back(self, argin):
    tool, toolcal = argin
    return self.cs8connection.back(tool, toolcal)
  def transfer(self, argin):
    tool, lid, sample, newlid, newsample, type, toolcal = argin
    return self.cs8connection.transfer(tool, lid, sample, newlid, newsample, type, toolcal)
  def soak(self, argin):
    tool, lid = argin
    return self.cs8connection.soak(tool, lid)
  def dry(self, argin):
    tool = argin
    return self.cs8connection.dry(tool)
  def gotodif(self, argin):
    tool, lid, sample, type, toolcal = argin
    return self.cs8connection.gotodif(tool, lid, sample, type, toolcal)
  def rd_position(self, argin):
    tool, lid = argin
    return self.cs8connection.rd_position(tool, lid)
  def rd_load(self, argin):
    tool, newlid = argin
    return self.cs8connection.rd_load(tool, newlid)
  def puckdetect(self, argin):
    lid, toolcal = argin
    return self.cs8connection.puckdetect(lid, toolcal)

  # 3.6.5.3 Crystallization plate commands
  def putplate(self, argin):
    tool, plate, well, type, toolcal = argin
    return self.cs8connection.putplate(tool, plate, well, type, toolcal)
  def getplate(self, argin):
    tool, drop, toolcal = argin
    return self.cs8connection.getplate(tool, drop, toolcal)
  def getputplate(self, argin):
    tool, plate, well, type, drop, toolcal = argin
    return self.cs8connection.getputplate(tool, plate, well, type, drop, toolcal)
  def goto_well(self, argin):
    tool, plate, well, toolcal = argin
    return self.cs8connection.goto_well(tool, plate, well, toolcal)
  def adjust(self, argin):
    tool, toolcal, x_shift, y_shift = argin
    return self.cs8connection.adjust(tool, toolcal, x_shift, y_shift)
  def focus(self, argin):
    tool, toolcal, z_shift = argin
    return self.cs8connection.focus(tool, toolcal, z_shift)
  def expose(self, argin):
    tool, toolcal, angle, oscillations, exp_time, step = argin
    return self.cs8connection.expose(tool, toolcal, angle, oscillations, exp_time, step)
  def collect(self, argin):
    tool, toolcal, angle, oscillations, exp_time, step, final_angle = argin
    return self.cs8connection.collect(tool, toolcal, angle, oscillations, exp_time, step, final_angle)
  def setplateangle(self, argin):
    tool, toolcal, angle = argin
    return self.cs8connection.setplateangle(tool, toolcal, angle)

  # 3.6.5.4 Virtual Inputs
  def vdi9xon(self, input): return self.cs8connection.vdi9xon(input)
  def vdi9xoff(self, input): return self.cs8connection.vdi9xoff(input)

  # 3.6.5.5 Commands for LN2 controller
  def regulon(self): return self.cs8connection.regulon()
  def reguloff(self): return self.cs8connection.reguloff()
  def warmon(self): return self.cs8connection.warmon()
  def warmoff(self): return self.cs8connection.warmoff()
  def regulon1(self): return self.cs8connection.regulon1()
  def reguloff1(self): return self.cs8connection.reguloff1()
  def regulon2(self): return self.cs8connection.regulon2()
  def reguloff2(self): return self.cs8connection.reguloff2()
  
  # 3.6.5.6 Maintenance commands
  def openlid1(self): return self.cs8connection.openlid1()
  def closelid1(self): return self.cs8connection.closelid1()
  def openlid2(self): return self.cs8connection.openlid2()
  def closelid2(self): return self.cs8connection.closelid2()
  def openlid3(self): return self.cs8connection.openlid3()
  def closelid3(self): return self.cs8connection.closelid3()
  def openlid4(self): return self.cs8connection.openlid4()
  def closelid4(self): return self.cs8connection.closelid4()
  def opentool(self): return self.cs8connection.opentool()
  def closetool(self): return self.cs8connection.closetool()
  def magneton(self): return self.cs8connection.magneton()
  def magnetoff(self): return self.cs8connection.magnetoff()
  def heateron(self): return self.cs8connection.heateron()
  def heateroff(self): return self.cs8connection.heateroff()
  def initdew1(self): return self.cs8connection.initdew1()
  def initdew2(self): return self.cs8connection.initdew2()
  def onestaticdw(self): return self.cs8connection.onestaticdw()
  def tworotatingdw(self): return self.cs8connection.tworotatingdw()

  # NOT DOCUMENTED THREE NEW COMMANDS...
  def clear_memory(self): return self.cs8connection.clear_memory()
  def reset_parameters(self): return self.cs8connection.reset_parameters()
  def resetmotion(self): return self.cs8connection.resetMotion()

  # 3.6.5.7 Status commands
  def mon_state(self): return self.cs8connection.state()
  def mon_di(self): return self.cs8connection.di()
  def mon_do(self): return self.cs8connection.do()
  def mon_position(self): return self.cs8connection.position()
  def mon_message(self): return self.cs8connection.message()
  def mon_config(self): return self.cs8connection.config()

  # BACKDOOR FOR SOFTWARE UPGRADES OR ANYTHING NEEDED... ;-D
  def send_op_cmd(self, cmd): return self.cs8connection.operate(cmd)
  def send_mon_cmd(self, cmd): return self.cs8connection.monitor(cmd)

class CATSClass(PyTango.DeviceClass):
  device_property_list = {
    'host': [PyTango.DevString,
             "Hostname of the CATS system.",
             []],
    'port_operate': [PyTango.DevUShort,
                     "Socket's port to operatethe CATS system.",
                     []],
    'port_monitor': [PyTango.DevUShort,
                     "Socket's port to monitor the CATS system.",
                     []],
    'update_freq_ms': [PyTango.DevUShort,
                       "Time in ms to update the status of the CATS system.",
                       []]
    }

  attr_list = {
    # STATE PARAMS pycats.state_params
    'Powered':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ]],
    'AutoMode':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ]],
    'DefaultStatus':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ]],
    'Tool':[[PyTango.DevString, PyTango.SCALAR, PyTango.READ]],
    'Path':[[PyTango.DevString, PyTango.SCALAR, PyTango.READ]],
    'LidSampleOnTool':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'NumSampleOnTool':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'LidSampleOnDiff':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'NumSampleOnDiff':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'NumPlateOnTool':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'Well':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'Barcode':[[PyTango.DevString, PyTango.SCALAR, PyTango.READ]],
    'PathRunning':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ]],
    'LN2Regulating':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ]],
    'LN2Warming':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ]],
    'SpeedRatio':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],
    'PuckDetectionDewar1':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'PuckDetectionDewar2':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'PositionNumberDewar1':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],
    'PositionNumberDewar2':[[PyTango.DevShort, PyTango.SCALAR, PyTango.READ]],

    # DI PARAMS pycats.di_params
    'di_CryoOK':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                 {'description':'False:'+pycats.di_help[TANGO2CATS['di_CryoOK']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CryoOK']][1]}],
    'di_EStopAirpresOK':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.di_help[TANGO2CATS['di_EStopAirpresOK']][0]+' True:'+pycats.di_help[TANGO2CATS['di_EStopAirpresOK']][1]}],
    'di_CollisonSensorOK':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                           {'description':'False:'+pycats.di_help[TANGO2CATS['di_CollisonSensorOK']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CollisonSensorOK']][1]}],
    'di_CryoHighLevelAlarm':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.di_help[TANGO2CATS['di_CryoHighLevelAlarm']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CryoHighLevelAlarm']][1]}],
    'di_CryoHighLevel':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.di_help[TANGO2CATS['di_CryoHighLevel']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CryoHighLevel']][1]}],
    'di_CryoHighLevel':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.di_help[TANGO2CATS['di_CryoHighLevel']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CryoHighLevel']][1]}],
    'di_CryoLowLevelAlarm':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_CryoLowLevelAlarm']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CryoLowLevelAlarm']][1]}],
    'di_CryoLiquidDetection':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                              {'description':'False:'+pycats.di_help[TANGO2CATS['di_CryoLiquidDetection']][0]+' True:'+pycats.di_help[TANGO2CATS['di_CryoLiquidDetection']][1]}],
    'di_PRI1_GFM':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI1_GFM']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI1_GFM']][1]}],
    'di_PRI2_API':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI2_API']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI2_API']][1]}],
    'di_PRI3_APL':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI3_APL']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI3_APL']][1]}],
    'di_PRI4_SOM':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI4_SOM']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI4_SOM']][1]}],
    'di_Cassette1Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette1Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette1Presence']][1]}],
    'di_Cassette2Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette2Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette2Presence']][1]}],
    'di_Cassette3Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette3Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette3Presence']][1]}],
    'di_Cassette4Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette4Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette4Presence']][1]}],
    'di_Cassette5Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette5Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette5Presence']][1]}],
    'di_Cassette6Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette6Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette6Presence']][1]}],
    'di_Cassette7Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette7Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette7Presence']][1]}],
    'di_Cassette8Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette8Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette8Presence']][1]}],
    'di_Cassette9Presence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_Cassette9Presence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Cassette9Presence']][1]}],
    'di_Lid1Open':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_Lid1Open']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Lid1Open']][1]}],
    'di_Lid2Open':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_Lid2Open']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Lid2Open']][1]}],
    'di_Lid3Open':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_Lid3Open']][0]+' True:'+pycats.di_help[TANGO2CATS['di_Lid3Open']][1]}],
    'di_ToolOpen':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.di_help[TANGO2CATS['di_ToolOpen']][0]+' True:'+pycats.di_help[TANGO2CATS['di_ToolOpen']][1]}],
    'di_ToolClosed':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                     {'description':'False:'+pycats.di_help[TANGO2CATS['di_ToolClosed']][0]+' True:'+pycats.di_help[TANGO2CATS['di_ToolClosed']][1]}],
    'di_LimSW1RotGripAxis':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_LimSW1RotGripAxis']][0]+' True:'+pycats.di_help[TANGO2CATS['di_LimSW1RotGripAxis']][1]}],
    'di_LimSW2RotGripAxis':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_LimSW2RotGripAxis']][0]+' True:'+pycats.di_help[TANGO2CATS['di_LimSW2RotGripAxis']][1]}],
    'di_ModbusPLCLifeBit':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                           {'description':'False:'+pycats.di_help[TANGO2CATS['di_ModbusPLCLifeBit']][0]+' True:'+pycats.di_help[TANGO2CATS['di_ModbusPLCLifeBit']][1]}],
    'di_LifeBitFromPLC':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.di_help[TANGO2CATS['di_LifeBitFromPLC']][0]+' True:'+pycats.di_help[TANGO2CATS['di_LifeBitFromPLC']][1]}],
    'di_ActiveLidOpened':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                          {'description':'False:'+pycats.di_help[TANGO2CATS['di_ActiveLidOpened']][0]+' True:'+pycats.di_help[TANGO2CATS['di_ActiveLidOpened']][1]}],
    'di_NewActiveLidOpened':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.di_help[TANGO2CATS['di_NewActiveLidOpened']][0]+' True:'+pycats.di_help[TANGO2CATS['di_NewActiveLidOpened']][1]}],
    'di_ToolChangerOpened':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.di_help[TANGO2CATS['di_ToolChangerOpened']][0]+' True:'+pycats.di_help[TANGO2CATS['di_ToolChangerOpened']][1]}],
    'di_ActiveCassettePresence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                                 {'description':'False:'+pycats.di_help[TANGO2CATS['di_ActiveCassettePresence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_ActiveCassettePresence']][1]}],
    'di_NewActiveCassettePresence':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                                    {'description':'False:'+pycats.di_help[TANGO2CATS['di_NewActiveCassettePresence']][0]+' True:'+pycats.di_help[TANGO2CATS['di_NewActiveCassettePresence']][1]}],
    'di_AllLidsClosed':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.di_help[TANGO2CATS['di_AllLidsClosed']][0]+' True:'+pycats.di_help[TANGO2CATS['di_AllLidsClosed']][1]}],
    'di_PRI5':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI5']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI5']][1]}],
    'di_PRI6':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI6']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI6']][1]}],
    'di_PRI7':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI7']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI7']][1]}],
    'di_PRI8':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI8']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI8']][1]}],
    'di_PRI9':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI9']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI9']][1]}],
    'di_PRI10':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI10']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI10']][1]}],
    'di_PRI11':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI11']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI11']][1]}],
    'di_PRI12':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.di_help[TANGO2CATS['di_PRI12']][0]+' True:'+pycats.di_help[TANGO2CATS['di_PRI12']][1]}],
    'di_VI90':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI90']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI90']][1]}],
    'di_VI91':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI91']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI91']][1]}],
    'di_VI92':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI92']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI92']][1]}],
    'di_VI93':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI93']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI93']][1]}],
    'di_VI94':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI94']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI94']][1]}],
    'di_VI95':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI95']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI95']][1]}],
    'di_VI96':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI96']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI96']][1]}],
    'di_VI97':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI97']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI97']][1]}],
    'di_VI98':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI98']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI98']][1]}],
    'di_VI99':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
               {'description':'False:'+pycats.di_help[TANGO2CATS['di_VI99']][0]+' True:'+pycats.di_help[TANGO2CATS['di_VI99']][1]}],
    
    # DO PARAMS pycats.do_params
    'do_ToolChanger':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                      {'description':'False:'+pycats.do_help[TANGO2CATS['do_ToolChanger']][0]+' True:'+pycats.do_help[TANGO2CATS['do_ToolChanger']][1]}],
    'do_ToolOpenClose':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.do_help[TANGO2CATS['do_ToolOpenClose']][0]+' True:'+pycats.do_help[TANGO2CATS['do_ToolOpenClose']][1]}],
    'do_FastOutput':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                     {'description':'False:'+pycats.do_help[TANGO2CATS['do_FastOutput']][0]+' True:'+pycats.do_help[TANGO2CATS['do_FastOutput']][1]}],
    'do_PRO1_MON':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO1_MON']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO1_MON']][1]}],
    'do_PRO2_COL':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO2_COL']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO2_COL']][1]}],
    'do_PRO3_LNW':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO3_LNW']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO3_LNW']][1]}],
    'do_PRO4_LNA':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO4_LNA']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO4_LNA']][1]}],
    'do_GreenLight':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                     {'description':'False:'+pycats.do_help[TANGO2CATS['do_GreenLight']][0]+' True:'+pycats.do_help[TANGO2CATS['do_GreenLight']][1]}],
    'do_PilzRelayReset':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_PilzRelayReset']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PilzRelayReset']][1]}],
    'do_ServoCardOn':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                      {'description':'False:'+pycats.do_help[TANGO2CATS['do_ServoCardOn']][0]+' True:'+pycats.do_help[TANGO2CATS['do_ServoCardOn']][1]}],
    'do_ServoCardRotation':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.do_help[TANGO2CATS['do_ServoCardRotation']][0]+' True:'+pycats.do_help[TANGO2CATS['do_ServoCardRotation']][1]}],
    'do_CryoValveLN2C':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2C']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2C']][1]}],
    'do_CryoValveLN2E':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2E']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2E']][1]}],
    'do_CryoValveGN2E':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.do_help[TANGO2CATS['do_CryoValveGN2E']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CryoValveGN2E']][1]}],
    'do_HeaterOnOff':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                      {'description':'False:'+pycats.do_help[TANGO2CATS['do_HeaterOnOff']][0]+' True:'+pycats.do_help[TANGO2CATS['do_HeaterOnOff']][1]}],
    'do_OpenCloseLid11':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid11']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid11']][1]}],
    'do_OpenCloseLid12':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid12']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid12']][1]}],
    'do_OpenCloseLid21':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid21']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid21']][1]}],
    'do_OpenCloseLid22':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid22']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid22']][1]}],
    'do_OpenCloseLid31':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid31']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid31']][1]}],
    'do_OpenCloseLid32':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                         {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid32']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid32']][1]}],
    'do_RequestDew1PosBit1':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit1']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit1']][1]}],
    'do_RequestDew1PosBit2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit2']][1]}],
    'do_RequestDew1PosBit3':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit3']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit3']][1]}],
    'do_RequestDew1PosBit4':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit4']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew1PosBit4']][1]}],
    'do_OpenLid':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                  {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenLid']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenLid']][1]}],
    'do_CloseLid':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_CloseLid']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CloseLid']][1]}],
    'do_OpenNewLid':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                     {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenNewLid']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenNewLid']][1]}],
    'do_CloseNewLid':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                      {'description':'False:'+pycats.do_help[TANGO2CATS['do_CloseNewLid']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CloseNewLid']][1]}],
    'do_BarcodeReader':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                        {'description':'False:'+pycats.do_help[TANGO2CATS['do_BarcodeReader']][0]+' True:'+pycats.do_help[TANGO2CATS['do_BarcodeReader']][1]}],
    'do_CloseAllLids':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                       {'description':'False:'+pycats.do_help[TANGO2CATS['do_CloseAllLids']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CloseAllLids']][1]}],
    'do_PRO5_IDL':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO5_IDL']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO5_IDL']][1]}],
    'do_PRO6_RAH':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO6_RAH']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO6_RAH']][1]}],
    'do_PRO7_RI1':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO7_RI1']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO7_RI1']][1]}],
    'do_PRO8_RI2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO8_RI2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO8_RI2']][1]}],
    'do_PRO9_LIO':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO9_LIO']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO9_LIO']][1]}],
    'do_PRO10':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO10']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO10']][1]}],
    'do_PRO11':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO11']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO11']][1]}],
    'do_PRO12':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO11']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO12']][1]}],
    'do_RequestDew2PosBit1':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit1']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit1']][1]}],
    'do_RequestDew2PosBit2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit2']][1]}],
    'do_RequestDew2PosBit3':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit3']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit3']][1]}],
    'do_RequestDew2PosBit4':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit4']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RequestDew2PosBit4']][1]}],
    'do_CryoValveLN2CDew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2CDew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2CDew2']][1]}],
    'do_CryoValveLN2EDew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2EDew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CryoValveLN2EDew2']][1]}],
    'do_CryoVavleGN2EDew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                            {'description':'False:'+pycats.do_help[TANGO2CATS['do_CryoVavleGN2EDew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_CryoVavleGN2EDew2']][1]}],
    'do_OpenCloseLid31Dew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid31Dew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid31Dew2']][1]}],
    'do_OpenCloseLid32Dew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid32Dew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid32Dew2']][1]}],
    'do_OpenCloseLid41Dew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid41Dew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid41Dew2']][1]}],
    'do_OpenCloseLid42Dew2':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                             {'description':'False:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid42Dew2']][0]+' True:'+pycats.do_help[TANGO2CATS['do_OpenCloseLid42Dew2']][1]}],
    'do_PRO13':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO13']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO13']][1]}],
    'do_PRO14':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO14']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO14']][1]}],
    'do_PRO15':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO15']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO15']][1]}],
    'do_PRO16':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                {'description':'False:'+pycats.do_help[TANGO2CATS['do_PRO16']][0]+' True:'+pycats.do_help[TANGO2CATS['do_PRO16']][1]}],
    'do_RotationDewNewPosWorking':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                                   {'description':'False:'+pycats.do_help[TANGO2CATS['do_RotationDewNewPosWorking']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RotationDewNewPosWorking']][1]}],
    'do_RotationDewarPosCassLoading':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                                      {'description':'False:'+pycats.do_help[TANGO2CATS['do_RotationDewarPosCassLoading']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RotationDewarPosCassLoading']][1]}],
    'do_RotationDewPosWorking':[[PyTango.DevBoolean, PyTango.SCALAR, PyTango.READ],
                                {'description':'False:'+pycats.do_help[TANGO2CATS['do_RotationDewPosWorking']][0]+' True:'+pycats.do_help[TANGO2CATS['do_RotationDewPosWorking']][1]}],

    # POSITION PARAMS pycats.position_params
    'Xpos':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],
    'Ypos':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],
    'Zpos':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],
    'RXpos':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],
    'RYpos':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],
    'RZpos':[[PyTango.DevFloat, PyTango.SCALAR, PyTango.READ]],

    # MESSAGE
    'Message':[[PyTango.DevString, PyTango.SCALAR, PyTango.READ]]
    }

  cmd_list = {
    # 3.6.5.1 General commands
    'powerOn': [[PyTango.DevVoid],[PyTango.DevString],],
    'powerOff': [[PyTango.DevVoid],[PyTango.DevString],],
    'panic': [[PyTango.DevVoid],[PyTango.DevString],],
    'abort': [[PyTango.DevVoid],[PyTango.DevString],],
    'pause': [[PyTango.DevVoid],[PyTango.DevString],],
    'reset': [[PyTango.DevVoid],[PyTango.DevString],],
    'restart': [[PyTango.DevVoid],[PyTango.DevString],],
    'backup': [[PyTango.DevShort, 'usbport = 100:USB0/J202 101:USB1/J209'], [PyTango.DevString],],
    'restore': [[PyTango.DevShort, 'usbport = 100:USB0/J202 101:USB1/J209'], [PyTango.DevString],],

    # 3.6.5.2 Trajectories commands
    'home': [[PyTango.DevUShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection'], [PyTango.DevString],],
    'safe': [[PyTango.DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection'], [PyTango.DevString],],
    'put': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [PyTango.DevString],],
    'put_HT': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)\n3:toolcal=0\n4:X_CATS shift (um)\n5:Y_CATS shift (um)\n6:Z_CATS shift (um)'], [PyTango.DevString],],
    'put_bcrd': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [PyTango.DevString],],
    'get': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:X_CATS shift (um)\n3:Y_CATS shift (um)\n4:Z_CATS shift (um)'], [PyTango.DevString],],
    'get_HT': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:X_CATS shift (um)\n3:Y_CATS shift (um)\n4:Z_CATS shift (um)'], [PyTango.DevString],],
    'getput': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [PyTango.DevString],],
    'getput_HT': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)\n3:toolcal=0\n4:X_CATS shift (um)\n5:Y_CATS shift (um)\n6:Z_CATS shift (um)'], [PyTango.DevString],],
    'getput_bcrd': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [PyTango.DevString],],
    'barcode': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:new lid number\n2:new sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0'], [PyTango.DevString],],
    'back': [[PyTango.DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0'], [PyTango.DevString],],
    'transfer': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number\n2:sample number\n3:new lid number\n4:new sample number\n5:type = 0:Actor 1:UniPuck (only cryotong)\n6:toolcal=0'], [PyTango.DevString],],
    'soak': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number'], [PyTango.DevString],],
    'dry': [[PyTango.DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection'], [PyTango.DevString],],
    'gotodif': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0'], [PyTango.DevString],],
    'rd_position': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:lid number'], [PyTango.DevString],],
    'rd_load': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:new lid number'], [PyTango.DevString],],
    'puckdetect': [[PyTango.DevVarStringArray, 'StringArray:\n0:lid number\n1:toolcal=0'], [PyTango.DevString],],


    # 3.6.5.3 Crystallization plate commands
    'putplate': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:plate number\n2:well number\n3:type = No info in docs\n4:toolcal=0'], [PyTango.DevString],],
    'getplate': [[PyTango.DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\\n1:drop=0\n2:toolcal=0'], [PyTango.DevString],],
    'getputplate': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:plate number\n2:well number\n3:type = No info in docs\n4:drop=0\n5:toolcal=0'], [PyTango.DevString],],
    'goto_well': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:plate number\n2:well number\n3:toolcal=0'], [PyTango.DevString],],
    'adjust': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:X_CATS shift (um)\n3:Y_CATS shift (um)'], [PyTango.DevString],],
    'focus': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:Z_CATS shift (um)'], [PyTango.DevString],],
    'expose': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:angle (deg)\n3:# oscillations\n4:expose time\n5:step:'], [PyTango.DevString],],
    'collect': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:angle (deg)\n3:# oscillations\n4:expose time\n5:step\n6:final angle'], [PyTango.DevString],],
    'setplateangle': [[PyTango.DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:angle (deg)'], [PyTango.DevString],],

    # 3.6.5.4 Virtual Inputs
    'vdi9xon': [[PyTango.DevShort, 'input = 90..91'], [PyTango.DevString],],
    'vdi9xoff': [[PyTango.DevShort, 'input = 90..91'], [PyTango.DevString],],

    # 3.6.5.5 Commands for LN2 controller
    'regulon': [[PyTango.DevVoid],[PyTango.DevString],],
    'reguloff': [[PyTango.DevVoid],[PyTango.DevString],],
    'warmon': [[PyTango.DevVoid],[PyTango.DevString],],
    'warmoff': [[PyTango.DevVoid],[PyTango.DevString],],
    'regulon1': [[PyTango.DevVoid],[PyTango.DevString],],
    'reguloff1': [[PyTango.DevVoid],[PyTango.DevString],],
    'regulon2': [[PyTango.DevVoid],[PyTango.DevString],],
    'reguloff2': [[PyTango.DevVoid],[PyTango.DevString],],
    
    # 3.6.5.6 Maintenance commands
    'openlid1': [[PyTango.DevVoid],[PyTango.DevString],],
    'closelid1': [[PyTango.DevVoid],[PyTango.DevString],],
    'openlid2': [[PyTango.DevVoid],[PyTango.DevString],],
    'closelid2': [[PyTango.DevVoid],[PyTango.DevString],],
    'openlid3': [[PyTango.DevVoid],[PyTango.DevString],],
    'closelid3': [[PyTango.DevVoid],[PyTango.DevString],],
    'openlid4': [[PyTango.DevVoid],[PyTango.DevString],],
    'closelid4': [[PyTango.DevVoid],[PyTango.DevString],],
    'opentool': [[PyTango.DevVoid],[PyTango.DevString],],
    'closetool': [[PyTango.DevVoid],[PyTango.DevString],],
    'magneton': [[PyTango.DevVoid],[PyTango.DevString],],
    'magnetoff': [[PyTango.DevVoid],[PyTango.DevString],],
    'heateron': [[PyTango.DevVoid],[PyTango.DevString],],
    'heateroff': [[PyTango.DevVoid],[PyTango.DevString],],
    'initdew1': [[PyTango.DevVoid],[PyTango.DevString],],
    'initdew2': [[PyTango.DevVoid],[PyTango.DevString],],
    'onestaticdw': [[PyTango.DevVoid],[PyTango.DevString],],
    'tworotatingdw': [[PyTango.DevVoid],[PyTango.DevString],],

    # NOT DOCUMENTED THREE NEW COMMANDS...
    'clear_memory': [[PyTango.DevVoid],[PyTango.DevString],],
    'reset_parameters': [[PyTango.DevVoid],[PyTango.DevString],],
    'resetmotion': [[PyTango.DevVoid],[PyTango.DevString],],
    
    # 3.6.5.7 Status commands
    'mon_state': [[PyTango.DevVoid],[PyTango.DevString],],
    'mon_di': [[PyTango.DevVoid],[PyTango.DevString],],
    'mon_do': [[PyTango.DevVoid],[PyTango.DevString],],
    'mon_position': [[PyTango.DevVoid],[PyTango.DevString],],
    'mon_message': [[PyTango.DevVoid],[PyTango.DevString],],
    'mon_config': [[PyTango.DevVoid],[PyTango.DevString],],
    
    # BACKDOOR FOR SOFTWARE UPGRADES OR ANYTHING NEEDED... ;-D
    'send_op_cmd': [[PyTango.DevString], [PyTango.DevString],],
    'send_mon_cmd': [[PyTango.DevString], [PyTango.DevString],],

    }

  def __init__(self, name):
    PyTango.DeviceClass.__init__(self, name)
    self.set_type(name)


def main():
  try:
    util = PyTango.Util(sys.argv)
    util.add_class(CATSClass, CATS, 'CATS')
    
    U = PyTango.Util.instance()
    U.server_init()
    U.server_run()

  except PyTango.DevFailed, e:
    print '-------> Received a DevFailed exception:',e
  except Exception,e:
    print '-------> An unforeseen exception occured....',e

if __name__ == "__main__":
    main()
