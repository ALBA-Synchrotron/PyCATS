import time
import logging
from tango import (Device_4Impl, DeviceClass, DevState, DevVoid, DevULong,
                   DevUShort, DevFloat, DevBoolean, DevString, DevShort,
                   DevVarStringArray, ArgType, READ, SCALAR, SPECTRUM)
from .utils import CATS2TANGO, TANGO2CATS, ISARA22TANGO, TANGO2ISARA2
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

        self.logger.info('%s state dictionary updates every %s ms' % (str(klass), self.update_freq_ms))
        self.logger.info('Ready to accept requests.')

        self.TANGO2ROBOT = TANGO2CATS
        self.ROBOT2TANGO = CATS2TANGO

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
                    'Exception when getting status from robot server:\n%s' %
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
                'Connected to the robot system.')
        except Exception as e:
            self.notify_new_state(
                DevState.ALARM,
                'Exception connecting to the robot system:\n' + str(e))

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
                #print("UPDATING",catsk,"value",new_value)
                attr_name = self.ROBOT2TANGO[catsk]
                #print("  TANGO ATTRIBUTE IS",attr_name)
                self.push_change_event(attr_name, new_value)

        new_status = 'Powered = %s\n' % \
                     self.status_dict[self.TANGO2ROBOT['Powered']]
        new_status += 'Tool = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['Tool']]
        new_status += 'Path = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['Path']]
        new_status += 'PathRunning = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['PathRunning']]
        new_status += 'PathSafe = %s\n' % \
                      self.is_path_safe()

        robot_model = self.cs8connection.get_model()

        if robot_model == "CATS":
            new_status += 'LidSampleOnTool= %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['LidSampleOnTool']]
        elif robot_model == "ISARA":
            new_status += 'PuckNumberOnTool = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['PuckNumberOnTool']]
        elif robot_model == "ISARA2":
            new_status += 'PuckNumberOnTool = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['NumPuckOnTool']]
        new_status += 'NumSampleOnTool = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['NumSampleOnTool']]

        if robot_model == "ISARA":
            new_status += 'PuckNumberOnTool2 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['PuckNumberOnTool2']]
            new_status += 'NumSampleOnTool2 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['NumSampleOnTool2']]
        elif robot_model == "ISARA2":
            new_status += 'PuckNumberOnTool2 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['NumPuckOnTool2']]
            new_status += 'NumSampleOnTool2 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['NumSampleOnTool2']]
            
        new_status += 'Barcode = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['Barcode']]

        if robot_model == "CATS":
            new_status += 'LidSampleOnDiff = %s\n' %\
                          self.status_dict[self.TANGO2ROBOT['LidSampleOnDiff']]
        elif robot_model == "ISARA":
            new_status += 'PuckNumberOnDiff = %s\n' %\
                          self.status_dict[self.TANGO2ROBOT['PuckSampleOnDiff']]
        elif robot_model == "ISARA2":
            new_status += 'PuckNumberOnDiff = %s\n' %\
                          self.status_dict[self.TANGO2ROBOT['NumPuckOnDiff']]

        new_status += 'NumSampleOnDiff = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['NumSampleOnDiff']]
        new_status += 'NumPlateOnTool = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['NumPlateOnTool']]

        if robot_model == "CATS":
            new_status += 'Well = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['Well']]

        new_status += 'LN2Regulating = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['LN2Regulating']]

        if robot_model == "CATS":
            new_status += 'LN2Warming = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['LN2Warming']]

        if robot_model in ("CATS", "ISARA"):
            new_status += 'AutoMode = %s\n' % \
                        self.status_dict[self.TANGO2ROBOT['AutoMode']]
            new_status += 'DefaultStatus = %s\n' % \
                        self.status_dict[self.TANGO2ROBOT['DefaultStatus']]
        elif robot_model == "ISARA2":
            new_status += 'RemoteMode = %s\n' % \
                        self.status_dict[self.TANGO2ROBOT['RemoteMode']]
            new_status += 'FaultStatus = %s\n' % \
                        self.status_dict[self.TANGO2ROBOT['FaultStatus']]

        new_status += 'SpeedRatio = %s\n' % \
                      self.status_dict[self.TANGO2ROBOT['SpeedRatio']]

        if robot_model == "CATS":
            new_status += 'PuckDetectionDewar1 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['PuckDetectionDewar1']]
            new_status += 'PuckDetectionDewar2 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['PuckDetectionDewar2']]
        if robot_model in ("CATS", "ISARA"):
            new_status += 'PositionNumberDewar1 = %s\n' % \
                        self.status_dict[self.TANGO2ROBOT['PositionNumberDewar1']]
        if robot_model == "CATS":
            new_status += 'PositionNumberDewar2 = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['PositionNumberDewar2']]

        if robot_model in ("ISARA", "ISARA2"):
            new_status += 'CurrentNumberOfSoaking = %s\n' % \
                          self.status_dict[self.TANGO2ROBOT['CurrentNumberOfSoaking']]

        if new_status_dict[self.TANGO2ROBOT['Path']] != '':
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
        self.status_dict[self.TANGO2ROBOT['Powered']])

    def read_AutoMode(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['AutoMode']])

    def read_DefaultStatus(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['DefaultStatus']])

    def read_Tool(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Tool']])

    def read_Path(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Path']])

    def read_CatsModel(self, attr): attr.set_value(
        self.cs8connection.get_model())

    def read_NbCassettes(self, attr): attr.set_value(
        self.cs8connection.get_number_pucks())

    def read_CassettePresence(self, attr): attr.set_value(
        self.cs8connection.get_puck_presence())

    def read_CassetteType(self, attr): attr.set_value(
        self.cs8connection.get_puck_types())

    def read_LidSampleOnTool(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LidSampleOnTool']])

    def read_NumSampleOnTool(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumSampleOnTool']])

    def read_LidSampleOnDiff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LidSampleOnDiff']])

    def read_NumSampleOnDiff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumSampleOnDiff']])

    def read_NumPlateOnTool(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumPlateOnTool']])

    def read_Well(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Well']])

    def read_Barcode(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Barcode']])

    def read_PathRunning(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PathRunning']])

    def read_PathSafe(self, attr): attr.set_value(
        self.cs8connection.is_path_safe())

    def read_RecoveryNeeded(self, attr): attr.set_value(
        self.cs8connection.is_recovery_needed())

    def read_LastCommandSent(self, attr): attr.set_value(
        self.cs8connection.get_last_command_sent())

    def read_LN2Regulating(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LN2Regulating']])

    def read_LN2Warming(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LN2Warming']])

    def read_SpeedRatio(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['SpeedRatio']])

    def read_PuckDetectionDewar1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PuckDetectionDewar1']])

    def read_PuckDetectionDewar2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PuckDetectionDewar2']])

    def read_PositionNumberDewar1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PositionNumberDewar1']])

    def read_PositionNumberDewar2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PositionNumberDewar2']])

    def read_PuckNumberInTool2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PuckNumberInTool2']])

    def read_SampleNumberInTool2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['SampleNumberInTool2']])

    def read_CurrentNumberOfSoaking(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['CurrentNumberOfSoaking']])

    def read_PuckTypeLid1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PuckTypeLid1']])

    def read_PuckTypeLid2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PuckTypeLid2']])

    def read_PuckTypeLid3(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PuckTypeLid3']])

    # DI PARAMS pycats.di_params
    def read_di_CryoOK(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CryoOK']])

    def read_di_EStopAirpresOK(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_EStopAirpresOK']])

    def read_di_CollisonSensorOK(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CollisonSensorOK']])

    def read_di_CryoHighLevelAlarm(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CryoHighLevelAlarm']])

    def read_di_CryoHighLevel(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CryoHighLevel']])

    def read_di_CryoLowLevel(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CryoLowLevel']])

    def read_di_CryoLowLevelAlarm(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CryoLowLevelAlarm']])

    def read_di_CryoLiquidDetection(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_CryoLiquidDetection']])

    def read_di_PRI1_GFM(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_GFM']])

    def read_di_PRI2_API(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_API']])

    def read_di_PRI3_APL(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_APL']])

    def read_di_PRI4_SOM(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_SOM']])

    def read_di_PRI_GFM(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_GFM']])

    def read_di_PRI_API(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_API']])

    def read_di_PRI_APL(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_APL']])

    def read_di_PRI_SOM(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI_SOM']])

    def read_di_DiffPlateMode(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_DiffPlateMode']])

    def read_di_PlateOnDiff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PlateOnDiff']])

    def read_di_Cassette1Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette1Presence']])

    def read_di_Cassette2Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette2Presence']])

    def read_di_Cassette3Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette3Presence']])

    def read_di_Cassette4Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette4Presence']])

    def read_di_Cassette5Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette5Presence']])

    def read_di_Cassette6Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette6Presence']])

    def read_di_Cassette7Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette7Presence']])

    def read_di_Cassette8Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette8Presence']])

    def read_di_Cassette9Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Cassette9Presence']])

    def read_di_Lid1Open(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Lid1Open']])

    def read_di_Lid2Open(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Lid2Open']])

    def read_di_Lid3Open(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Lid3Open']])

    def read_di_ToolOpen(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ToolOpen']])

    def read_di_ToolClosed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ToolClosed']])

    def read_di_LimSW1RotGripAxis(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_LimSW1RotGripAxis']])

    def read_di_LimSW2RotGripAxis(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_LimSW2RotGripAxis']])

    def read_di_ModbusPLCLifeBit(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ModbusPLCLifeBit']])

    def read_di_LifeBitFromPLC(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_LifeBitFromPLC']])

    def read_di_ActiveLidOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ActiveLidOpened']])

    def read_di_NewActiveLidOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_NewActiveLidOpened']])

    def read_di_ToolChangerOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ToolChangerOpened']])

    def read_di_ActiveCassettePresence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ActiveCassettePresence']])

    def read_di_NewActiveCassettePresence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_NewActiveCassettePresence']])

    def read_di_AllLidsClosed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_AllLidsClosed']])

    def read_di_PRI5(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI5']])

    def read_di_PRI6(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI6']])

    def read_di_PRI7(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI7']])

    def read_di_PRI8(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI8']])

    def read_di_PRI9(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI9']])

    def read_di_PRI10(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI10']])

    def read_di_PRI11(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI11']])

    def read_di_PRI12(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_PRI12']])

    def read_di_VI90(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI90']])

    def read_di_VI91(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI91']])

    def read_di_VI92(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI92']])

    def read_di_VI93(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI93']])

    def read_di_VI94(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI94']])

    def read_di_VI95(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI95']])

    def read_di_VI96(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI96']])

    def read_di_VI97(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI97']])

    def read_di_VI98(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI98']])

    def read_di_VI99(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_VI99']])

    # DO PARAMS pycats.do_params
    def read_do_ToolChanger(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ToolChanger']])

    def read_do_ToolOpenClose(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ToolOpenClose']])

    def read_do_FastOutput(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_FastOutput']])

    def read_do_PRO1_MON(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO1_MON']])

    def read_do_PRO2_COL(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO2_COL']])

    def read_do_PRO3_LNW(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO3_LNW']])

    def read_do_PRO4_LNA(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO4_LNA']])

    def read_do_GreenLight(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_GreenLight']])

    def read_do_PilzRelayReset(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PilzRelayReset']])

    def read_do_ServoCardOn(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ServoCardOn']])

    def read_do_ServoCardRotation(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ServoCardRotation']])

    def read_do_CryoValveLN2C(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CryoValveLN2C']])

    def read_do_CryoValveLN2E(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CryoValveLN2E']])

    def read_do_CryoValveGN2E(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CryoValveGN2E']])

    def read_do_HeaterOnOff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_HeaterOnOff']])

    def read_do_OpenCloseLid11(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid11']])

    def read_do_OpenCloseLid12(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid12']])

    def read_do_OpenCloseLid21(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid21']])

    def read_do_OpenCloseLid22(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid22']])

    def read_do_OpenCloseLid31(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid31']])

    def read_do_OpenCloseLid32(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid32']])

    def read_do_RequestDew1PosBit1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew1PosBit1']])

    def read_do_RequestDew1PosBit2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew1PosBit2']])

    def read_do_RequestDew1PosBit3(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew1PosBit3']])

    def read_do_RequestDew1PosBit4(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew1PosBit4']])

    def read_do_OpenLid(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenLid']])

    def read_do_CloseLid(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseLid']])

    def read_do_OpenNewLid(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenNewLid']])

    def read_do_CloseNewLid(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseNewLid']])

    def read_do_BarcodeReader(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_BarcodeReader']])

    def read_do_CloseAllLids(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseAllLids']])

    def read_do_PRO5_IDL(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO5_IDL']])

    def read_do_PRO6_RAH(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO6_RAH']])

    def read_do_PRO7_RI1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO7_RI1']])

    def read_do_PRO8_RI2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO8_RI2']])

    def read_do_PRO9_LIO(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO9_LIO']])

    def read_do_PRO10(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO10']])

    def read_do_PRO11(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO11']])

    def read_do_PRO12(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO12']])

    def read_do_RequestDew2PosBit1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew2PosBit1']])

    def read_do_RequestDew2PosBit2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew2PosBit2']])

    def read_do_RequestDew2PosBit3(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew2PosBit3']])

    def read_do_RequestDew2PosBit4(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RequestDew2PosBit4']])

    def read_do_CryoValveLN2CDew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CryoValveLN2CDew2']])

    def read_do_CryoValveLN2EDew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CryoValveLN2EDew2']])

    def read_do_CryoVavleGN2EDew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CryoVavleGN2EDew2']])

    def read_do_OpenCloseLid31Dew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid31Dew2']])

    def read_do_OpenCloseLid32Dew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid32Dew2']])

    def read_do_OpenCloseLid41Dew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid41Dew2']])

    def read_do_OpenCloseLid42Dew2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenCloseLid42Dew2']])

    def read_do_PRO13(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO13']])

    def read_do_PRO14(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO14']])

    def read_do_PRO15(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO15']])

    def read_do_PRO16(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO16']])

    def read_do_RotationDewNewPosWorking(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RotationDewNewPosWorking']])

    def read_do_RotationDewarPosCassLoading(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RotationDewarPosCassLoading']])

    def read_do_RotationDewPosWorking(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RotationDewPosWorking']])

    # POSITION PARAMS pycats.position_params
    def read_Xpos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Xpos']])

    def read_Ypos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Ypos']])

    def read_Zpos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Zpos']])

    def read_RXpos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['RXpos']])

    def read_RYpos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['RYpos']])

    def read_RZpos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['RZpos']])

    # MESSAGE
    def read_Message(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Message']])

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
        return self.cs8connection.settool2(puck_lid, sample, type)

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
        num_sample_on_diff = self.status_dict[self.TANGO2ROBOT['NumSampleOnDiff']]
        sample_on_magnet = self.status_dict[self.TANGO2ROBOT['di_PRI_SOM']]

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



class ISARA2(CATS):
    def __init__(self, klass, name):
        self.model = "isara2"
        CATS.__init__(self, klass, name)
        self.TANGO2ROBOT = TANGO2ISARA2
        self.ROBOT2TANGO = ISARA22TANGO

    def is_sample_on_diff(self):
        num_sample_on_diff = self.status_dict[self.TANGO2ROBOT['NumSampleOnDiff']]
        sample_on_magnet = self.status_dict[self.TANGO2ROBOT['do_PRI4_SOM']]
        return (num_sample_on_diff != -1) or sample_on_magnet

    #################################################################
    #                        READ ATTRIBUTES
    #################################################################

    # STATE PARAMS pycats.state_params_isara2

    def read_RemoteMode(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['RemoteMode']])

    def read_FaultStatus(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['FaultStatus']])

    def read_Position(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['Position']])

    def read_GripperJawAOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['GripperJawAOpened']])

    def read_GripperJawBOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['GripperJawBOpened']])

    def read_LidSampleOnTool(self, attr): attr.set_value(1)

    def read_NumPuckOnTool(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumPuckOnTool']])

    def read_NumSampleOnTool(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumSampleOnTool']])

    def read_NumPuckOnTool2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumPuckOnTool2']])

    def read_NumSampleOnTool2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumSampleOnTool2']])

    def read_LidSampleOnDiff(self, attr): attr.set_value(1)

    def read_NumPuckOnDiff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumPuckOnDiff']])

    def read_NumPlateOnDiff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['NumPlateOnDiff']])

    def read_PathRunning(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PathRunning']])

    def read_PathPaused(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PathPaused']])

    def read_LN2DewarLevel(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LN2DewarLevel']])

    def read_LN2MaxLevelSetpoint(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LN2MaxLevelSetpoint']])

    def read_LN2MinLevelSetpoint(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LN2MinLevelSetpoint']])

    def read_CameraAutoTrackEnabled(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['CameraAutoTrackEnabled']])

    def read_GripperDrying(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['GripperDrying']])

    def read_PhaseSepLN2Regulating(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PhaseSepLN2Regulating']])

    def read_PhaseSepLN2Regulating(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PhaseSepLN2Regulating']])

    def read_AlarmsWord(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['AlarmsWord']])

    def read_JointAxis1pos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['JointAxis1pos']])

    def read_JointAxis2pos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['JointAxis2pos']])

    def read_JointAxis3pos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['JointAxis3pos']])

    def read_JointAxis4pos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['JointAxis4pos']])

    def read_JointAxis5pos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['JointAxis5pos']])

    def read_JointAxis6pos(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['JointAxis6pos']])

    def read_RobotControllerMessage(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['RobotControllerMessage']])

    def read_CryoVisionMessage(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['CryoVisionMessage']])

    def read_CryoVisionFeedbackData(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['CryoVisionFeedbackData']])

    def read_IsExternalLightOff(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['IsExternalLightOff']])

    def read_IsHeatingCableOn(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['IsHeatingCableOn']])

    def read_DewarHighTemperature(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['DewarHighTemperature']])

    def read_DewarLowTemperature(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['DewarLowTemperature']])

    def read_PhaseSepLevelTemperature(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PhaseSepLevelTemperature']])

    def read_PhaseSepAlarmTemperature(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['PhaseSepAlarmTemperature']])

    def read_LastTeachResult(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['LastTeachResult']])

    # STATE PARAMS pycats.di_params_isara2

    def read_di_Standby(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Standby']])

    def read_di_Ready(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Ready']])

    def read_di_Running(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Running']])

    def read_di_Paused(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_Paused']])

    def read_di_NoFaultState(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_NoFaultState']])

    def read_di_DebugMode(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_DebugMode']])

    def read_di_WarningState(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_WarningState']])

    def read_di_ManualMode(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ManualMode']])

    def read_di_EStopTeachPendant(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_EStopTeachPendant']])

    def read_di_EStopWorkModeSel(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_EStopWorkModeSel']])

    def read_di_EStopA(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_EStopA']])

    def read_di_EStopB(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_EStopB']])

    def read_di_ShockSensor(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ShockSensor']])

    def read_di_DoorOpen(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_DoorOpen']])

    def read_di_InternalFault(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_InternalFault']])

    def read_di_ToolChangerOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ToolChangerOpened']])

    def read_di_GripperAOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_GripperAOpened']])

    def read_di_GripperAClosed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_GripperAClosed']])

    def read_di_GripperBOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_GripperBOpened']])

    def read_di_GripperBClosed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_GripperBClosed']])

    def read_di_BlowingAir(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_BlowingAir']])

    def read_di_SingleGripperOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_SingleGripperOpened']])

    def read_di_SingleGripperClosed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_SingleGripperClosed']])

    def read_di_ClassicGripperOpened(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ClassicGripperOpened']])

    def read_di_ClassicGripperClosed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ClassicGripperClosed']])

    def read_di_ArmOutOfDewar(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ArmOutOfDewar']])

    def read_di_ArmOutOfGonio(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ArmOutOfGonio']])

    def read_di_ArmInDewar(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ArmInDewar']])

    def read_di_ArmInGonio(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ArmInGonio']])

    def read_di_ArmInHomeDry(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_ArmInHomeDry']])

    def read_di_DeadManPressed(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_DeadManPressed']])

    def read_di_UnlockedArmBrake(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_UnlockedArmBrake']])

    def read_di_SafetyAckSent(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_SafetyAckSent']])

    def read_di_NetworkStarted(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_NetworkStarted']])

    def read_di_RestartNeeded(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['di_RestartNeeded']])

    # STATE PARAMS pycats.do_params_isara2
    def read_do_PowerOnReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PowerOnReq']])

    def read_do_FaultAckReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_FaultAckReq']])

    def read_do_SeqStopReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_SeqStopReq']])

    def read_do_SeqPauseReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_SeqPauseReq']])

    def read_do_SeqEndAck(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_SeqEndAck']])

    def read_do_ManualInpAck(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ManualInpAck']])

    def read_do_RoomTempDewar(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RoomTempDewar']])

    def read_do_ColdCondDewar(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ColdCondDewar']])

    def read_do_LidOpenedFdbk(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_LidOpenedFdbk']])

    def read_do_LidClosedFdbk(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_LidClosedFdbk']])

    def read_do_OpenGripperAReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenGripperAReq']])

    def read_do_CloseGripperAReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseGripperAReq']])

    def read_do_OpenGripperBReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenGripperBReq']])

    def read_do_CloseGripperBReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseGripperBReq']])

    def read_do_LN2RegFdbk(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_LN2RegFdbk']])

    def read_do_SetGonioMemReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_SetGonioMemReq']])

    def read_do_SetGripperAMemReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_SetGripperAMemReq']])

    def read_do_SetGripperBMemReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_SetGripperBMemReq']])

    def read_do_ClearMemReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ClearMemReq']])

    def read_do_ClearSeqParamReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ClearSeqParamReq']])

    def read_do_RobotMsgReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_RobotMsgReq']])

    def read_do_ResetProgMemReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_ResetProgMemReq']])

    def read_do_PRI4_SOM(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRI4_SOM']])

    def read_do_PRI11_MON(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRI11_MON']])

    def read_do_PRO2_IDL(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO2_IDL']])

    def read_do_PRO3_RAH(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO3_RAH']])

    def read_do_PRO4_RI1(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO4_RI1']])

    def read_do_PRO5_RI2(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO5_RI2']])

    def read_do_PRO6_RI3(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO6_RI3']])

    def read_do_PRO7_RI4(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_PRO7_RI4']])

    def read_do_Puck1Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck1Presence']])
    def read_do_Puck2Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck2Presence']])
    def read_do_Puck3Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck3Presence']])
    def read_do_Puck4Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck4Presence']])
    def read_do_Puck5Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck5Presence']])
    def read_do_Puck6Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck6Presence']])
    def read_do_Puck7Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck7Presence']])
    def read_do_Puck8Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck8Presence']])
    def read_do_Puck9Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck9Presence']])
    def read_do_Puck10Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck10Presence']])
    def read_do_Puck11Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck11Presence']])
    def read_do_Puck12Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck12Presence']])
    def read_do_Puck13Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck13Presence']])
    def read_do_Puck14Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck14Presence']])
    def read_do_Puck15Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck15Presence']])
    def read_do_Puck16Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck16Presence']])
    def read_do_Puck17Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck17Presence']])
    def read_do_Puck18Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck18Presence']])
    def read_do_Puck19Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck19Presence']])
    def read_do_Puck20Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck20Presence']])
    def read_do_Puck21Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck21Presence']])
    def read_do_Puck22Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck22Presence']])
    def read_do_Puck23Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck23Presence']])
    def read_do_Puck24Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck24Presence']])
    def read_do_Puck25Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck25Presence']])
    def read_do_Puck26Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck26Presence']])
    def read_do_Puck27Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck27Presence']])
    def read_do_Puck28Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck28Presence']])
    def read_do_Puck29Presence(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_Puck29Presence']])

    def read_do_OpenSingleGripperReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenSingleGripperReq']])

    def read_do_CloseSingleGripperReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseSingleGripperReq']])

    def read_do_OpenClassicGripperReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_OpenClassicGripperReq']])

    def read_do_CloseClassicGripperReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseClassicGripperReq']])

    def read_do_CloseClassGripObjDelReq(self, attr): attr.set_value(
        self.status_dict[self.TANGO2ROBOT['do_CloseClassGripObjDelReq']])

    def opentoolb(self): return self.cs8connection.opentool2()
    def closetoolb(self): return self.cs8connection.closetool2()

    def setautocloselidtimer(self, timer): return self.cs8connection.setautocloselidtimer(timer)

    def setspeed(self, speed_percent): return self.cs8connection.setspeed(speed_percent)

    def sethighln2(self, high_threshold): return self.cs8connection.sethighln2(high_threshold)
    def setlowln2(self, low_threshold): return self.cs8connection.setlowln2(low_threshold)

    def ps_regulon(self): return self.cs8connection.ps_regulon()
    def ps_reguloff(self): return self.cs8connection.ps_reguloff()

    def dc_regulon(self): return self.cs8connection.dc_regulon()
    def dc_reguloff(self): return self.cs8connection.dc_reguloff()

    def dc_sethighln2(self, high_threshold): return self.cs8connection.dc_sethighln2(high_threshold)
    def dc_setlowln2(self, low_threshold): return self.cs8connection.dc_setlowln2(low_threshold)

    def setmaxsoaktime(self, max_soak_time): return self.cs8connection.setmaxsoaktime(max_soak_time)

    def setmaxsoaknb(self, max_soak_nb): return self.cs8connection.setmaxsoaknb(max_soak_nb)

    def setgrippercoolingtimer(self, timer): return self.cs8connection.setgrippercoolingtimer(timer)

    def setautodrytimer(self, timer): return self.cs8connection.setautodrytimer(timer)

    # Trajectory commands
    def home(self, tool):
        return self.cs8connection.home(tool)

    def recover(self, tool):
        return self.cs8connection.recover(tool)

    def back(self, tool):
        return self.cs8connection.back(tool)

    def soak(self, tool):
        return self.cs8connection.soak(tool)

    def dry(self, tool):
        return self.cs8connection.dry(tool)

    def changetool(self, tool): raise NotImplementedError

    def toolcalibration(self, tool):
        return self.cs8connection.toolcalibration(tool)

    def barcode(self, argin):
        tool, puck, sample, type, dis_smp_det = argin
        raise NotImplementedError
        #return self.cs8connection.barcode(tool, puck, sample. type)

    def put(self, argin):
        tool, puck, sample, type, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def put_bcrd(self, argin):
        tool, puck, sample, type, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def get(self, argin):
        tool, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def get_bcrd(self, argin):
        tool, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def getput(self, argin):
        tool, puck, sample, type, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def getput_bcrd(self, argin):
        tool, puck, sample, type, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def pick(self, argin):
        tool, puck, sample, type, dis_smp_det = argin
        raise NotImplementedError

    def pick_bcrd(self, argin):
        tool, puck, sample, type, dis_smp_det = argin
        raise NotImplementedError

    def gotodif(self, argin):
        tool, puck_lid, sample, type, dis_smp_det = argin
        raise NotImplementedError

    def get_HT(self, argin):
        tool, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def put_HT(self, argin):
        tool, puck, sample, type, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def getput_HT(self, argin):
        tool, puck, sample, type, dis_smp_det, x_shift, y_shift, z_shift = argin
        raise NotImplementedError

    def back_HT(self, tool):
        raise NotImplementedError

    def putplate(self, argin):
        tool, plate = argin
        raise NotImplementedError

    def getplate(self, tool):
        raise NotImplementedError

    def platetodif(self, argin):
        tool, plate = argin
        raise NotImplementedError



class ISARA2Class(CATSClass):
    device_property_list = {
        'host': [DevString,
                 "Hostname of the ISARA2 system.",
                 []],
        'port_operate': [DevUShort,
                         "Socket's port to operate the ISARA2 system.",
                         [1000]],
        'port_monitor': [DevUShort,
                         "Socket's port to monitor the ISARA2 system.",
                         [10000]],
        'puck_types': [DevString,
                       "nb_pucks x puck_type (2=unipuck,1=spine,0=ignore).",
                       ["22222222222222222222222222222"]],
        'update_freq_ms': [DevUShort,
                           "Update time in ms for the ISARA2 status.",
                           [300]],
        'reconnection_timeout': [DevUShort,
                                 "Timeout in seconds to reconnect or stop the DS.",
                                 [30]],
        'reconnection_interval': [DevUShort,
                                  "Wait time in seconds between reconnection attempts",
                                  [5]]
    }

    attr_list = {
        'CatsModel': [[DevString, SCALAR, READ]],
        'NbCassettes': [[DevShort, SCALAR, READ]],
        'CassetteType': [[ArgType.DevShort, SPECTRUM, READ, 32]],

        # STATE PARAMS pycats.state_params_isara2
        'Powered': [[DevBoolean, SCALAR, READ]],
        'RemoteMode': [[DevBoolean, SCALAR, READ]],
        'FaultStatus': [[DevBoolean, SCALAR, READ]],
        'Tool': [[DevString, SCALAR, READ]],
        'Position': [[DevString, SCALAR, READ]],
        'Path': [[DevString, SCALAR, READ]],
        'GripperJawAOpened': [[DevBoolean, SCALAR, READ]],
        'GripperJawBOpened': [[DevBoolean, SCALAR, READ]],
        'LidSampleOnTool': [[DevShort, SCALAR, READ]],
        'NumPuckOnTool': [[DevShort, SCALAR, READ]],
        'NumSampleOnTool': [[DevShort, SCALAR, READ]],
        'NumPuckOnTool2': [[DevShort, SCALAR, READ]],
        'NumSampleOnTool2': [[DevShort, SCALAR, READ]],
        'LidSampleOnDiff': [[DevShort, SCALAR, READ]],
        'NumPuckOnDiff': [[DevShort, SCALAR, READ]],
        'NumSampleOnDiff': [[DevShort, SCALAR, READ]],
        'NumPlateOnTool': [[DevShort, SCALAR, READ]],
        'NumPlateOnDiff': [[DevShort, SCALAR, READ]],
        'Barcode': [[DevString, SCALAR, READ]],
        'PathRunning': [[DevBoolean, SCALAR, READ]],
        'PathPaused': [[DevBoolean, SCALAR, READ]],
        'SpeedRatio': [[DevFloat, SCALAR, READ]],
        'LN2Regulating': [[DevBoolean, SCALAR, READ]],
        'CurrentNumberOfSoaking': [[DevShort, SCALAR, READ]],
        'LN2DewarLevel': [[DevFloat, SCALAR, READ]],
        'LN2MaxLevelSetpoint': [[DevFloat, SCALAR, READ]],
        'LN2MinLevelSetpoint': [[DevFloat, SCALAR, READ]],
        'CameraAutoTrackEnabled': [[DevBoolean, SCALAR, READ]],
        'GripperDrying': [[DevBoolean, SCALAR, READ]],
        'PhaseSepLN2Regulating': [[DevBoolean, SCALAR, READ]],
        'Message': [[DevString, SCALAR, READ]],
        'AlarmsWord': [[DevULong, SCALAR, READ]],
        'Xpos': [[DevFloat, SCALAR, READ]],
        'Ypos': [[DevFloat, SCALAR, READ]],
        'Zpos': [[DevFloat, SCALAR, READ]],
        'RXpos': [[DevFloat, SCALAR, READ]],
        'RYpos': [[DevFloat, SCALAR, READ]],
        'RZpos': [[DevFloat, SCALAR, READ]],
        'JointAxis1pos': [[DevFloat, SCALAR, READ]],
        'JointAxis2pos': [[DevFloat, SCALAR, READ]],
        'JointAxis3pos': [[DevFloat, SCALAR, READ]],
        'JointAxis4pos': [[DevFloat, SCALAR, READ]],
        'JointAxis5pos': [[DevFloat, SCALAR, READ]],
        'JointAxis6pos': [[DevFloat, SCALAR, READ]],
        'RobotControllerMessage': [[DevString, SCALAR, READ]],
        'CryoVisionMessage': [[DevString, SCALAR, READ]],
        'CryoVisionFeedbackData': [[DevString, SCALAR, READ]],
        'IsExternalLightOff': [[DevString, SCALAR, READ]],
        'IsHeatingCableOn': [[DevString, SCALAR, READ]],
        'DewarHighTemperature': [[DevFloat, SCALAR, READ]],
        'DewarLowTemperature': [[DevFloat, SCALAR, READ]],
        'PhaseSepLevelTemperature': [[DevFloat, SCALAR, READ]],
        'PhaseSepAlarmTemperature': [[DevFloat, SCALAR, READ]],
        'LastTeachResult': [[DevShort, SCALAR, READ]],

        # DI PARAMS pycats.di_params_isara2
        'di_Standby': [[DevBoolean, SCALAR, READ]],
        'di_Ready': [[DevBoolean, SCALAR, READ]],
        'di_Running': [[DevBoolean, SCALAR, READ]],
        'di_Paused': [[DevBoolean, SCALAR, READ]],
        'di_NoFaultState': [[DevBoolean, SCALAR, READ]],
        'di_DebugMode': [[DevBoolean, SCALAR, READ]],
        'di_WarningState': [[DevBoolean, SCALAR, READ]],
        'di_ManualMode': [[DevBoolean, SCALAR, READ]],
        'di_EStopTeachPendant': [[DevBoolean, SCALAR, READ]],
        'di_EStopWorkModeSel': [[DevBoolean, SCALAR, READ]],
        'di_EStopA': [[DevBoolean, SCALAR, READ]],
        'di_EStopB': [[DevBoolean, SCALAR, READ]],
        'di_ShockSensor': [[DevBoolean, SCALAR, READ]],
        'di_DoorOpen': [[DevBoolean, SCALAR, READ]],
        'di_InternalFault': [[DevBoolean, SCALAR, READ]],
        'di_ToolChangerOpened': [[DevBoolean, SCALAR, READ]],
        'di_GripperAOpened': [[DevBoolean, SCALAR, READ]],
        'di_GripperAClosed': [[DevBoolean, SCALAR, READ]],
        'di_GripperBOpened': [[DevBoolean, SCALAR, READ]],
        'di_GripperBClosed': [[DevBoolean, SCALAR, READ]],
        'di_BlowingAir': [[DevBoolean, SCALAR, READ]],
        'di_SingleGripperOpened': [[DevBoolean, SCALAR, READ]],
        'di_SingleGripperClosed': [[DevBoolean, SCALAR, READ]],
        'di_ClassicGripperOpened': [[DevBoolean, SCALAR, READ]],
        'di_ClassicGripperClosed': [[DevBoolean, SCALAR, READ]],
        'di_OpenLidReq': [[DevBoolean, SCALAR, READ]],
        'di_CloseLidReq': [[DevBoolean, SCALAR, READ]],
        'di_AirBlowerReq': [[DevBoolean, SCALAR, READ]],
        'di_AirSupplyReq': [[DevBoolean, SCALAR, READ]],
        'di_LN2RegulationReq': [[DevBoolean, SCALAR, READ]],
        'di_ArmOutOfDewar': [[DevBoolean, SCALAR, READ]],
        'di_ArmOutOfGonio': [[DevBoolean, SCALAR, READ]],
        'di_ArmInDewar': [[DevBoolean, SCALAR, READ]],
        'di_ArmInGonio': [[DevBoolean, SCALAR, READ]],
        'di_ArmInHomeDry': [[DevBoolean, SCALAR, READ]],
        'di_DeadManPressed': [[DevBoolean, SCALAR, READ]],
        'di_UnlockedArmBrake': [[DevBoolean, SCALAR, READ]],
        'di_SafetyAckSent': [[DevBoolean, SCALAR, READ]],
        'di_NetworkStarted': [[DevBoolean, SCALAR, READ]],
        'di_RestartNeeded': [[DevBoolean, SCALAR, READ]],

        # DO PARAMS pycats.do_params_isara2
        'do_PowerOnReq': [[DevBoolean, SCALAR, READ]],
        'do_FaultAckReq': [[DevBoolean, SCALAR, READ]],
        'do_SeqStopReq': [[DevBoolean, SCALAR, READ]],
        'do_SeqPauseReq': [[DevBoolean, SCALAR, READ]],
        'do_SeqEndAck': [[DevBoolean, SCALAR, READ]],
        'do_ManualInpAck': [[DevBoolean, SCALAR, READ]],
        'do_RoomTempDewar': [[DevBoolean, SCALAR, READ]],
        'do_ColdCondDewar': [[DevBoolean, SCALAR, READ]],
        'do_LidOpenedFdbk': [[DevBoolean, SCALAR, READ]],
        'do_LidClosedFdbk': [[DevBoolean, SCALAR, READ]],
        'do_OpenGripperAReq': [[DevBoolean, SCALAR, READ]],
        'do_CloseGripperAReq': [[DevBoolean, SCALAR, READ]],
        'do_OpenGripperBReq': [[DevBoolean, SCALAR, READ]],
        'do_CloseGripperBReq': [[DevBoolean, SCALAR, READ]],
        'do_LN2RegFdbk': [[DevBoolean, SCALAR, READ]],
        'do_SetGonioMemReq': [[DevBoolean, SCALAR, READ]],
        'do_SetGripperAMemReq': [[DevBoolean, SCALAR, READ]],
        'do_SetGripperBMemReq': [[DevBoolean, SCALAR, READ]],
        'do_ClearMemReq': [[DevBoolean, SCALAR, READ]],
        'do_ClearSeqParamReq': [[DevBoolean, SCALAR, READ]],
        'do_RobotMsgReq': [[DevBoolean, SCALAR, READ]],
        'do_ResetProgMemReq': [[DevBoolean, SCALAR, READ]],
        'do_PRI4_SOM': [[DevBoolean, SCALAR, READ]],
        'do_PRI11_MON': [[DevBoolean, SCALAR, READ]],
        'do_PRO2_IDL': [[DevBoolean, SCALAR, READ]],
        'do_PRO3_RAH': [[DevBoolean, SCALAR, READ]],
        'do_PRO4_RI1': [[DevBoolean, SCALAR, READ]],
        'do_PRO5_RI2': [[DevBoolean, SCALAR, READ]],
        'do_PRO6_RI3': [[DevBoolean, SCALAR, READ]],
        'do_PRO7_RI4': [[DevBoolean, SCALAR, READ]],
        'do_Puck1Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck2Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck3Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck4Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck5Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck6Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck7Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck8Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck9Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck10Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck11Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck12Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck13Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck14Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck15Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck16Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck17Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck18Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck19Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck20Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck21Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck22Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck23Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck24Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck25Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck26Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck27Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck28Presence': [[DevBoolean, SCALAR, READ]],
        'do_Puck29Presence': [[DevBoolean, SCALAR, READ]],
        'do_OpenSingleGripperReq': [[DevBoolean, SCALAR, READ]],
        'do_CloseSingleGripperReq': [[DevBoolean, SCALAR, READ]],
        'do_OpenClassicGripperReq': [[DevBoolean, SCALAR, READ]],
        'do_CloseClassicGripperReq': [[DevBoolean, SCALAR, READ]],
        'do_CloseClassGripObjDelReq': [[DevBoolean, SCALAR, READ]],

        # Convenience values
        'SampleOnDiff': [[DevBoolean, SCALAR, READ]],
        'Version': [[DevString, SCALAR, READ]],
        'CassettePresence': [[ArgType.DevShort, SPECTRUM, READ, 32]],
        'LastCommandSent': [[DevString, SCALAR, READ]],
        'RecoveryNeeded': [[DevBoolean, SCALAR, READ]],
    }

    cmd_list = {
        # General commands
        'powerOn': [[DevVoid], [DevString], ],
        'powerOff': [[DevVoid], [DevString], ],
        'panic': [[DevVoid], [DevString], ],
        'abort': [[DevVoid], [DevString], ],
        'pause': [[DevVoid], [DevString], ],
        'reset': [[DevVoid], [DevString], ],
        'restart': [[DevVoid], [DevString], ],
        'speedup': [[DevVoid], [DevString], ],
        'speeddown': [[DevVoid], [DevString], ],
        'setspeed': [[DevFloat], [DevString], ],

        # Tool commands
        'opentool': [[DevVoid], [DevString], ],
        'closetool': [[DevVoid], [DevString], ],
        'opentool2': [[DevVoid], [DevString], ],
        'closetool2': [[DevVoid], [DevString], ],
        'opentoolb': [[DevVoid], [DevString], ],
        'closetoolb': [[DevVoid], [DevString], ],
        
        # Magnet commands
        'magneton': [[DevVoid], [DevString], ],
        'magnetoff': [[DevVoid], [DevString], ],

        # Dewar commands
        'openlid': [[DevVoid], [DevString], ],
        'closelid': [[DevVoid], [DevString], ],
        'setautocloselidtimer': [[DevUShort], [DevString], ],

        # LN2 controller commands
        'regulon': [[DevVoid], [DevString], ],
        'reguloff': [[DevVoid], [DevString], ],
        'sethighln2': [[DevFloat], [DevString], ],
        'setlowln2': [[DevFloat], [DevString], ],
        'ps_regulon': [[DevVoid], [DevString], ],
        'ps_reguloff': [[DevVoid], [DevString], ],
        'dc_regulon': [[DevVoid], [DevString], ],
        'dc_reguloff': [[DevVoid], [DevString], ],
        'dc_sethighln2': [[DevFloat], [DevString], ],
        'dc_setlowln2': [[DevFloat], [DevString], ],

        # Heater commands
        'heateron': [[DevVoid], [DevString], ],
        'heateroff': [[DevVoid], [DevString], ],

        # Soak/dry/cool commands
        'setmaxsoaktime': [[DevUShort], [DevString], ],
        'setmaxsoaknb': [[DevUShort], [DevString], ],
        'setautodrytimer': [[DevUShort], [DevString], ],
        'setgrippercoolingtimer': [[DevUShort], [DevString], ],

        # Status commands
        'mon_state': [[DevVoid], [DevString], ],
        'mon_di': [[DevVoid], [DevString], ],
        'mon_do': [[DevVoid], [DevString], ],
        'mon_position': [[DevVoid], [DevString], ],
        'mon_message': [[DevVoid], [DevString], ],

        # Trajectory commands 0=tool changer 1=cryotong 2=single magnetic 3=double magnetic 4=minispine 5=rotating 6=plate 7=spare 8=laser teaching
        'home': [[DevUShort, 'tool'], [DevString], ],
        'recover': [[DevUShort, 'tool'], [DevString], ],
        'back': [[DevUShort, 'tool'], [DevString], ],
        'soak': [[DevUShort, 'tool'], [DevString], ],
        'dry': [[DevShort, 'tool'], [DevString], ],

        # Tool trajectory commands
        'changetool': [[DevUShort, 'tool'], [DevString], ],
        'toolcalibration': [[DevUShort, 'tool'], [DevString], ],

        # Sample trajectory commands
        'barcode': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection'], [DevString], ],
        'put': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection\n5:x_gonio shift (um)\n6:y_gonio shift (um)\n7:z_gonio shift (um)'], [DevString], ],
        'put_bcrd': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection\n5:x_gonio shift (um)\n6:y_gonio shift (um)\n7:z_gonio shift (um)'], [DevString], ],
        'get': [[DevVarStringArray, 'StringArray:\n0:tool\n1:x_gonio shift (um)\n2:y_gonio shift (um)\n3:z_gonio shift (um)'], [DevString], ],
        'get_bcrd': [[DevVarStringArray, 'StringArray:\n0:tool\n1:x_gonio shift (um)\n2:y_gonio shift (um)\n3:z_gonio shift (um)'], [DevString], ],
        'getput': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection\n5:x_gonio shift (um)\n6:y_gonio shift (um)\n7:z_gonio shift (um)'], [DevString], ],
        'getput_bcrd': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection\n5:x_gonio shift (um)\n6:y_gonio shift (um)\n7:z_gonio shift (um)'], [DevString], ],
        'pick': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection'], [DevString], ],
        'pick_bcrd': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection'], [DevString], ],
        'gotodif': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection'], [DevString], ],

        # Hot-puck trajectory commands
        'get_HT': [[DevVarStringArray, 'StringArray:\n0:tool\n1:x_gonio shift (um)\n2:y_gonio shift (um)\n3:z_gonio shift (um)'], [DevString], ],
        'put_HT': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection\n5:x_gonio shift (um)\n6:y_gonio shift (um)\n7:z_gonio shift (um)'], [DevString], ],
        'getput_HT': [[DevVarStringArray, 'StringArray:\n0:tool\n1:puck number\n2:sample number\n3:type = 0:Other 1:Hampton\n4:disable sample detection\n5:x_gonio shift (um)\n6:y_gonio shift (um)\n7:z_gonio shift (um)'], [DevString], ],
        'back_HT': [[DevUShort, 'tool'], [DevString], ],

        # Plate trajectory commands
        'putplate': [[DevVarStringArray, 'StringArray:\n0:tool\n1:plate number'], [DevString], ],
        'getplate': [[DevUShort, 'tool'], [DevString], ],
        'platetodif': [[DevVarStringArray, 'StringArray:\n0:tool\n1:plate number'], [DevString], ],

        # Sample commands
        'setondiff': [[DevVarStringArray, 'StringArray:\n0:puck number\n1:sample number\n2:type = 0:Other 1:Hampton'], [DevString], ],
        'settool': [[DevVarStringArray, 'StringArray:\n0:puck number\n1:sample number\n2:type = 0:Other 1:Hampton'], [DevString], ],

        # Cleanup commands
        'clearbcrd': [[DevVoid], [DevString], ],
        'clear_memory': [[DevVoid], [DevString], ],
    }
