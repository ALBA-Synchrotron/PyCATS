import time
import logging
from tango import (Device_4Impl, DeviceClass, DevState, DevVoid,
                   DevUShort, DevFloat, DevBoolean, DevString, DevShort,
                   DevVarStringArray, ArgType, READ, SCALAR, SPECTRUM)
from .utils import CATS2TANGO, TANGO2CATS
from ..messages import di_help, do_help, message_help
from ..core import CS8Connection
from ..logger import get_logger
from .. import __version__


# class StatusUpdateThread(threading.Thread):
#     def __init__(self, ds):
#         threading.Thread.__init__(self)
#         self.ds = ds
#         self.should_run = False
#
#     def stopRunning(self):
#         self.should_run = False
#
#     def run(self):
#         while self.should_run:
#             try:
#                 new_status_dict = self.ds.cs8connection.getStatusDict()
#                 self.ds.processStatusDict(new_status_dict)
#             except Exception as e:
#                 import traceback
#                 print("error reading status", traceback.format_exc())
#                 self.ds.notifyNewState(
#                     DevState.ALARM,
#                     'Exception getting status from the CATS system:\n%s' %
#                     str(e))
#             time.sleep(self.ds.update_freq_ms / 1000.)


class CATS(Device_4Impl):
    """ A Python Device Server to communicate with the IRELEC's CATS Sample Changer
    """

    def __init__(self, klass, name):
        Device_4Impl.__init__(self, klass, name)
        self.cs8connection = CS8Connection()
        self.logger = get_logger(__name__)
        # self.status_update_thread = None
        self.status_dict = {}
        self.init_device()

        # Tell Tango that the attributes have events
        for attr_name in list(self.get_device_class().attr_list.keys()):
            self.set_change_event(attr_name, True, False)

        self.set_change_event('State', True, False)
        self.set_change_event('Status', True, False)
        self.logger.info('CATS state dictionary updates every %s ms' %
                         self.update_freq_ms)
        self.logger.info('Ready to accept requests.')

    def update_status(self):
        if self.cs8connection.connected:
            # self.logger.debug("getting status dict...")
            try:
                new_status_dict = self.cs8connection.get_status_dict()
                self.process_status_dict(new_status_dict)
            except Exception as e:
                import traceback
                self.logger.error("Error reading status: %s" % traceback.format_exc())
                self.notify_new_state(
                    DevState.ALARM,
                    'Exception when getting status from CATS server:\n%s' %
                    str(e))
            time.sleep(self.update_freq_ms / 1000.)
        else:
            # self.logger.debug("Requesting reconnection...")
            time.sleep(self.update_freq_ms / 1000.)

    def check_reconnection(self):
        if not self.cs8connection.connected:
            self.cs8connection.reconnect(every=self.reconnection_interval,
                                         timeout=self.reconnection_timeout)

    def init_device(self):
        self.get_device_properties(self.get_device_class())
        try:
            self.cs8connection.set_model(self.model)
            self.cs8connection.set_puck_types(self.puck_types)
            self.cs8connection.connect(
                self.host, self.port_operate, self.port_monitor)
            # self.status_update_thread = StatusUpdateThread(self)
            # self.status_update_thread.start()
            self.notify_new_state(
                DevState.ON,
                'Connected to the CATS system.')
        except Exception as e:
            self.notify_new_state(
                DevState.ALARM,
                'Exception connecting to the CATS system:\n' + str(e))

    def delete_device(self):
        # if self.status_update_thread is not None:
        #     self.status_update_thread.stopRunning()
        self.status_dict = {}
        self.cs8connection.disconnect()

    def notify_new_state(self, state, status=None):
        self.set_state(state)
        if status is None:
            status = 'Device is in %s state.' % state
        self.set_status(status)
        self.push_change_event('State', state)
        self.push_change_event('Status', status)

    def process_status_dict(self, new_status_dict):

        for catsk, new_value in new_status_dict.items():
            if new_status_dict[catsk] != self.status_dict.get(catsk, None):
                self.status_dict[catsk] = new_value
                # Notify any tango client that the value has changed
                attr_name = CATS2TANGO[catsk]
                self.push_change_event(attr_name, new_value)

        new_status = 'Powered = %s\n' % \
                     self.status_dict[TANGO2CATS['Powered']]
        new_status += 'Tool = %s\n' % \
                      self.status_dict[TANGO2CATS['Tool']]
        new_status += 'Path = %s\n' % \
                      self.status_dict[TANGO2CATS['Path']]
        new_status += 'PathRunning = %s\n' % \
                      self.status_dict[TANGO2CATS['PathRunning']]
        new_status += 'PathSafe = %s\n' % \
                      self.is_path_safe()

        if self.cs8connection.get_model() != "ISARA":
            new_status += 'LidSampleOnTool= %s\n' % \
                          self.status_dict[TANGO2CATS['LidSampleOnTool']]
        else:
            new_status += 'PuckNumberOnTool = %s\n' % \
                          self.status_dict[TANGO2CATS['PuckNumberOnTool']]
        new_status += 'NumSampleOnTool = %s\n' % \
                      self.status_dict[TANGO2CATS['NumSampleOnTool']]

        if self.cs8connection.get_model() == "ISARA":
            new_status += 'PuckNumberOnTool2 = %s\n' % \
                          self.status_dict[TANGO2CATS['PuckNumberOnTool2']]
            new_status += 'NumSampleOnTool2 = %s\n' % \
                          self.status_dict[TANGO2CATS['NumSampleOnTool2']]
        new_status += 'Barcode = %s\n' % \
                      self.status_dict[TANGO2CATS['Barcode']]

        if self.cs8connection.get_model() != "ISARA":
            new_status += 'LidSampleOnDiff = %s\n' %\
                          self.status_dict[TANGO2CATS['LidSampleOnDiff']]
        else:
            new_status += 'PuckNumberOnDiff = %s\n' %\
                          self.status_dict[TANGO2CATS['PuckSampleOnDiff']]
        new_status += 'NumSampleOnDiff = %s\n' % \
                      self.status_dict[TANGO2CATS['NumSampleOnDiff']]
        new_status += 'NumPlateOnTool = %s\n' % \
                      self.status_dict[TANGO2CATS['NumPlateOnTool']]

        if self.cs8connection.get_model() != "ISARA":
            new_status += 'Well = %s\n' % \
                          self.status_dict[TANGO2CATS['Well']]
        new_status += 'LN2Regulating = %s\n' % \
                      self.status_dict[TANGO2CATS['LN2Regulating']]

        if self.cs8connection.get_model() != "ISARA":
            new_status += 'LN2Warming = %s\n' % \
                          self.status_dict[TANGO2CATS['LN2Warming']]
        new_status += 'AutoMode = %s\n' % \
                      self.status_dict[TANGO2CATS['AutoMode']]
        new_status += 'DefaultStatus = %s\n' % \
                      self.status_dict[TANGO2CATS['DefaultStatus']]
        new_status += 'SpeedRatio = %s\n' % \
                      self.status_dict[TANGO2CATS['SpeedRatio']]

        if self.cs8connection.get_model() != "ISARA":
            new_status += 'PuckDetectionDewar1 = %s\n' % \
                          self.status_dict[TANGO2CATS['PuckDetectionDewar1']]
            new_status += 'PuckDetectionDewar2 = %s\n' % \
                          self.status_dict[TANGO2CATS['PuckDetectionDewar2']]
        new_status += 'PositionNumberDewar1 = %s\n' % \
                      self.status_dict[TANGO2CATS['PositionNumberDewar1']]

        if self.cs8connection.get_model() != "ISARA":
            new_status += 'PositionNumberDewar2 = %s\n' % \
                          self.status_dict[TANGO2CATS['PositionNumberDewar2']]

        if self.cs8connection.get_model() == "ISARA":
            new_status += 'CurrentNumberOfSoaking = %s\n' % \
                          self.status_dict[TANGO2CATS['CurrentNumberOfSoaking']]

        if new_status_dict[TANGO2CATS['Path']] != '':
            self.notify_new_state(DevState.RUNNING, new_status)
        else:
            self.notify_new_state(DevState.ON, new_status)

    def is_path_safe(self):
        return self.cs8connection.is_path_safe()

    def is_recovery_needed(self):
        return self.cs8connection.is_recovery_needed()

    #################################################################
    #                        READ ATTRIBUTES
    #################################################################

    # STATE PARAMS pycats.state_params

    def read_Powered(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Powered']])

    def read_AutoMode(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['AutoMode']])

    def read_DefaultStatus(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['DefaultStatus']])

    def read_Tool(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Tool']])

    def read_Path(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Path']])

    def read_CatsModel(
        self, attr): attr.set_value(
        self.cs8connection.get_model())

    def read_NbCassettes(
        self, attr): attr.set_value(
        self.cs8connection.get_number_pucks())

    def read_CassettePresence(
        self, attr): attr.set_value(
        self.cs8connection.get_puck_presence())

    def read_CassetteType(
        self, attr): attr.set_value(
        self.cs8connection.get_puck_types())

    def read_LidSampleOnTool(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['LidSampleOnTool']])

    def read_NumSampleOnTool(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['NumSampleOnTool']])

    def read_LidSampleOnDiff(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['LidSampleOnDiff']])

    def read_NumSampleOnDiff(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['NumSampleOnDiff']])

    def read_NumPlateOnTool(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['NumPlateOnTool']])

    def read_Well(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Well']])

    def read_Barcode(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Barcode']])

    def read_PathRunning(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PathRunning']])

    def read_PathSafe(
        self, attr): attr.set_value(
        self.cs8connection.is_path_safe())

    def read_RecoveryNeeded(
        self, attr): attr.set_value(
        self.cs8connection.is_recovery_needed())

    def read_LastCommandSent(
        self, attr): attr.set_value(
        self.cs8connection.get_last_command_sent())

    def read_LN2Regulating(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['LN2Regulating']])

    def read_LN2Warming(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['LN2Warming']])

    def read_SpeedRatio(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['SpeedRatio']])

    def read_PuckDetectionDewar1(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PuckDetectionDewar1']])

    def read_PuckDetectionDewar2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PuckDetectionDewar2']])

    def read_PositionNumberDewar1(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PositionNumberDewar1']])

    def read_PositionNumberDewar2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PositionNumberDewar2']])

    def read_PuckNumberInTool2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PuckNumberInTool2']])

    def read_SampleNumberInTool2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['SampleNumberInTool2']])

    def read_CurrentNumberOfSoaking(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['CurrentNumberOfSoaking']])

    def read_PuckTypeLid1(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PuckTypeLid1']])

    def read_PuckTypeLid2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PuckTypeLid2']])

    def read_PuckTypeLid3(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['PuckTypeLid3']])

    # DI PARAMS pycats.di_params
    def read_di_CryoOK(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CryoOK']])

    def read_di_EStopAirpresOK(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_EStopAirpresOK']])

    def read_di_CollisonSensorOK(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CollisonSensorOK']])

    def read_di_CryoHighLevelAlarm(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CryoHighLevelAlarm']])

    def read_di_CryoHighLevel(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CryoHighLevel']])

    def read_di_CryoLowLevel(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CryoLowLevel']])

    def read_di_CryoLowLevelAlarm(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CryoLowLevelAlarm']])

    def read_di_CryoLiquidDetection(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_CryoLiquidDetection']])

    def read_di_PRI1_GFM(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_GFM']])

    def read_di_PRI2_API(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_API']])

    def read_di_PRI3_APL(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_APL']])

    def read_di_PRI4_SOM(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_SOM']])

    def read_di_PRI_GFM(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_GFM']])

    def read_di_PRI_API(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_API']])

    def read_di_PRI_APL(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_APL']])

    def read_di_PRI_SOM(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI_SOM']])

    def read_di_DiffPlateMode(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_DiffPlateMode']])

    def read_di_PlateOnDiff(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PlateOnDiff']])

    def read_di_Cassette1Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette1Presence']])

    def read_di_Cassette2Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette2Presence']])

    def read_di_Cassette3Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette3Presence']])

    def read_di_Cassette4Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette4Presence']])

    def read_di_Cassette5Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette5Presence']])

    def read_di_Cassette6Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette6Presence']])

    def read_di_Cassette7Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette7Presence']])

    def read_di_Cassette8Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette8Presence']])

    def read_di_Cassette9Presence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Cassette9Presence']])

    def read_di_Lid1Open(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Lid1Open']])

    def read_di_Lid2Open(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Lid2Open']])

    def read_di_Lid3Open(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_Lid3Open']])

    def read_di_ToolOpen(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_ToolOpen']])

    def read_di_ToolClosed(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_ToolClosed']])

    def read_di_LimSW1RotGripAxis(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_LimSW1RotGripAxis']])

    def read_di_LimSW2RotGripAxis(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_LimSW2RotGripAxis']])

    def read_di_ModbusPLCLifeBit(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_ModbusPLCLifeBit']])

    def read_di_LifeBitFromPLC(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_LifeBitFromPLC']])

    def read_di_ActiveLidOpened(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_ActiveLidOpened']])

    def read_di_NewActiveLidOpened(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_NewActiveLidOpened']])

    def read_di_ToolChangerOpened(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_ToolChangerOpened']])

    def read_di_ActiveCassettePresence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_ActiveCassettePresence']])

    def read_di_NewActiveCassettePresence(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_NewActiveCassettePresence']])

    def read_di_AllLidsClosed(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_AllLidsClosed']])

    def read_di_PRI5(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI5']])

    def read_di_PRI6(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI6']])

    def read_di_PRI7(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI7']])

    def read_di_PRI8(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI8']])

    def read_di_PRI9(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI9']])

    def read_di_PRI10(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI10']])

    def read_di_PRI11(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI11']])

    def read_di_PRI12(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_PRI12']])

    def read_di_VI90(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI90']])

    def read_di_VI91(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI91']])

    def read_di_VI92(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI92']])

    def read_di_VI93(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI93']])

    def read_di_VI94(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI94']])

    def read_di_VI95(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI95']])

    def read_di_VI96(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI96']])

    def read_di_VI97(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI97']])

    def read_di_VI98(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI98']])

    def read_di_VI99(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['di_VI99']])

    # DO PARAMS pycats.do_params
    def read_do_ToolChanger(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_ToolChanger']])

    def read_do_ToolOpenClose(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_ToolOpenClose']])

    def read_do_FastOutput(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_FastOutput']])

    def read_do_PRO1_MON(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO1_MON']])

    def read_do_PRO2_COL(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO2_COL']])

    def read_do_PRO3_LNW(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO3_LNW']])

    def read_do_PRO4_LNA(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO4_LNA']])

    def read_do_GreenLight(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_GreenLight']])

    def read_do_PilzRelayReset(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PilzRelayReset']])

    def read_do_ServoCardOn(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_ServoCardOn']])

    def read_do_ServoCardRotation(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_ServoCardRotation']])

    def read_do_CryoValveLN2C(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CryoValveLN2C']])

    def read_do_CryoValveLN2E(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CryoValveLN2E']])

    def read_do_CryoValveGN2E(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CryoValveGN2E']])

    def read_do_HeaterOnOff(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_HeaterOnOff']])

    def read_do_OpenCloseLid11(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid11']])

    def read_do_OpenCloseLid12(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid12']])

    def read_do_OpenCloseLid21(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid21']])

    def read_do_OpenCloseLid22(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid22']])

    def read_do_OpenCloseLid31(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid31']])

    def read_do_OpenCloseLid32(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid32']])

    def read_do_RequestDew1PosBit1(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew1PosBit1']])

    def read_do_RequestDew1PosBit2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew1PosBit2']])

    def read_do_RequestDew1PosBit3(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew1PosBit3']])

    def read_do_RequestDew1PosBit4(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew1PosBit4']])

    def read_do_OpenLid(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenLid']])

    def read_do_CloseLid(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CloseLid']])

    def read_do_OpenNewLid(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenNewLid']])

    def read_do_CloseNewLid(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CloseNewLid']])

    def read_do_BarcodeReader(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_BarcodeReader']])

    def read_do_CloseAllLids(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CloseAllLids']])

    def read_do_PRO5_IDL(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO5_IDL']])

    def read_do_PRO6_RAH(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO6_RAH']])

    def read_do_PRO7_RI1(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO7_RI1']])

    def read_do_PRO8_RI2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO8_RI2']])

    def read_do_PRO9_LIO(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO9_LIO']])

    def read_do_PRO10(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO10']])

    def read_do_PRO11(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO11']])

    def read_do_PRO12(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO12']])

    def read_do_RequestDew2PosBit1(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew2PosBit1']])

    def read_do_RequestDew2PosBit2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew2PosBit2']])

    def read_do_RequestDew2PosBit3(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew2PosBit3']])

    def read_do_RequestDew2PosBit4(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RequestDew2PosBit4']])

    def read_do_CryoValveLN2CDew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CryoValveLN2CDew2']])

    def read_do_CryoValveLN2EDew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CryoValveLN2EDew2']])

    def read_do_CryoVavleGN2EDew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_CryoVavleGN2EDew2']])

    def read_do_OpenCloseLid31Dew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid31Dew2']])

    def read_do_OpenCloseLid32Dew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid32Dew2']])

    def read_do_OpenCloseLid41Dew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid41Dew2']])

    def read_do_OpenCloseLid42Dew2(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_OpenCloseLid42Dew2']])

    def read_do_PRO13(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO13']])

    def read_do_PRO14(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO14']])

    def read_do_PRO15(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO15']])

    def read_do_PRO16(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_PRO16']])

    def read_do_RotationDewNewPosWorking(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RotationDewNewPosWorking']])

    def read_do_RotationDewarPosCassLoading(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RotationDewarPosCassLoading']])

    def read_do_RotationDewPosWorking(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['do_RotationDewPosWorking']])

    # POSITION PARAMS pycats.position_params
    def read_Xpos(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Xpos']])

    def read_Ypos(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Ypos']])

    def read_Zpos(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Zpos']])

    def read_RXpos(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['RXpos']])

    def read_RYpos(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['RYpos']])

    def read_RZpos(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['RZpos']])

    # MESSAGE
    def read_Message(self, attr): attr.set_value(
        self.status_dict[TANGO2CATS['Message']])

    # Convenience values
    def read_SampleOnDiff(self, attr): attr.set_value(self.is_sample_on_diff())

    # Version
    def read_Version(self, attr): attr.set_value(__version__)

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

    def recoverFailure(self): return self.cs8connection.start_recovery()

    # 3.6.5.2 Trajectories commands
    def home(self, argin):
        tool = argin
        return self.cs8connection.home(tool)

    def safe(self, argin):
        tool = argin
        return self.cs8connection.safe(tool)

    def put(self, argin):
        if self.is_sample_on_diff():
            raise Exception(
                "Put operation not authorized while a sample is detected on magnet")
        tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.put(
            tool,
            puck_lid,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def put_HT(self, argin):
        tool, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.put_HT(
            tool, sample, type, toolcal, x_shift, y_shift, z_shift)

    def put_bcrd(self, argin):
        if self.is_sample_on_diff():
            raise Exception(
                "Put operation not authorized while a sample is detected on magnet")
        tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.put_bcrd(
            tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift)

    def get(self, argin):
        tool, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.get(tool, toolcal, x_shift, y_shift, z_shift)

    def get_HT(self, argin):
        tool, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.get_HT(
            tool, toolcal, x_shift, y_shift, z_shift)

    def getput(self, argin):
        tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.getput(
            tool,
            puck_lid,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def getput_HT(self, argin):
        tool, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.getput_HT(
            tool, sample, type, toolcal, x_shift, y_shift, z_shift)

    def getput_bcrd(self, argin):
        tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.getput_bcrd(
            tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift)

    def barcode(self, argin):
        tool, puck_lid, sample, type, toolcal = argin
        return self.cs8connection.barcode(
            tool, puck_lid, sample, type, toolcal)

    def back(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            tool = argin[0]
            return self.cs8connection.back(tool)
        else:
            tool, toolcal = argin
            return self.cs8connection.back(tool, toolcal)

    def transfer(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "Transfer command not available for ISARA model"
        tool, lid, sample, newlid, newsample, type, toolcal = argin
        return self.cs8connection.transfer(
            tool, lid, sample, newlid, newsample, type, toolcal)

    def pick(self, argin):
        tool, puck, sample, type = argin
        return self.cs8connection.pick(tool, puck, sample, type)

    def getpuckpick(self, argin):
        tool, puck_lid, sample, type, toolcal, x_shift, y_shift, z_shift = argin
        return self.cs8connection.getputpick(tool, puck_lid, sample, type,
                                             x_shift, y_shift, z_shift)

    def soak(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            tool = argin[0]
            return self.cs8connection.soak(tool)
        else:
            tool, puck_lid = argin
            return self.cs8connection.soak(tool, puck_lid)

    def dry(self, argin):
        tool = argin
        return self.cs8connection.dry(tool)

    def dryhome(self, argin):
        tool = argin
        return self.cs8connection.dryhome(tool)

    def gotodif(self, argin):
        tool, puck_lid, sample, type, toolcal = argin
        return self.cs8connection.gotodif(
            tool, puck_lid, sample, type, toolcal)

    def rd_position(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "rd_position is not a command for ISARA model"
        tool, puck_lid = argin
        return self.cs8connection.rd_position(tool, puck_lid)

    def rd_load(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "rd_load is not a command for ISARA model"
        tool, newpuck_lid = argin
        return self.cs8connection.rd_load(tool, newpuck_lid)

    def puckdetect(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "puckdetect is not a command for ISARA model"
        puck_lid, toolcal = argin
        return self.cs8connection.puckdetect(puck_lid, toolcal)

    def recover(self, argin):
        tool = argin
        return self.cs8connection.recover(tool)

    def setondiff(self, argin):
        puck_lid, sample, type = argin
        return self.cs8connection.setondiff(puck_lid, sample, type)

    def settool(self, argin):
        puck_lid, sample, type = argin
        return self.cs8connection.settool(puck_lid, sample, type)

    def settool2(self, argin):
        puck_lid, sample, type = argin
        return self.cs8connection.settool(puck_lid, sample, type)

    def cap_on_lid(self, argin):
        tool = argin
        return self.cs8connection.cap_on_lid(tool)

    def cap_off_lid(self, argin):
        tool = argin
        return self.cs8connection.cap_off_lid(tool)

    # 3.6.5.3 Crystallization plate commands
    def putplate(self, argin):
        tool, plate, well, type, toolcal = argin
        return self.cs8connection.putplate(tool, plate, well, type, toolcal)

    def getplate(self, argin):
        tool, drop, toolcal = argin
        return self.cs8connection.getplate(tool, drop, toolcal)

    def getputplate(self, argin):
        tool, plate, well, type, drop, toolcal = argin
        return self.cs8connection.getputplate(
            tool, plate, well, type, drop, toolcal)

    def goto_well(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "goto_well is not a command for ISARA model"
        tool, plate, well, toolcal = argin
        return self.cs8connection.goto_well(tool, plate, well, toolcal)

    def adjust(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "adjust is not a command for ISARA model"
        tool, toolcal, x_shift, y_shift = argin
        return self.cs8connection.adjust(tool, toolcal, x_shift, y_shift)

    def focus(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "focus is not a command for ISARA model"
        tool, toolcal, z_shift = argin
        return self.cs8connection.focus(tool, toolcal, z_shift)

    def expose(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "expose is not a command for ISARA model"
        tool, toolcal, angle, oscillations, exp_time, step = argin
        return self.cs8connection.expose(
            tool, toolcal, angle, oscillations, exp_time, step)

    def collect(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "collect is not a command for ISARA model"
        tool, toolcal, angle, oscillations, exp_time, step, final_angle = argin
        return self.cs8connection.collect(
            tool, toolcal, angle, oscillations, exp_time, step, final_angle)

    def setplateangle(self, argin):
        if self.cs8connection.get_model() == "ISARA":
            return "setplateangle is not a command for ISARA model"
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

    def opentool2(self): return self.cs8connection.opentool2()

    def closetool2(self): return self.cs8connection.closetool2()

    def magneton(self): return self.cs8connection.magneton()

    def magnetoff(self): return self.cs8connection.magnetoff()

    def heateron(self): return self.cs8connection.heateron()

    def heateroff(self): return self.cs8connection.heateroff()

    def initdew1(self): return self.cs8connection.initdew1()

    def initdew2(self): return self.cs8connection.initdew2()

    def onestaticdw(self): return self.cs8connection.onestaticdw()

    def tworotatingdw(self): return self.cs8connection.tworotatingdw()

    def openlid(self): return self.cs8connection.openlid()

    def closelid(self): return self.cs8connection.closelid()

    def clearbcrd(self): return self.cs8connection.clearbcrd()

    def remotespeedon(self): return self.cs8connection.remotespeedon()

    def remotespeedoff(self): return self.cs8connection.remotespeedoff()

    def speedup(self): return self.cs8connection.speedup()

    def speeddown(self): return self.cs8connection.speeddown()

    #
    def clear_memory(self): return self.cs8connection.clear_memory()

    def reset_parameters(self): return self.cs8connection.reset_parameters()

    def resetmotion(self): return self.cs8connection.resetmotion()

    def toolcalibration(self, argin):
        tool = argin
        return self.cs8connection.toolcalibration(tool)

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

    def is_sample_on_diff(self):
        num_sample_on_diff = self.status_dict[TANGO2CATS['NumSampleOnDiff']]
        sample_on_magnet = self.status_dict[TANGO2CATS['di_PRI_SOM']]

        return (num_sample_on_diff != -1) or sample_on_magnet


class CATSClass(DeviceClass):
    device_property_list = {
        'host': [DevString,
                 "Hostname of the CATS system.",
                 []],
        'port_operate': [DevUShort,
                         "Socket's port to operatethe CATS system.",
                         [1000]],
        'port_monitor': [DevUShort,
                         "Socket's port to monitor the CATS system.",
                         [10000]],
        'model': [DevString,
                  "System model (cats/isara).",
                  ["cats"]],
        'puck_types': [DevString,
                       "nb_pucks x puck_type (2=unipuck,1=spine,0=ignore).",
                       ["111111111"]],
        'update_freq_ms': [DevUShort,
                           "Update time in ms for the CATS status.",
                           [300]],
        'reconnection_timeout': [DevUShort,
                                 "Timeout in seconds to reconnect or stop the DS.",
                                 [30]],
        'reconnection_interval': [DevUShort,
                                  "Wait time in seconds between reconnection attempts",
                                  [5]]
    }

    attr_list = {
        # STATE PARAMS pycats.state_params
        'Powered': [[DevBoolean, SCALAR, READ]],
        'AutoMode': [[DevBoolean, SCALAR, READ]],
        'DefaultStatus': [[DevBoolean, SCALAR, READ]],
        'Tool': [[DevString, SCALAR, READ]],
        'Path': [[DevString, SCALAR, READ]],
        'CatsModel': [[DevString, SCALAR, READ]],
        'NbCassettes': [[DevShort, SCALAR, READ]],
        'CassettePresence': [[ArgType.DevShort, SPECTRUM, READ, 32]],
        'CassetteType': [[ArgType.DevShort, SPECTRUM, READ, 32]],
        'LidSampleOnTool': [[DevShort, SCALAR, READ]],
        'NumSampleOnTool': [[DevShort, SCALAR, READ]],
        'LidSampleOnDiff': [[DevShort, SCALAR, READ]],
        'NumSampleOnDiff': [[DevShort, SCALAR, READ]],
        'NumPlateOnTool': [[DevShort, SCALAR, READ]],
        'Well': [[DevShort, SCALAR, READ]],
        'Barcode': [[DevString, SCALAR, READ]],
        'PathRunning': [[DevBoolean, SCALAR, READ]],
        'PathSafe': [[DevBoolean, SCALAR, READ]],
        'RecoveryNeeded': [[DevBoolean, SCALAR, READ]],
        'LastCommandSent': [[DevString, SCALAR, READ]],
        'LN2Regulating': [[DevBoolean, SCALAR, READ]],
        'LN2Warming': [[DevBoolean, SCALAR, READ]],
        'SpeedRatio': [[DevFloat, SCALAR, READ]],
        'PuckDetectionDewar1': [[DevShort, SCALAR, READ]],
        'PuckDetectionDewar2': [[DevShort, SCALAR, READ]],
        'PositionNumberDewar1': [[DevShort, SCALAR, READ]],
        'PositionNumberDewar2': [[DevShort, SCALAR, READ]],
        'PuckNumberInTool2': [[DevShort, SCALAR, READ]],
        'SampleNumberInTool2': [[DevShort, SCALAR, READ]],
        'CurrentNumberOfSoaking': [[DevShort, SCALAR, READ]],
        'PuckTypeLid1': [[DevShort, SCALAR, READ]],
        'PuckTypeLid2': [[DevShort, SCALAR, READ]],
        'PuckTypeLid3': [[DevShort, SCALAR, READ]],

        # DI PARAMS pycats.di_params
        'di_CryoOK': [[DevBoolean, SCALAR, READ],
                      {'description': 'False:' + di_help[TANGO2CATS['di_CryoOK']][0] + ' True:' + di_help[TANGO2CATS['di_CryoOK']][1]}],
        'di_EStopAirpresOK': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + di_help[TANGO2CATS['di_EStopAirpresOK']][0] + ' True:' + di_help[TANGO2CATS['di_EStopAirpresOK']][1]}],
        'di_CollisonSensorOK': [[DevBoolean, SCALAR, READ],
                                {'description': 'False:' + di_help[TANGO2CATS['di_CollisonSensorOK']][0] + ' True:' + di_help[TANGO2CATS['di_CollisonSensorOK']][1]}],
        'di_CryoHighLevelAlarm': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + di_help[TANGO2CATS['di_CryoHighLevelAlarm']][0] + ' True:' + di_help[TANGO2CATS['di_CryoHighLevelAlarm']][1]}],
        'di_CryoHighLevel': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + di_help[TANGO2CATS['di_CryoHighLevel']][0] + ' True:' + di_help[TANGO2CATS['di_CryoHighLevel']][1]}],
        'di_CryoLowLevel': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + di_help[TANGO2CATS['di_CryoLowLevel']][0] + ' True:' + di_help[TANGO2CATS['di_CryoLowLevel']][1]}],
        'di_CryoLowLevelAlarm': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_CryoLowLevelAlarm']][0] + ' True:' + di_help[TANGO2CATS['di_CryoLowLevelAlarm']][1]}],
        'di_CryoLiquidDetection': [[DevBoolean, SCALAR, READ],
                                   {'description': 'False:' + di_help[TANGO2CATS['di_CryoLiquidDetection']][0] + ' True:' + di_help[TANGO2CATS['di_CryoLiquidDetection']][1]}],

        # we keep this for backward compatibility. for ISARA / CATS
        # compatibility we remove number of process input from attribute name
        'di_PRI1_GFM': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_PRI_GFM']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_GFM']][1]}],
        'di_PRI2_API': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_PRI_API']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_API']][1]}],
        'di_PRI3_APL': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_PRI_APL']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_APL']][1]}],
        'di_PRI4_SOM': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_PRI_SOM']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_SOM']][1]}],
        'di_PRI_GFM': [[DevBoolean, SCALAR, READ],
                       {'description': 'False:' + di_help[TANGO2CATS['di_PRI_GFM']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_GFM']][1]}],
        'di_PRI_API': [[DevBoolean, SCALAR, READ],
                       {'description': 'False:' + di_help[TANGO2CATS['di_PRI_API']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_API']][1]}],
        'di_PRI_APL': [[DevBoolean, SCALAR, READ],
                       {'description': 'False:' + di_help[TANGO2CATS['di_PRI_APL']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_APL']][1]}],
        'di_PRI_SOM': [[DevBoolean, SCALAR, READ],
                       {'description': 'False:' + di_help[TANGO2CATS['di_PRI_SOM']][0] + ' True:' + di_help[TANGO2CATS['di_PRI_SOM']][1]}],
        'di_PlateOnDiff': [[DevBoolean, SCALAR, READ],
                           {'description': 'False:' + di_help[TANGO2CATS['di_PlateOnDiff']][0] + ' True:' + di_help[TANGO2CATS['di_PlateOnDiff']][1]}],
        'di_DiffPlateMode': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + di_help[TANGO2CATS['di_DiffPlateMode']][0] + ' True:' + di_help[TANGO2CATS['di_DiffPlateMode']][1]}],
        'di_Cassette1Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette1Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette1Presence']][1]}],
        'di_Cassette2Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette2Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette2Presence']][1]}],
        'di_Cassette3Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette3Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette3Presence']][1]}],
        'di_Cassette4Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette4Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette4Presence']][1]}],
        'di_Cassette5Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette5Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette5Presence']][1]}],
        'di_Cassette6Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette6Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette6Presence']][1]}],
        'di_Cassette7Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette7Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette7Presence']][1]}],
        'di_Cassette8Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette8Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette8Presence']][1]}],
        'di_Cassette9Presence': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_Cassette9Presence']][0] + ' True:' + di_help[TANGO2CATS['di_Cassette9Presence']][1]}],
        'di_Lid1Open': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_Lid1Open']][0] + ' True:' + di_help[TANGO2CATS['di_Lid1Open']][1]}],
        'di_Lid2Open': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_Lid2Open']][0] + ' True:' + di_help[TANGO2CATS['di_Lid2Open']][1]}],
        'di_Lid3Open': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_Lid3Open']][0] + ' True:' + di_help[TANGO2CATS['di_Lid3Open']][1]}],
        'di_ToolOpen': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + di_help[TANGO2CATS['di_ToolOpen']][0] + ' True:' + di_help[TANGO2CATS['di_ToolOpen']][1]}],
        'di_ToolClosed': [[DevBoolean, SCALAR, READ],
                          {'description': 'False:' + di_help[TANGO2CATS['di_ToolClosed']][0] + ' True:' + di_help[TANGO2CATS['di_ToolClosed']][1]}],
        'di_LimSW1RotGripAxis': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_LimSW1RotGripAxis']][0] + ' True:' + di_help[TANGO2CATS['di_LimSW1RotGripAxis']][1]}],
        'di_LimSW2RotGripAxis': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_LimSW2RotGripAxis']][0] + ' True:' + di_help[TANGO2CATS['di_LimSW2RotGripAxis']][1]}],
        'di_ModbusPLCLifeBit': [[DevBoolean, SCALAR, READ],
                                {'description': 'False:' + di_help[TANGO2CATS['di_ModbusPLCLifeBit']][0] + ' True:' + di_help[TANGO2CATS['di_ModbusPLCLifeBit']][1]}],
        'di_LifeBitFromPLC': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + di_help[TANGO2CATS['di_LifeBitFromPLC']][0] + ' True:' + di_help[TANGO2CATS['di_LifeBitFromPLC']][1]}],
        'di_ActiveLidOpened': [[DevBoolean, SCALAR, READ],
                               {'description': 'False:' + di_help[TANGO2CATS['di_ActiveLidOpened']][0] + ' True:' + di_help[TANGO2CATS['di_ActiveLidOpened']][1]}],
        'di_NewActiveLidOpened': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + di_help[TANGO2CATS['di_NewActiveLidOpened']][0] + ' True:' + di_help[TANGO2CATS['di_NewActiveLidOpened']][1]}],
        'di_ToolChangerOpened': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + di_help[TANGO2CATS['di_ToolChangerOpened']][0] + ' True:' + di_help[TANGO2CATS['di_ToolChangerOpened']][1]}],
        'di_ActiveCassettePresence': [[DevBoolean, SCALAR, READ],
                                      {'description': 'False:' + di_help[TANGO2CATS['di_ActiveCassettePresence']][0] + ' True:' + di_help[TANGO2CATS['di_ActiveCassettePresence']][1]}],
        'di_NewActiveCassettePresence': [[DevBoolean, SCALAR, READ],
                                         {'description': 'False:' + di_help[TANGO2CATS['di_NewActiveCassettePresence']][0] + ' True:' + di_help[TANGO2CATS['di_NewActiveCassettePresence']][1]}],
        'di_AllLidsClosed': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + di_help[TANGO2CATS['di_AllLidsClosed']][0] + ' True:' + di_help[TANGO2CATS['di_AllLidsClosed']][1]}],
        'di_PRI5': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_PRI5']][0] + ' True:' + di_help[TANGO2CATS['di_PRI5']][1]}],
        'di_PRI6': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_PRI6']][0] + ' True:' + di_help[TANGO2CATS['di_PRI6']][1]}],
        'di_PRI7': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_PRI7']][0] + ' True:' + di_help[TANGO2CATS['di_PRI7']][1]}],
        'di_PRI8': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_PRI8']][0] + ' True:' + di_help[TANGO2CATS['di_PRI8']][1]}],
        'di_PRI9': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_PRI9']][0] + ' True:' + di_help[TANGO2CATS['di_PRI9']][1]}],
        'di_PRI10': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + di_help[TANGO2CATS['di_PRI10']][0] + ' True:' + di_help[TANGO2CATS['di_PRI10']][1]}],
        'di_PRI11': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + di_help[TANGO2CATS['di_PRI11']][0] + ' True:' + di_help[TANGO2CATS['di_PRI11']][1]}],
        'di_PRI12': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + di_help[TANGO2CATS['di_PRI12']][0] + ' True:' + di_help[TANGO2CATS['di_PRI12']][1]}],
        'di_VI90': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI90']][0] + ' True:' + di_help[TANGO2CATS['di_VI90']][1]}],
        'di_VI91': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI91']][0] + ' True:' + di_help[TANGO2CATS['di_VI91']][1]}],
        'di_VI92': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI92']][0] + ' True:' + di_help[TANGO2CATS['di_VI92']][1]}],
        'di_VI93': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI93']][0] + ' True:' + di_help[TANGO2CATS['di_VI93']][1]}],
        'di_VI94': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI94']][0] + ' True:' + di_help[TANGO2CATS['di_VI94']][1]}],
        'di_VI95': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI95']][0] + ' True:' + di_help[TANGO2CATS['di_VI95']][1]}],
        'di_VI96': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI96']][0] + ' True:' + di_help[TANGO2CATS['di_VI96']][1]}],
        'di_VI97': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI97']][0] + ' True:' + di_help[TANGO2CATS['di_VI97']][1]}],
        'di_VI98': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI98']][0] + ' True:' + di_help[TANGO2CATS['di_VI98']][1]}],
        'di_VI99': [[DevBoolean, SCALAR, READ],
                    {'description': 'False:' + di_help[TANGO2CATS['di_VI99']][0] + ' True:' + di_help[TANGO2CATS['di_VI99']][1]}],

        # DO PARAMS pycats.do_params
        'do_ToolChanger': [[DevBoolean, SCALAR, READ],
                           {'description': 'False:' + do_help[TANGO2CATS['do_ToolChanger']][0] + ' True:' + do_help[TANGO2CATS['do_ToolChanger']][1]}],
        'do_ToolOpenClose': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + do_help[TANGO2CATS['do_ToolOpenClose']][0] + ' True:' + do_help[TANGO2CATS['do_ToolOpenClose']][1]}],
        'do_FastOutput': [[DevBoolean, SCALAR, READ],
                          {'description': 'False:' + do_help[TANGO2CATS['do_FastOutput']][0] + ' True:' + do_help[TANGO2CATS['do_FastOutput']][1]}],
        'do_PRO1_MON': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO1_MON']][0] + ' True:' + do_help[TANGO2CATS['do_PRO1_MON']][1]}],
        'do_PRO2_COL': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO2_COL']][0] + ' True:' + do_help[TANGO2CATS['do_PRO2_COL']][1]}],
        'do_PRO3_LNW': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO3_LNW']][0] + ' True:' + do_help[TANGO2CATS['do_PRO3_LNW']][1]}],
        'do_PRO4_LNA': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO4_LNA']][0] + ' True:' + do_help[TANGO2CATS['do_PRO4_LNA']][1]}],
        'do_GreenLight': [[DevBoolean, SCALAR, READ],
                          {'description': 'False:' + do_help[TANGO2CATS['do_GreenLight']][0] + ' True:' + do_help[TANGO2CATS['do_GreenLight']][1]}],
        'do_PilzRelayReset': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_PilzRelayReset']][0] + ' True:' + do_help[TANGO2CATS['do_PilzRelayReset']][1]}],
        'do_ServoCardOn': [[DevBoolean, SCALAR, READ],
                           {'description': 'False:' + do_help[TANGO2CATS['do_ServoCardOn']][0] + ' True:' + do_help[TANGO2CATS['do_ServoCardOn']][1]}],
        'do_ServoCardRotation': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + do_help[TANGO2CATS['do_ServoCardRotation']][0] + ' True:' + do_help[TANGO2CATS['do_ServoCardRotation']][1]}],
        'do_CryoValveLN2C': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + do_help[TANGO2CATS['do_CryoValveLN2C']][0] + ' True:' + do_help[TANGO2CATS['do_CryoValveLN2C']][1]}],
        'do_CryoValveLN2E': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + do_help[TANGO2CATS['do_CryoValveLN2E']][0] + ' True:' + do_help[TANGO2CATS['do_CryoValveLN2E']][1]}],
        'do_CryoValveGN2E': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + do_help[TANGO2CATS['do_CryoValveGN2E']][0] + ' True:' + do_help[TANGO2CATS['do_CryoValveGN2E']][1]}],
        'do_HeaterOnOff': [[DevBoolean, SCALAR, READ],
                           {'description': 'False:' + do_help[TANGO2CATS['do_HeaterOnOff']][0] + ' True:' + do_help[TANGO2CATS['do_HeaterOnOff']][1]}],
        'do_OpenCloseLid11': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid11']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid11']][1]}],
        'do_OpenCloseLid12': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid12']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid12']][1]}],
        'do_OpenCloseLid21': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid21']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid21']][1]}],
        'do_OpenCloseLid22': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid22']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid22']][1]}],
        'do_OpenCloseLid31': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid31']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid31']][1]}],
        'do_OpenCloseLid32': [[DevBoolean, SCALAR, READ],
                              {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid32']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid32']][1]}],
        'do_RequestDew1PosBit1': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew1PosBit1']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew1PosBit1']][1]}],
        'do_RequestDew1PosBit2': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew1PosBit2']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew1PosBit2']][1]}],
        'do_RequestDew1PosBit3': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew1PosBit3']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew1PosBit3']][1]}],
        'do_RequestDew1PosBit4': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew1PosBit4']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew1PosBit4']][1]}],
        'do_OpenLid': [[DevBoolean, SCALAR, READ],
                       {'description': 'False:' + do_help[TANGO2CATS['do_OpenLid']][0] + ' True:' + do_help[TANGO2CATS['do_OpenLid']][1]}],
        'do_CloseLid': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_CloseLid']][0] + ' True:' + do_help[TANGO2CATS['do_CloseLid']][1]}],
        'do_OpenNewLid': [[DevBoolean, SCALAR, READ],
                          {'description': 'False:' + do_help[TANGO2CATS['do_OpenNewLid']][0] + ' True:' + do_help[TANGO2CATS['do_OpenNewLid']][1]}],
        'do_CloseNewLid': [[DevBoolean, SCALAR, READ],
                           {'description': 'False:' + do_help[TANGO2CATS['do_CloseNewLid']][0] + ' True:' + do_help[TANGO2CATS['do_CloseNewLid']][1]}],
        'do_BarcodeReader': [[DevBoolean, SCALAR, READ],
                             {'description': 'False:' + do_help[TANGO2CATS['do_BarcodeReader']][0] + ' True:' + do_help[TANGO2CATS['do_BarcodeReader']][1]}],
        'do_CloseAllLids': [[DevBoolean, SCALAR, READ],
                            {'description': 'False:' + do_help[TANGO2CATS['do_CloseAllLids']][0] + ' True:' + do_help[TANGO2CATS['do_CloseAllLids']][1]}],
        'do_PRO5_IDL': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO5_IDL']][0] + ' True:' + do_help[TANGO2CATS['do_PRO5_IDL']][1]}],
        'do_PRO6_RAH': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO6_RAH']][0] + ' True:' + do_help[TANGO2CATS['do_PRO6_RAH']][1]}],
        'do_PRO7_RI1': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO7_RI1']][0] + ' True:' + do_help[TANGO2CATS['do_PRO7_RI1']][1]}],
        'do_PRO8_RI2': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO8_RI2']][0] + ' True:' + do_help[TANGO2CATS['do_PRO8_RI2']][1]}],
        'do_PRO9_LIO': [[DevBoolean, SCALAR, READ],
                        {'description': 'False:' + do_help[TANGO2CATS['do_PRO9_LIO']][0] + ' True:' + do_help[TANGO2CATS['do_PRO9_LIO']][1]}],
        'do_PRO10': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO10']][0] + ' True:' + do_help[TANGO2CATS['do_PRO10']][1]}],
        'do_PRO11': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO11']][0] + ' True:' + do_help[TANGO2CATS['do_PRO11']][1]}],
        'do_PRO12': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO11']][0] + ' True:' + do_help[TANGO2CATS['do_PRO12']][1]}],
        'do_RequestDew2PosBit1': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew2PosBit1']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew2PosBit1']][1]}],
        'do_RequestDew2PosBit2': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew2PosBit2']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew2PosBit2']][1]}],
        'do_RequestDew2PosBit3': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew2PosBit3']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew2PosBit3']][1]}],
        'do_RequestDew2PosBit4': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_RequestDew2PosBit4']][0] + ' True:' + do_help[TANGO2CATS['do_RequestDew2PosBit4']][1]}],
        'do_CryoValveLN2CDew2': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + do_help[TANGO2CATS['do_CryoValveLN2CDew2']][0] + ' True:' + do_help[TANGO2CATS['do_CryoValveLN2CDew2']][1]}],
        'do_CryoValveLN2EDew2': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + do_help[TANGO2CATS['do_CryoValveLN2EDew2']][0] + ' True:' + do_help[TANGO2CATS['do_CryoValveLN2EDew2']][1]}],
        'do_CryoVavleGN2EDew2': [[DevBoolean, SCALAR, READ],
                                 {'description': 'False:' + do_help[TANGO2CATS['do_CryoVavleGN2EDew2']][0] + ' True:' + do_help[TANGO2CATS['do_CryoVavleGN2EDew2']][1]}],
        'do_OpenCloseLid31Dew2': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid31Dew2']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid31Dew2']][1]}],
        'do_OpenCloseLid32Dew2': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid32Dew2']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid32Dew2']][1]}],
        'do_OpenCloseLid41Dew2': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid41Dew2']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid41Dew2']][1]}],
        'do_OpenCloseLid42Dew2': [[DevBoolean, SCALAR, READ],
                                  {'description': 'False:' + do_help[TANGO2CATS['do_OpenCloseLid42Dew2']][0] + ' True:' + do_help[TANGO2CATS['do_OpenCloseLid42Dew2']][1]}],
        'do_PRO13': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO13']][0] + ' True:' + do_help[TANGO2CATS['do_PRO13']][1]}],
        'do_PRO14': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO14']][0] + ' True:' + do_help[TANGO2CATS['do_PRO14']][1]}],
        'do_PRO15': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO15']][0] + ' True:' + do_help[TANGO2CATS['do_PRO15']][1]}],
        'do_PRO16': [[DevBoolean, SCALAR, READ],
                     {'description': 'False:' + do_help[TANGO2CATS['do_PRO16']][0] + ' True:' + do_help[TANGO2CATS['do_PRO16']][1]}],
        'do_RotationDewNewPosWorking': [[DevBoolean, SCALAR, READ],
                                        {'description': 'False:' + do_help[TANGO2CATS['do_RotationDewNewPosWorking']][0] + ' True:' + do_help[TANGO2CATS['do_RotationDewNewPosWorking']][1]}],
        'do_RotationDewarPosCassLoading': [[DevBoolean, SCALAR, READ],
                                           {'description': 'False:' + do_help[TANGO2CATS['do_RotationDewarPosCassLoading']][0] + ' True:' + do_help[TANGO2CATS['do_RotationDewarPosCassLoading']][1]}],
        'do_RotationDewPosWorking': [[DevBoolean, SCALAR, READ],
                                     {'description': 'False:' + do_help[TANGO2CATS['do_RotationDewPosWorking']][0] + ' True:' + do_help[TANGO2CATS['do_RotationDewPosWorking']][1]}],

        # POSITION PARAMS pycats.position_params
        'Xpos': [[DevFloat, SCALAR, READ]],
        'Ypos': [[DevFloat, SCALAR, READ]],
        'Zpos': [[DevFloat, SCALAR, READ]],
        'RXpos': [[DevFloat, SCALAR, READ]],
        'RYpos': [[DevFloat, SCALAR, READ]],
        'RZpos': [[DevFloat, SCALAR, READ]],

        # MESSAGE
        'Message': [[DevString, SCALAR, READ]],

        # Convenience values
        'SampleOnDiff': [[DevBoolean, SCALAR, READ]],
        'Version': [[DevString, SCALAR, READ]]
    }

    cmd_list = {
        # 3.6.5.1 General commands
        'powerOn': [[DevVoid], [DevString], ],
        'powerOff': [[DevVoid], [DevString], ],
        'panic': [[DevVoid], [DevString], ],
        'abort': [[DevVoid], [DevString], ],
        'pause': [[DevVoid], [DevString], ],
        'reset': [[DevVoid], [DevString], ],
        'restart': [[DevVoid], [DevString], ],
        'backup': [[DevShort, 'usbport = 100:USB0/J202 101:USB1/J209'], [DevString], ],
        'restore': [[DevShort, 'usbport = 100:USB0/J202 101:USB1/J209'], [DevString], ],

        # 3.6.5.2 Trajectories commands
        'home': [[DevUShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper'], [DevString], ],
        'safe': [[DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper'], [DevString], ],
        'put': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [DevString], ],
        'put_bcrd': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [DevString], ],
        'get': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0\n2:X_CATS shift (um)\n3:Y_CATS shift (um)\n4:Z_CATS shift (um)'], [DevString], ],
        'getput': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [DevString], ],
        'getput_bcrd': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0\n5:X_CATS shift (um)\n6:Y_CATS shift (um)\n7:Z_CATS shift (um)'], [DevString], ],
        'barcode': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:new sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0'], [DevString], ],
        'back': [[DevVarStringArray, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0'], [DevString], ],
        'transfer': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:sample number\n3:new puck or lid number\n4:new sample number\n5:type = 0:Actor 1:UniPuck (only cryotong)\n6:toolcal=0'], [DevString], ],
        'pick': [[DevVarStringArray, 'StringArray:\n5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)'], [DevString], ],
        'getpuckpick': [[DevVarStringArray, 'StringArray:\n5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:X_CATS shift (um)\n5:Y_CATS shift (um)\n6:Z_CATS shift (um)'], [DevString], ],
        'soak': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number'], [DevString], ],
        'dry': [[DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper'], [DevString], ],
        'dryhome': [[DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper'], [DevString], ],
        'gotodif': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number\n2:sample number\n3:type = 0:Actor 1:UniPuck (only cryotong)\n4:toolcal=0'], [DevString], ],
        'rd_position': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:puck or lid number'], [DevString], ],
        'rd_load': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:new puck or lid number'], [DevString], ],
        'puckdetect': [[DevVarStringArray, 'StringArray:\n0:puck or lid number\n1:toolcal=0'], [DevString], ],
        'recover': [[DevUShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper'], [DevString], ],
        'setondiff': [[DevVarStringArray, 'StringArray:\n0:puck or lid number\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)'], [DevString], ],
        'settool': [[DevVarStringArray, 'StringArray:\n0:puck or lid number\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)'], [DevString], ],
        'settool2': [[DevVarStringArray, 'StringArray:\n0:puck or lid number\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)'], [DevString], ],
        'put_HT': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)\n3:toolcal=0\n4:X_CATS shift (um)\n5:Y_CATS shift (um)\n6:Z_CATS shift (um)'], [DevString], ],
        'get_HT': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:toolcal=0\n2:X_CATS shift (um)\n3:Y_CATS shift (um)\n4:Z_CATS shift (um)'], [DevString], ],
        'getput_HT': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection\n1:sample number\n2:type = 0:Actor 1:UniPuck (only cryotong)\n3:toolcal=0\n4:X_CATS shift (um)\n5:Y_CATS shift (um)\n6:Z_CATS shift (um)'], [DevString], ],
        'recoverFailure': [[DevVoid], [DevString], ],

        # 3.6.5.3 Crystallization plate commands
        'putplate': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:plate number\n2:well number\n3:type = No info in docs\n4:toolcal=0'], [DevString], ],
        'getplate': [[DevShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\\n1:drop=0\n2:toolcal=0'], [DevString], ],
        'getputplate': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:plate number\n2:well number\n3:type = No info in docs\n4:drop=0\n5:toolcal=0'], [DevString], ],
        'goto_well': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:plate number\n2:well number\n3:toolcal=0'], [DevString], ],
        'adjust': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0\n2:X_CATS shift (um)\n3:Y_CATS shift (um)'], [DevString], ],
        'focus': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0\n2:Z_CATS shift (um)'], [DevString], ],
        'expose': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0\n2:angle (deg)\n3:# oscillations\n4:expose time\n5:step:'], [DevString], ],
        'collect': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0\n2:angle (deg)\n3:# oscillations\n4:expose time\n5:step\n6:final angle'], [DevString], ],
        'setplateangle': [[DevVarStringArray, 'StringArray:\n0:tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper\n1:toolcal=0\n2:angle (deg)'], [DevString], ],

        # 3.6.5.4 Virtual Inputs
        'vdi9xon': [[DevShort, 'input = 90..91'], [DevString], ],
        'vdi9xoff': [[DevShort, 'input = 90..91'], [DevString], ],

        # 3.6.5.5 Commands for LN2 controller
        'regulon': [[DevVoid], [DevString], ],
        'reguloff': [[DevVoid], [DevString], ],
        'warmon': [[DevVoid], [DevString], ],
        'warmoff': [[DevVoid], [DevString], ],
        'regulon1': [[DevVoid], [DevString], ],
        'reguloff1': [[DevVoid], [DevString], ],
        'regulon2': [[DevVoid], [DevString], ],
        'reguloff2': [[DevVoid], [DevString], ],

        # 3.6.5.6 Maintenance commands
        'openlid1': [[DevVoid], [DevString], ],
        'closelid1': [[DevVoid], [DevString], ],
        'openlid2': [[DevVoid], [DevString], ],
        'closelid2': [[DevVoid], [DevString], ],
        'openlid3': [[DevVoid], [DevString], ],
        'closelid3': [[DevVoid], [DevString], ],
        'openlid4': [[DevVoid], [DevString], ],
        'closelid4': [[DevVoid], [DevString], ],
        'opentool': [[DevVoid], [DevString], ],
        'closetool': [[DevVoid], [DevString], ],
        'opentool2': [[DevVoid], [DevString], ],
        'closetool2': [[DevVoid], [DevString], ],
        'magneton': [[DevVoid], [DevString], ],
        'magnetoff': [[DevVoid], [DevString], ],
        'heateron': [[DevVoid], [DevString], ],
        'heateroff': [[DevVoid], [DevString], ],
        'initdew1': [[DevVoid], [DevString], ],
        'initdew2': [[DevVoid], [DevString], ],
        'onestaticdw': [[DevVoid], [DevString], ],
        'tworotatingdw': [[DevVoid], [DevString], ],
        'openlid': [[DevVoid], [DevString], ],
        'closelid': [[DevVoid], [DevString], ],
        'clearbcrd': [[DevVoid], [DevString], ],
        'remotespeedon': [[DevVoid], [DevString], ],
        'remotespeedoff': [[DevVoid], [DevString], ],
        'speedup': [[DevVoid], [DevString], ],
        'speeddown': [[DevVoid], [DevString], ],
        'clear_memory': [[DevVoid], [DevString], ],
        'reset_parameters': [[DevVoid], [DevString], ],
        'resetmotion': [[DevVoid], [DevString], ],
        'cap_on_lid': [[DevUShort, 'tool = 6:Soaking cap'], [DevString], ],
        'cap_off_lid': [[DevUShort, 'tool = 6:Soaking cap'], [DevString], ],
        'toolcalibration': [[DevUShort, 'tool = 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates 4:Puck Detection 5:Double Gripper'], [DevString], ],

        # 3.6.5.7 Status commands
        'mon_state': [[DevVoid], [DevString], ],
        'mon_di': [[DevVoid], [DevString], ],
        'mon_do': [[DevVoid], [DevString], ],
        'mon_position': [[DevVoid], [DevString], ],
        'mon_message': [[DevVoid], [DevString], ],
        'mon_config': [[DevVoid], [DevString], ],

        # BACKDOOR FOR SOFTWARE UPGRADES OR ANYTHING NEEDED... ;-D
        'send_op_cmd': [[DevString], [DevString], ],
        'send_mon_cmd': [[DevString], [DevString], ],

    }

    def __init__(self, name):
        DeviceClass.__init__(self, name)
        self.set_type(name)
