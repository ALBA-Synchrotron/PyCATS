import socket
import struct
from threading import Lock

### CS8 CONSTANTS ###

# Improvements in version 5:
#
# 1) Trajectory commands args 8 and 9 are NOT SPARE any more
#    #8: plate dropping position
#    #9: tool calibration values
#
# 2) 3 new trajectory commands:
#    def rd_position(self, tool, lid):
#    def rd_load(tool, newlid):
#    def puckdetect(self, lid, toolcal):
#
# 3) 4 new LN2 controller commands:
#    def regulon1(self):
#    def reguloff1(self):
#    def regulon2(self):
#    def reguloff2(self):
#
# 4) 6 new Maintenance commands:
#    def openlid4(self):
#    def closelid4(self):
#    def initdew1(self):
#    def initdew2(self):
#    def onestaticdw(self):
#    def tworotatingdw(self):
#
# 5) 4 new State Params
#    #16: puck detection result on Dewar #1
#    #17: puck detection result on Dewar #2
#    #18: position number in Dewar #1
#    #19: position number in Dewar #2
#
# 6) do() answers now 99 signals (instead of 55) New signals:
#    'REQ_DEW1_POS_B1'
#    'REQ_DEW1_POS_B2'
#    'REQ_DEW1_POS_B3'
#    'REQ_DEW1_POS_B4'
#    'REQ_DEW2_POS_B1'
#    'REQ_DEW2_POS_B2'
#    'REQ_DEW2_POS_B3'
#    'REQ_DEW2_POS_B4'
#    'CRYO_VALVE_LN2_C_DEW2'
#    'CRYO_VALVE_LN2_E_DEW2'
#    'CRYO_VALVE_GN2_E_DEW2'
#    'OPEN_CLOSE_LID_3_1_DEW2'
#    'OPEN_CLOSE_LID_3_2_DEW2'
#    'OPEN_CLOSE_LID_4_1_DEW2'
#    'OPEN_CLOSE_LID_4_2_DEW2'
#    'PROCESS_OUTPUT_13'
#    'PROCESS_OUTPUT_14'
#    'PROCESS_OUTPUT_15'
#    'PROCESS_OUTPUT_16'
#    'ROT_DEW_NEW_POS_CTRL_ROBOT_WORKING'
#    'ROT_DEW_POS_CTRL_CASS_LOADING'
#    'ROT_DEW_POS_CTRL_ROBOT_WORKING'
#
# 7) NOT DOCUMENTED 3 NEW COMMANDS
#    def clear_memory(self):
#    def reset_parameters(self):
#    def resetmotion(self):


state_params = ['POWER_1_0', 'AUTO_MODE_STATUS_1_0', 'DEFAULT_STATUS_1_0', 'TOOL_NUM_OR_NAME', 'PATH_NAME', 'LID_NUM_SAMPLE_MOUNTED_ON_TOOL', 'NUM_SAMPLE_ON_TOOL', 'LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER', 'NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER', 'NUM_OF_PLATE_IN_TOOL', 'WELL_NUM', 'BARCODE_NUM', 'PATH_RUNNING_1_0', 'LN2_REGULATION_RUNNING_1_0', 'LN2_WARMING_RUNNING_1_0', 'ROBOT_SPEED_RATIO', 'PUCK_DET_RESULT_DEW1', 'PUCK_DET_RESULT_DEW2', 'POSITION_NUM_DEW1', 'POSITION_NUM_DEW2']

di_params = ['CRYOGEN_SENSORS_OK','ESTOP_AND_AIRPRES_OK','COLLISION_SENSOR_OK','CRYOGEN_HIGH_LEVEL_ALARM','CRYOGEN_HIGH_LEVEL','CRYOGEN_LOW_LEVEL','CRYOGEN_LOW_LEVEL_ALARM','CRYOGEN_LIQUID_DETECTION','PRI1_GFM','PRI2_API','PRI3_APL','PRI4_SOM','CASSETTE_1_PRESENCE','CASSETTE_2_PRESENCE','CASSETTE_3_PRESENCE','CASSETTE_4_PRESENCE','CASSETTE_5_PRESENCE','CASSETTE_6_PRESENCE','CASSETTE_7_PRESENCE','CASSETTE_8_PRESENCE','CASSETTE_9_PRESENCE','LID_1_OPENED','LID_2_OPENED','LID_3_OPENED','TOOL_OPENED','TOOL_CLOSED','LIMSW1_ROT_GRIP_AXIS','LIMSW2_ROT_GRIP_AXIS','MODBUS_PLC_LIFE_BIT','.','.','LIFE_BIT_COMING_FROM_PLC','ACTIVE_LID_OPENED','NEW_ACTIVE_LID_OPENED','TOOL_CHANGER_OPENED','ACTIVE_CASSETTE_PRESENCE','NEW_ACTIVE_CASSETTE_PRESENCE','ALL_LIDS_CLOSED','.','.','.','.','.','.','.','.','.','PROCESS_INPUT_5','PROCESS_INPUT_6','PROCESS_INPUT_7','PROCESS_INPUT_8','PROCESS_INPUT_9','PROCESS_INPUT_10','PROCESS_INPUT_11','PROCESS_INPUT_12','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','VIRTUAL_INPUT_90','VIRTUAL_INPUT_91','VIRTUAL_INPUT_92','VIRTUAL_INPUT_93','VIRTUAL_INPUT_94','VIRTUAL_INPUT_95','VIRTUAL_INPUT_96','VIRTUAL_INPUT_97','VIRTUAL_INPUT_98','VIRTUAL_INPUT_99']

do_params = ['TOOL_CHANGER','TOOL_OPEN_CLOSE','FAST_OUTPUT','.','PRO1_MON','PRO2_COL','PRO3_LNW','PRO4_LNA','GREEN_LIGHT','PILZ_RELAY_RESET','SERVO_CARD_ON','SERVO_CARD_ROTATION_+-','CRYOGEN_VALVE_LN2_C','CRYOGEN_VALVE_LN2_E','CRYOGEN_VALVE_GN2_E','HEATER_ON_OFF','OPEN_CLOSE_LID_1_1','OPEN_CLOSE_LID_1_2','OPEN_CLOSE_LID_2_1','OPEN_CLOSE_LID_2_2','OPEN_CLOSE_LID_3_1','OPEN_CLOSE_LID_3_2','.','.','.','REQ_DEW1_POS_B1','REQ_DEW1_POS_B2','REQ_DEW1_POS_B3','REQ_DEW1_POS_B4','.','.','.','OPEN_LID','CLOSE_LID','OPEN_NEW_LID','CLOSE_NEW_LID','BARCODE_READER_CONTROL','CLOSE_ALL_LIDS','.','.','.','.','.','.','.','.','.','PRO5_IDL','PRO6_RAH','PRO7_RI1','PRO8_RI2','PRO9_LIO','PROCESS_OUTPUT_10','PROCESS_OUTPUT_11','PROCESS_OUTPUT_12', '.','.','.','.','REQ_DEW2_POS_B1','REQ_DEW2_POS_B2','REQ_DEW2_POS_B3','REQ_DEW2_POS_B4','.','.','CRYO_VALVE_LN2_C_DEW2','CRYO_VALVE_LN2_E_DEW2','CRYO_VALVE_GN2_E_DEW2','.','OPEN_CLOSE_LID_3_1_DEW2','OPEN_CLOSE_LID_3_2_DEW2','OPEN_CLOSE_LID_4_1_DEW2','OPEN_CLOSE_LID_4_2_DEW2','PROCESS_OUTPUT_13','PROCESS_OUTPUT_14','PROCESS_OUTPUT_15','PROCESS_OUTPUT_16','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','.','ROT_DEW_NEW_POS_CTRL_ROBOT_WORKING','ROT_DEW_POS_CTRL_CASS_LOADING','ROT_DEW_POS_CTRL_ROBOT_WORKING']

             
position_params = ['X_POSITION_IN_MM','Y_POSITION_IN_MM','Z_POSITION_IN_MM','RX_POSITION_IN_MM','RY_POSITION_IN_MM','RZ_POSITION_IN_MM']

di_help = {
    '.':('NOT_USED','NOT_USED'),
    'CRYOGEN_SENSORS_OK':('SENSOR_FAILURE','SENSORS_OK'),
    'ESTOP_AND_AIRPRES_OK':('E-STOP_TRIGGERED_OR_PRESSURE_LOSS','NO_E-STOP_AND_PRESSURE_OK'),
    'COLLISION_SENSOR_OK':('COLLISION','NO_COLLISION'),
    'CRYOGEN_HIGH_LEVEL_ALARM':('HIGH_LEVEL_ALARM','NO_ALARM'),
    'CRYOGEN_HIGH_LEVEL':('HIGH_LEVEL_NOT_REACHED','HIGH_LEVEL_REACHED'),
    'CRYOGEN_LOW_LEVEL':('LOW_LEVEL_NOT_REACHED','LOW_LEVEL_REACHED'),
    'CRYOGEN_LOW_LEVEL_ALARM':('LOW_LEVEL_ALARM','NO_ALARM'),
    'CRYOGEN_LIQUID_DETECTION':('GASEOUS_PHASE','LIQUID_PHASE'),
    'PRI1_GFM':('The robot cannot move','The robot can move in area 0'),
    'PRI2_API':('Sample environment is not ready for put/get of pins','Sample environment is ready for put/get of pins'),
    'PRI3_APL':('Sample environment is not ready for put/get of plates','Sample environment is ready for put/get of plates'),
    'PRI4_SOM':('No sample detected on magnet','Sample detected on magnet'),
    'CASSETTE_1_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_2_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_3_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_4_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_5_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_6_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_7_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_8_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'CASSETTE_9_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'LID_1_OPENED':('LID_NOT_OPENED','LID_COMPLETELY_OPENED'),
    'LID_2_OPENED':('LID_NOT_OPENED','LID_COMPLETELY_OPENED'),
    'LID_3_OPENED':('LID_NOT_OPENED','LID_COMPLETELY_OPENED'),
    'TOOL_OPENED':('TOOL_NOT_COMPLETELY_OPENED','TOOL_COMPLETELY_OPENED'),
    'TOOL_CLOSED':('TOOL_NOT_COMPLETELY_CLOSED','TOOL_COMPLETELY_CLOSED'),
    'LIMSW1_ROT_GRIP_AXIS':('GRIPPER_IN_THE_DIFFRACTOMETER_ANGULAR_POSITION','GRIPPER_NOT_IN_THE_DIFFRACTOMETER_ANGULAR_POSITION'),
    'LIMSW2_ROT_GRIP_AXIS':('GRIPPER_IN_THE_DEWAR_ANGULAR_POSITION','GRIPPER_NOT_IN_THE_DEWAR_ANGULAR_POSITION'),
    'MODBUS_PLC_LIFE_BIT':('---','---'),
    'LIFE_BIT_COMING_FROM_PLC':('---','---'),
    'ACTIVE_LID_OPENED':('LID_NOT_OPENED','LID_COMPLETELY_OPENED'),
    'NEW_ACTIVE_LID_OPENED':('LID_NOT_OPENED','LID_COMPLETELY_OPENED'),
    'TOOL_CHANGER_OPENED':('TOOL_CHANGER_RELEASED','TOOL_CHANGER_ENGAGED'),
    'ACTIVE_CASSETTE_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'NEW_ACTIVE_CASSETTE_PRESENCE':('NO_CASSETTE','CASSETTE_IN_PLACE'),
    'ALL_LIDS_CLOSED':('LID(S)_COMPLETELY_CLOSED','ALL_LIDS_NOT_OPENED'),
    'PROCESS_INPUT_5':('---','---'),
    'PROCESS_INPUT_6':('---','---'),
    'PROCESS_INPUT_7':('---','---'),
    'PROCESS_INPUT_8':('---','---'),
    'PROCESS_INPUT_9':('---','---'),
    'PROCESS_INPUT_10':('---','---'),
    'PROCESS_INPUT_11':('---','---'),
    'PROCESS_INPUT_12':('---','---'),
    'VIRTUAL_INPUT_90':('---','---'),
    'VIRTUAL_INPUT_91':('---','---'),
    'VIRTUAL_INPUT_92':('---','---'),
    'VIRTUAL_INPUT_93':('---','---'),
    'VIRTUAL_INPUT_94':('---','---'),
    'VIRTUAL_INPUT_95':('---','---'),
    'VIRTUAL_INPUT_96':('---','---'),
    'VIRTUAL_INPUT_97':('---','---'),
    'VIRTUAL_INPUT_98':('---','---'),
    'VIRTUAL_INPUT_99':('---','---')
    }

do_help = {
    '.':('---','---'),
    'TOOL_CHANGER':('TOOL_GRIPPED','TOOL_RELEASED'),
    'TOOL_OPEN_CLOSE':('CLOSE_THE_TOOL','OPEN_THE_TOOL'),
    'FAST_OUTPUT':('CONTACT_OPENED','CONTACT_CLOSED'),
    'PRO1_MON':('Turn the smart magnet on','Turn the smart magnet off'),
    'PRO2_COL':('No collision','A collision has occurred'),
    'PRO3_LNW':('No liquid N2 warning has been triggered','Liquid N2 warning has been triggered'),
    'PRO4_LNA':('No liquid N2 alarm has been triggered','Liquid N2 alarm has been triggered'),
    'GREEN_LIGHT':('---','MODBUS_LINK_OK'),
    'PILZ_RELAY_RESET':('---','RESET_OF_THE_RELAY'),
    'SERVO_CARD_ON':('CARD_DISABLED','CARD_ON'),
    'SERVO_CARD_ROTATION_+-':('TOWARDS_THE_DIFFRACTOMETER_POSITION','TOWARDS_THE_DEWAR_POSITION'),
    'CRYOGEN_VALVE_LN2_C':('VALVE_CLOSED','VALVE_OPENED'),
    'CRYOGEN_VALVE_LN2_E':('VALVE_CLOSED','VALVE_OPENED'),
    'CRYOGEN_VALVE_GN2_E':('VALVE_CLOSED','VALVE_OPENED'),
    'HEATER_ON_OFF':('HEATER_OFF','HEATER_ON'),
    'OPEN_CLOSE_LID_1_1':('CLOSE_LID_1','OPEN_LID_1'),
    'OPEN_CLOSE_LID_1_2':('OPEN_LID_1','CLOSE_LID_1'),
    'OPEN_CLOSE_LID_2_1':('CLOSE_LID_2','OPEN_LID_2'),
    'OPEN_CLOSE_LID_2_2':('OPEN_LID_2','CLOSE_LID_2'),
    'OPEN_CLOSE_LID_3_1':('CLOSE_LID_3','OPEN_LID_3'),
    'OPEN_CLOSE_LID_3_2':('OPEN_LID_3','CLOSE_LID_3'),
    'REQ_DEW1_POS_B1':('---','---'),
    'REQ_DEW1_POS_B2':('---','---'),
    'REQ_DEW1_POS_B3':('---','---'),
    'REQ_DEW1_POS_B4':('---','---'),
    'OPEN_LID':('---','OPEN_ACTIVE_LID'),
    'CLOSE_LID':('---','CLOSE_ACTIVE_LID'),
    'OPEN_NEW_LID':('---','OPEN_NEW_ACTIVE_LID'),
    'CLOSE_NEW_LID':('---','CLOSE_NEW_ACTIVE_LID'),
    'BARCODE_READER_CONTROL':('---','ASK_FOR_A_BARCODE_READING'),
    'CLOSE_ALL_LIDS':('---','CLOSE_ALL_LIDS'),
    'PRO5_IDL':('The robot is executing a command','The robot is not executing any command'),
    'PRO6_RAH':('Robot arm is running a trajectory','Robot is at home position'),
    'PRO7_RI1':('Robot is not in area 1: (a) stop routine that checks RI2 and (b) enable motors','Robot is in area 1:  (a) start routine that checks RI2 and (b) disable motors'),
    'PRO8_RI2':('The robot is not in area 2. So, the cryostream nozzle is allowed  at position 1 (~5 mm from sample)','The robot is in area 2. So, the cryostream nozzle is allowed  at position 2 (~40? mm from sample)'),
    'PRO9_LIO':('No lid is open','Any lid is open'),
    'PROCESS_OUTPUT_10':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_11':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_12':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'REQ_DEW2_POS_B1':('---','---'),
    'REQ_DEW2_POS_B2':('---','---'),
    'REQ_DEW2_POS_B3':('---','---'),
    'REQ_DEW2_POS_B4':('---','---'),
    'CRYO_VALVE_LN2_C_DEW2':('VALVE_CLOSED','VALVE_OPENED'),
    'CRYO_VALVE_LN2_E_DEW2':('VALVE_CLOSED','VALVE_OPENED'),
    'CRYO_VALVE_GN2_E_DEW2':('VALVE_CLOSED','VALVE_OPENED'),
    'OPEN_CLOSE_LID_3_1_DEW2':('CLOSE_LID_3','OPEN_LID_3'),
    'OPEN_CLOSE_LID_3_2_DEW2':('OPEN_LID_3','CLOSE_LID_3'),
    'OPEN_CLOSE_LID_4_1_DEW2':('CLOSE_LID_4','OPEN_LID_4'),
    'OPEN_CLOSE_LID_4_2_DEW2':('OPEN_LID_4','CLOSE_LID_4'),
    'PROCESS_OUTPUT_13':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_14':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_15':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_16':('OPEN_THE_CONTACT','CLOSE_THE_CONTACT'),
    'ROT_DEW_NEW_POS_CTRL_ROBOT_WORKING':('---','Ask for a Dewar positioning on robot working lid'),
    'ROT_DEW_POS_CTRL_CASS_LOADING':('---','Ask for the positioning on cassettes loading lid'),
    'ROT_DEW_POS_CTRL_ROBOT_WORKING':('---','Ask for a Dewar positioning on robot working lid'),
     }

message_help = {
    'BackUp is running':('BackUp is running.','/'),
    'BackUp error':('BackUp error.','Make sure the USB Key is well plugged.'),
    'BackUp completed':('BackUp completed.','/'),
    'Restore is running':('Restore is running.','/'),
    'Restore error':('Restore error.','Make sure the USB Key is well plugged or BackUp is stored on it.'),
    'Restore completed':('Restore completed.','/'),
    'doors opened':('Door(s) is(are) opened.','Close the door(s) or switch to Manual Mode.'),
    'Manual brake control selected':('Manual brake button is not 0 position.','Turn the manual brake button to the 0 position.'),
    'emerency stop or air pressure fault':('One of emergency stops has been pressed or the compressed air pressure is too low.','Pull off the emergency stop or check the compressed air.'),
    'collision detection':('The robot hit something.','Unlock the arm brakes, move the robot manually and then re-engaged the shock detector.'),
    'Modbus communication fault':('Modbus communication fault.','Make sure that the Ethernet cable is well plugged on the CS8C controller and on the PLC (inside the electro-pneumatic racks). Make sure that the power of the CS8C controller and the PLC is on.'),
    'LOC menu not disabled':('Menu LOC is selected on the Teach Pendant.','Quit the LOC menu of the Teach Pendant.'),
    'Remote Mode requested':('Remote Mode is not selected.','Switch to Remorte Mode on the Teach Pendant.'),
    'Disable when path is running':('A trajectory command has been sent to system which is already processing a task.','Wait fo rthe end of the path or abort the path which is running.'),
    'X- collision':('The X- limit is reached in the frame World.','Modify the trajectory or readjust the limit.'),
    'X+ collision':('The X+ limit is reached in the frame World.','Modify the trajectory or readjust the limit.'),
    'Y- collision':('The Y- limit is reached in the frame World.','Modify the trajectory or readjust the limit.'),
    'Y+ collision':('The Y+ limit is reached in the frame World.','Modify the trajectory or readjust the limit.'),
    'Z- collision':('The Z- limit is reached in the frame World.','Modify the trajectory or readjust the limit.'),
    'Z+ collision':('The Z+ limit is reached in the frame World.','Modify the trajectory or readjust the limit.'),
    'Robot foot collision':('Collision with the foot of the robot arm.','Modify the trajectory.'),
    'low level alarm':('LN2 level in the Dewar is low.','Check the LN2 supply.'),
    'high level alarm':('LN2 level in the Dewar is too high.','Close the main valve of the LN2 supply and contact IRELEC support.'),
    'cryogenic incoherent signals':('LN2 low level is false and LN2 high level is true.','Check the pressure of the LN2 supply and control the LN2 sensors.'),
    'cryogen sensors fault':('Failure of the LN2 sensors.','Contact IRELEC support.'),
    'No LN2 available, regulation stopped':('No LN2 detection by phase sensor, from the beginning of filling up.','Check LN2 main supply, check phase sensor, and contact IRELEC support.'),
    'FillingUp Timeout':('Maximum time for filling up was exceeded.','Check LN2 main supply, check level sensor, and contact IRELEC support.')
    }

TOOL_FLANGE = 0
TOOL_CRYOTONG = 1
TOOL_EMBL_ESRF = 2
TOOL_PLATES = 3
TOOL_PUCK = 4




######################## TANGO ATTRIBUTE NAMES ################################
CATS2TANGO = {
  # STATE PARAMS pycats.state_params
  'POWER_1_0': 'Powered',
  'AUTO_MODE_STATUS_1_0': 'AutoMode',
  'DEFAULT_STATUS_1_0': 'DefaultStatus',
  'TOOL_NUM_OR_NAME': 'Tool',
  'PATH_NAME': 'Path',
  'LID_NUM_SAMPLE_MOUNTED_ON_TOOL': 'LidSampleOnTool',
  'NUM_SAMPLE_ON_TOOL': 'NumSampleOnTool',
  'LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER': 'LidSampleOnDiff',
  'NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER': 'NumSampleOnDiff',
  'NUM_OF_PLATE_IN_TOOL': 'NumPlateOnTool',
  'WELL_NUM': 'Well',
  'BARCODE_NUM': 'Barcode',
  'PATH_RUNNING_1_0': 'PathRunning',
  'LN2_REGULATION_RUNNING_1_0': 'LN2Regulating',
  'LN2_WARMING_RUNNING_1_0': 'LN2Warming',
  'ROBOT_SPEED_RATIO': 'SpeedRatio',
  'PUCK_DET_RESULT_DEW1': 'PuckDetectionDewar1',
  'PUCK_DET_RESULT_DEW2': 'PuckDetectionDewar2',
  'POSITION_NUM_DEW1': 'PositionNumberDewar1',
  'POSITION_NUM_DEW2': 'PositionNumberDewar2',

  # DI PARAMS pycats.di_params
  'CRYOGEN_SENSORS_OK': 'di_CryoOK',
  'ESTOP_AND_AIRPRES_OK': 'di_EStopAirpresOK',
  'COLLISION_SENSOR_OK': 'di_CollisonSensorOK',
  'CRYOGEN_HIGH_LEVEL_ALARM': 'di_CryoHighLevelAlarm',
  'CRYOGEN_HIGH_LEVEL': 'di_CryoHighLevel',
  'CRYOGEN_LOW_LEVEL': 'di_CryoHighLevel',
  'CRYOGEN_LOW_LEVEL_ALARM': 'di_CryoLowLevelAlarm',
  'CRYOGEN_LIQUID_DETECTION': 'di_CryoLiquidDetection',
  'PRI1_GFM': 'di_PRI1_GFM',
  'PRI2_API': 'di_PRI2_API',
  'PRI3_APL': 'di_PRI3_APL',
  'PRI4_SOM': 'di_PRI4_SOM',
  'CASSETTE_1_PRESENCE': 'di_Cassette1Presence',
  'CASSETTE_2_PRESENCE': 'di_Cassette2Presence',
  'CASSETTE_3_PRESENCE': 'di_Cassette3Presence',
  'CASSETTE_4_PRESENCE': 'di_Cassette4Presence',
  'CASSETTE_5_PRESENCE': 'di_Cassette5Presence',
  'CASSETTE_6_PRESENCE': 'di_Cassette6Presence',
  'CASSETTE_7_PRESENCE': 'di_Cassette7Presence',
  'CASSETTE_8_PRESENCE': 'di_Cassette8Presence',
  'CASSETTE_9_PRESENCE': 'di_Cassette9Presence',
  'LID_1_OPENED': 'di_Lid1Open',
  'LID_2_OPENED': 'di_Lid2Open',
  'LID_3_OPENED': 'di_Lid3Open',
  'TOOL_OPENED': 'di_ToolOpen',
  'TOOL_CLOSED': 'di_ToolClosed',
  'LIMSW1_ROT_GRIP_AXIS': 'di_LimSW1RotGripAxis',
  'LIMSW2_ROT_GRIP_AXIS': 'di_LimSW2RotGripAxis',
  'MODBUS_PLC_LIFE_BIT': 'di_ModbusPLCLifeBit',
  'LIFE_BIT_COMING_FROM_PLC': 'di_LifeBitFromPLC',
  'ACTIVE_LID_OPENED': 'di_ActiveLidOpened',
  'NEW_ACTIVE_LID_OPENED': 'di_NewActiveLidOpened',
  'TOOL_CHANGER_OPENED': 'di_ToolChangerOpened',
  'ACTIVE_CASSETTE_PRESENCE': 'di_ActiveCassettePresence',
  'NEW_ACTIVE_CASSETTE_PRESENCE': 'di_NewActiveCassettePresence',
  'ALL_LIDS_CLOSED': 'di_AllLidsClosed',
  'PROCESS_INPUT_5': 'di_PRI5',
  'PROCESS_INPUT_6': 'di_PRI6',
  'PROCESS_INPUT_7': 'di_PRI7',
  'PROCESS_INPUT_8': 'di_PRI8',
  'PROCESS_INPUT_9': 'di_PRI9',
  'PROCESS_INPUT_10': 'di_PRI10',
  'PROCESS_INPUT_11': 'di_PRI11',
  'PROCESS_INPUT_12': 'di_PRI12',
  'VIRTUAL_INPUT_90': 'di_VI90',
  'VIRTUAL_INPUT_91': 'di_VI91',
  'VIRTUAL_INPUT_92': 'di_VI92',
  'VIRTUAL_INPUT_93': 'di_VI93',
  'VIRTUAL_INPUT_94': 'di_VI94',
  'VIRTUAL_INPUT_95': 'di_VI95',
  'VIRTUAL_INPUT_96': 'di_VI96',
  'VIRTUAL_INPUT_97': 'di_VI97',
  'VIRTUAL_INPUT_98': 'di_VI98',
  'VIRTUAL_INPUT_99': 'di_VI99',

  # DO PARAMS pycats.do_params
  'TOOL_CHANGER': 'do_ToolChanger',
  'TOOL_OPEN_CLOSE': 'do_ToolOpenClose',
  'FAST_OUTPUT': 'do_FastOutput',
  'PRO1_MON': 'do_PRO1_MON',
  'PRO2_COL': 'do_PRO2_COL',
  'PRO3_LNW': 'do_PRO3_LNW',
  'PRO4_LNA': 'do_PRO4_LNA',
  'GREEN_LIGHT': 'do_GreenLight',
  'PILZ_RELAY_RESET': 'do_PilzRelayReset',
  'SERVO_CARD_ON': 'do_ServoCardOn',
  'SERVO_CARD_ROTATION_+-': 'do_ServoCardRotation',
  'CRYOGEN_VALVE_LN2_C': 'do_CryoValveLN2C',
  'CRYOGEN_VALVE_LN2_E': 'do_CryoValveLN2E',
  'CRYOGEN_VALVE_GN2_E': 'do_CryoValveGN2E',
  'HEATER_ON_OFF': 'do_HeaterOnOff',
  'OPEN_CLOSE_LID_1_1': 'do_OpenCloseLid11',
  'OPEN_CLOSE_LID_1_2': 'do_OpenCloseLid12',
  'OPEN_CLOSE_LID_2_1': 'do_OpenCloseLid21',
  'OPEN_CLOSE_LID_2_2': 'do_OpenCloseLid22',
  'OPEN_CLOSE_LID_3_1': 'do_OpenCloseLid31',
  'OPEN_CLOSE_LID_3_2': 'do_OpenCloseLid32',
  'REQ_DEW1_POS_B1': 'do_RequestDew1PosBit1',
  'REQ_DEW1_POS_B2': 'do_RequestDew1PosBit2',
  'REQ_DEW1_POS_B3': 'do_RequestDew1PosBit3',
  'REQ_DEW1_POS_B4': 'do_RequestDew1PosBit4',
  'OPEN_LID': 'do_OpenLid',
  'CLOSE_LID': 'do_CloseLid',
  'OPEN_NEW_LID': 'do_OpenNewLid',
  'CLOSE_NEW_LID': 'do_CloseNewLid',
  'BARCODE_READER_CONTROL': 'do_BarcodeReader',
  'CLOSE_ALL_LIDS': 'do_CloseAllLids',
  'PRO5_IDL': 'do_PRO5_IDL',
  'PRO6_RAH': 'do_PRO6_RAH',
  'PRO7_RI1': 'do_PRO7_RI1',
  'PRO8_RI2': 'do_PRO8_RI2',
  'PRO9_LIO': 'do_PRO9_LIO',
  'PROCESS_OUTPUT_10': 'do_PRO10',
  'PROCESS_OUTPUT_11': 'do_PRO11',
  'PROCESS_OUTPUT_12': 'do_PRO12',
  'REQ_DEW2_POS_B1': 'do_RequestDew2PosBit1',
  'REQ_DEW2_POS_B2': 'do_RequestDew2PosBit2',
  'REQ_DEW2_POS_B3': 'do_RequestDew2PosBit3',
  'REQ_DEW2_POS_B4': 'do_RequestDew2PosBit4',
  'CRYO_VALVE_LN2_C_DEW2': 'do_CryoValveLN2CDew2',
  'CRYO_VALVE_LN2_E_DEW2': 'do_CryoValveLN2EDew2',
  'CRYO_VALVE_GN2_E_DEW2': 'do_CryoVavleGN2EDew2',
  'OPEN_CLOSE_LID_3_1_DEW2': 'do_OpenCloseLid31Dew2',
  'OPEN_CLOSE_LID_3_2_DEW2': 'do_OpenCloseLid32Dew2',
  'OPEN_CLOSE_LID_4_1_DEW2': 'do_OpenCloseLid41Dew2',
  'OPEN_CLOSE_LID_4_2_DEW2': 'do_OpenCloseLid42Dew2',
  'PROCESS_OUTPUT_13': 'do_PRO13',
  'PROCESS_OUTPUT_14': 'do_PRO14',
  'PROCESS_OUTPUT_15': 'do_PRO15',
  'PROCESS_OUTPUT_16': 'do_PRO16',
  'ROT_DEW_NEW_POS_CTRL_ROBOT_WORKING': 'do_RotationDewNewPosWorking',
  'ROT_DEW_POS_CTRL_CASS_LOADING': 'do_RotationDewarPosCassLoading',
  'ROT_DEW_POS_CTRL_ROBOT_WORKING': 'do_RotationDewPosWorking',

  # POSITION PARAMS pycats.position_params
  'X_POSITION_IN_MM': 'Xpos',
  'Y_POSITION_IN_MM': 'Ypos',
  'Z_POSITION_IN_MM': 'Zpos',
  'RX_POSITION_IN_MM': 'RXpos',
  'RY_POSITION_IN_MM': 'RYpos',
  'RZ_POSITION_IN_MM': 'RZpos',

  # MESSAGE
  'MESSAGE': 'Message'
  }

TANGO2CATS = {}
for k,v in CATS2TANGO.iteritems(): TANGO2CATS[v] = k

###############################################################################


class CS8Connection():
  def __init__(self, host=None, operate_port=None, monitor_port=None):
    self.sock_op = None
    self.lock_op = Lock()
    self.sock_mon = None
    self.lock_mon = Lock()
    if host is not None and operate_port is not None and monitor_port is not None:
      self.connect(host, operate_port, monitor_port)

  def __del__(self):
    self.disconnect()

  def connect(self, host, operate_port, monitor_port):
    self.host = host
    self.operate_port = operate_port
    self.monitor_port = monitor_port

    # Operate the CATS system
    self.sock_op = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock_op.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    self.sock_op.connect((self.host, self.operate_port))
    # Monitor the CATS system
    self.sock_mon = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock_mon.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    self.sock_mon.connect((self.host, self.monitor_port))

  def disconnect(self):
    if self.sock_op is not None:
      self.sock_op.close()
      self.sock_op = None
    if self.sock_mon is not None:
      self.sock_mon.close()
      self.sock_mon = None
    # if you disconnect and connect immediately, some times you recieve '[Errno 104] Connection reset by peer'
    import time
    time.sleep(0.05)


  def _query(self, sock, cmd):
    sock.send(cmd+'\r')
    received = sock.recv(1024)
    # !!! WARNING !!!
    # THERE IS NO CONTROL OF THE END OF MESSAGE
    #
    # AS IT IS SAID IN http://www.amk.ca/python/howto/sockets/
    # SECTION "3 Using a Socket"
    #
    # A protocol like HTTP uses a socket for only one
    # transfer. The client sends a request, the reads a
    # reply. That's it. The socket is discarded. This
    # means that a client can detect the end of the reply
    # by receiving 0 bytes.
    # 
    # But if you plan to reuse your socket for further
    # transfers, you need to realize that there is no
    # "EOT" (End of Transfer) on a socket. I repeat: if a
    # socket send or recv returns after handling 0 bytes,
    # the connection has been broken. If the connection
    # has not been broken, you may wait on a recv forever,
    # because the socket will not tell you that there's
    # nothing more to read (for now). Now if you think
    # about that a bit, you'll come to realize a
    # fundamental truth of sockets: messages must either
    # be fixed length (yuck), or be delimited (shrug), or
    # indicate how long they are (much better), or end by
    # shutting down the connection. The choice is entirely
    # yours, (but some ways are righter than others).

    # CHECK THAT THE ANSWER IS FROM THE COMMAND SENT
    received = received.replace('\r','')
    cmd_name = (cmd.find('(') > 0 and cmd[:cmd.find('(')]) or cmd
    if not received.startswith(cmd_name) and cmd != 'message':
        raise Exception('Answer is not the one expected.\nCmd: %s\nAns: %s' % (cmd, received))

    return received

  ### OPERATE HELPER FUNCTIONS ###
  def operate(self, cmd):
    with self.lock_op:
      return self._query(self.sock_op, cmd)

  # 3.6.5.1 General commands
  def powerOn(self): return self.operate('on')
  def powerOff(self): return self.operate('off')
  def panic(self): return self.operate('panic')
  def abort(self): return self.operate('abort')
  def pause(self): return self.operate('pause')
  def reset(self): return self.operate('reset')
  def restart(self): return self.operate('restart')
  def backup(self, usbport): return self.operate('backup(%s)'%usbport)
  def restore(self, usbport): return self.operate('resotre(%s)'%usbport)

  # 3.6.5.2 Trajectories commands
  # All trajectory commands share the same argument table ?!?!?!
  # NOT USED PARAMETERS should be filled with 0s
  #
  # #0   #1  #2     #3     #4
  # tool lid sample newlid newsample
  # #5    #6   #7   #8      #9
  # plate well type drop    toolcal
  # #10     #11     #12     #13   #14
  # x_shift y_shift z_shift angle oscillations
  # #15      #16  #17         #18      #19
  # exp_time step final_angle spare_18 spare_19
  #
  # Notes:
  # tool 0:Flange 1:Cryotong 2:EMBL/ESRF 3:Plates
  # type FOR CRYOTONG TOOL: 0:Actor 1:UniPuck
  # type FOR PLATES: NO INFO IN DOCUMENTATION

  def trajectory(self, cmd, tool, lid=0, sample=0, newlid=0, newsample=0, \
                     plate=0, well=0, type=0, drop=0, toolcal=0, \
                     x_shift=0, y_shift=0, z_shift=0, angle=0, oscillations=0, \
                     exp_time=0, step=0, final_angle=0, spare_18=0, spare_19=0):

    # Some checks
    if tool not in ("2", "3"):
      raise Exception('Only EMBL/SPINE or PLATES allowed')

    args = [tool, lid, sample, newlid, newsample, plate, well, type, \
              drop, toolcal, x_shift, y_shift, z_shift, angle, \
              oscillations, exp_time, step, final_angle, spare_18, spare_19]
    args_str = ','.join(map(str, args))
    cmd_and_args = cmd + '(' + args_str + ')'
    return self.operate(cmd_and_args)

  def home(self, tool):
    return self.trajectory('home', tool)

  def safe(self, tool):
    return self.trajectory('safe', tool)

  def put(self, tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift):
    return self.trajectory('put', tool, lid, sample, 0, 0, 0, 0, type, 0, toolcal, x_shift, y_shift, z_shift)

  def put_bcrd(self, tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift):
    return self.trajectory('put_bcrd', tool, lid, sample, 0, 0, 0, 0, type, 0, toolcal, x_shift, y_shift, z_shift)

  def get(self, tool, toolcal, x_shift, y_shift, z_shift):
    return self.trajectory('get', tool, 0, 0, 0, 0, 0, 0, 0, 0, toolcal, x_shift, y_shift, z_shift)

  def getput(self, tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift):
    return self.trajectory('getput', tool, lid, sample, 0, 0, 0, 0, type, 0, toolcal, x_shift, y_shift, z_shift)

  def getput_bcrd(self, tool, lid, sample, type, toolcal, x_shift, y_shift, z_shift):
    return self.trajectory('getput_bcrd', tool, lid, sample, 0, 0, 0, 0, type, 0, toolcal, x_shift, y_shift, z_shift)

  def barcode(self, tool, newlid, newsample, type, toolcal):
    return self.trajectory('barcode', tool, 0, 0, newlid, newsample, 0, 0, type, 0, toolcal)

  def back(self, tool, toolcal):
    return self.trajectory('back', tool, 0, 0, 0, 0, 0, 0, 0, toolcal)

  def transfer(self, tool, lid, sample, newlid, newsample, type, toolcal):
    return self.trajectory('transfer', tool, lid, sample, newlid, newsample, 0, 0, type, 0, toolcal)

  def soak(self, tool, lid):
    return self.trajectory('soak', tool, lid)

  def dry(self, tool):
    return self.trajectory('dry', tool)

  def gotodif(self, tool, lid, sample, type, toolcal):
    return self.trajectory('gotodif', tool, lid, sample, 0, 0, 0, 0, type, 0, toolcal)

  def rd_position(self, tool, lid):
    return self.trajectory('rd_position', tool, lid)

  def rd_load(tool, newlid):
    return self.trajectory('rd_load', tool, 0, 0, newlid)
  
  def puckdetect(self, lid, toolcal):
    return self.trajectory('puckdetect', 4, lid, 0, 0, 0, 0, 0, 0, 0, toolcal)
    
  # 3.6.5.3 Crystallization plate commands
  def putplate(self, tool, plate, well, type, toolcal):
    return self.trajectory('putplate',tool, 0, 0, 0, 0, plate, well, type, 0, toolcal)

  def getplate(self, tool, drop, toolcal):
    return self.trajectory('getplate', tool, 0, 0, 0, 0, 0, 0, 0, drop, toolcal)

  def getputplate(self, tool, plate, well, type, drop, toolcal):
    return self.trajectory('getputplate',tool, 0, 0, 0, 0, plate, well, type, drop, toolcal)

  def goto_well(self, tool, plate, well, toolcal):
    return self.trajectory('goto_well',tool, 0, 0, 0, 0, plate, well, 0, 0, toolcal)

  def adjust(self, tool, toolcal, x_shift, y_shift):
    return self.trajectory('adjust', tool, 0, 0, 0, 0, 0, 0, 0, 0, toolcal, x_shift, y_shift)

  def focus(self, tool, toolcal, z_shift):
    return self.trajectory('focus', tool, 0, 0, 0, 0, 0, 0, 0, 0, toolcal, 0, 0, z_shift)

  def expose(self, tool, toolcal, angle, oscillations, exp_time, step):
    return self.trajectory('expose', tool, 0, 0, 0, 0, 0, 0, 0, 0, toolcal, 0, 0, 0, \
                      angle, oscillations, exp_time, step)

  def collect(self, tool, toolcal, angle, oscillations, exp_time, step, final_angle):
    return self.trajectory('collect', tool, 0, 0, 0, 0, 0, 0, 0, 0, toolcal, 0, 0, 0, \
                      angle, oscillations, exp_time, step, final_angle)

  def setplateangle(self, tool, toolcal, angle):
    return self.trajectory('setplateangle', tool, 0, 0, 0, 0, 0, 0, 0, 0, toolcal, 0, 0, 0, angle)

  # GOTODIF ALREADY DEFINED FOR PINS!!!!
  #def gotodif(self, tool, plate, well, type, toolcal):
  #  return self.trajectory('gotodif',tool, 0, 0, 0, 0, plate, well, type, 0, toolcal)


  # 3.6.5.4 Virtual Inputs
  def vdi9xon(self, input): return self.operate('vdi%don'%input)
  def vdi9xoff(self, input): return self.operate('vdi%doff'%input)

  # 3.6.5.5 Commands for LN2 controller
  def regulon(self): return self.operate('regulon')
  def reguloff(self): return self.operate('reguloff')
  def warmon(self): return self.operate('warmon')
  def warmoff(self): return self.operate('warmoff')
  def regulon1(self): return self.operate('regulon1')
  def reguloff1(self): return self.operate('reguloff1')
  def regulon2(self): return self.operate('regulon2')
  def reguloff2(self): return self.operate('reguloff2')

  # 3.6.5.6 Maintenance commands
  def openlid1(self): return self.operate('openlid1')
  def closelid1(self): return self.operate('closelid1')
  def openlid2(self): return self.operate('openlid2')
  def closelid2(self): return self.operate('closelid2')
  def openlid3(self): return self.operate('openlid3')
  def closelid3(self): return self.operate('closelid3')
  def openlid4(self): return self.operate('openlid4')
  def closelid4(self): return self.operate('closelid4')
  def opentool(self): return self.operate('opentool')
  def closetool(self): return self.operate('closetool')
  def magneton(self): return self.operate('magneton')
  def magnetoff(self): return self.operate('magnetoff')
  def heateron(self): return self.operate('heateron')
  def heateroff(self): return self.operate('heateroff')
  def initdew1(self): return self.operate('initdew1')
  def initdew2(self): return self.operate('initdew2')
  def onestaticdw(self): return self.operate('1staticdw')
  def tworotatingdw(self): return self.operate('2rotatingdw')

  # NOT DOCUMENTED THREE NEW COMMANDS...
  def clear_memory(self): return self.operate('clear memory')
  def reset_parameters(self): return self.operate('reset parameters')
  def resetmotion(self): return self.operate('resetMotion')


  ### MONITOR HELPER FUNCTIONS ###
  def monitor(self, cmd):
    with self.lock_mon:
      return self._query(self.sock_mon, cmd)

  # 3.6.5.7 Status commands
  def state(self): return self.monitor('state')
  def di(self): return self.monitor('di')
  def do(self): return self.monitor('do')
  def position(self): return self.monitor('position')
  def message(self): return self.monitor('message')
  def config(self): return self.monitor('config')

  # Some timing tests:
  # %timeit -n 10 -r 10 cs8connection.state()
  # 10 loops, best of 10: 14.8 ms per loop
  # %timeit -n 10 -r 10 cs8connection.di()
  # 10 loops, best of 10: 22.7 ms per loop
  # %timeit -n 10 -r 10 cs8connection.do()
  # 10 loops, best of 10: 17.3 ms per loop
  #  %timeit -n 10 -r 10 cs8connection.position()
  # 10 loops, best of 10: 12.9 ms per loop
  # %timeit -n 10 -r 10 cs8connection.message()
  # 10 loops, best of 10: 11.2 ms per loop
  #
  # 14.8+22.7+17.3+12.9+11.2 = 78.9 ms
  # %timeit -n 10 -r 10 c.getStatusDict()
  # 10 loops, best of 10: 84 ms per loop

  def getStatusDict(self):
    state_ans = self.state()
    di_ans = self.di()
    do_ans = self.do()
    position_ans = self.position()
    message_ans = self.message()
    status_dict = {}

    # State
    state_values = state_ans[state_ans.find('(')+1:-1].split(',')
    for i,v in enumerate(state_values):
      key = state_params[i]
      # Make flags boolean :-D
      if key.endswith('_1_0'):
        v = v == '1'
      # Make numbers integer :-D
      elif key in ['LID_NUM_SAMPLE_MOUNTED_ON_TOOL',
                   'NUM_SAMPLE_ON_TOOL',
                   'LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER',
                   'NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER',
                   'NUM_OF_PLATE_IN_TOOL',
                   'WELL_NUM',
                   'PUCK_DET_RESULT_DEW1',
                   'PUCK_DET_RESULT_DEW2',
                   'POSITION_NUM_DEW1',
                   'POSITION_NUM_DEW2']:
        if v == '': v = -1
        else: v = int(v)
      elif key == 'ROBOT_SPEED_RATIO':
        v = float(v)
      status_dict[key] = v

    # DI
    di_str = di_ans[di_ans.find('(')+1:-1]
    di_values = map(lambda x:x=='1', di_str)
    for i,v in enumerate(di_values):
      key = di_params[i]
      if key != '.':
        status_dict[key] = v

    # DO
    do_str = do_ans[do_ans.find('(')+1:-1]
    do_values = map(lambda x:x=='1', do_str)
    for i,v in enumerate(do_values):
      key = do_params[i]
      if key != '.':
        status_dict[key] = v

    # POSITION
    position_values = position_ans[position_ans.find('(')+1:-1].split(',')
    for i,v in enumerate(position_values):
      key = position_params[i]
      status_dict[key] = float(v)

    # MESSAGE
    status_dict['MESSAGE'] = message_ans

    return status_dict
    

######################################################
# Just for testing
if __name__ == '__main__':
  import time
  cs8 = CS8Connection()
  cs8.connect('bl13cats.cells.es', 1000, 10000)

  print '1) Check monitoring'
  print cs8.state()
  print cs8.di()
  print cs8.do()
  print cs8.position()
  print cs8.message()
  #
  #print
  #print '2) Check operation'
  #print cs8.di()
  #print cs8.openlid1()
  #time.sleep(4)
  #print cs8.di()
  #print cs8.closelid1()
  #time.sleep(4)
  #print cs8.di()




















