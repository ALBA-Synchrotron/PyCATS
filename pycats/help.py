di_help = {
    '.': ('NOT_USED', 'NOT_USED'),
    'CRYOGEN_SENSORS_OK': ('SENSOR_FAILURE', 'SENSORS_OK'),
    'ESTOP_AND_AIRPRES_OK': ('E-STOP_TRIGGERED_OR_PRESSURE_LOSS', 'NO_E-STOP_AND_PRESSURE_OK'),
    'COLLISION_SENSOR_OK': ('COLLISION', 'NO_COLLISION'),
    'CRYOGEN_HIGH_LEVEL_ALARM': ('HIGH_LEVEL_ALARM', 'NO_ALARM'),
    'CRYOGEN_HIGH_LEVEL': ('HIGH_LEVEL_NOT_REACHED', 'HIGH_LEVEL_REACHED'),
    'CRYOGEN_LOW_LEVEL': ('LOW_LEVEL_NOT_REACHED', 'LOW_LEVEL_REACHED'),
    'CRYOGEN_LOW_LEVEL_ALARM': ('LOW_LEVEL_ALARM', 'NO_ALARM'),
    'CRYOGEN_LIQUID_DETECTION': ('GASEOUS_PHASE', 'LIQUID_PHASE'),
    'PRI_GFM': ('The robot cannot move', 'The robot can move in area 0'),
    'PRI_API': ('Sample environment is not ready for put/get of pins', 'Sample environment is ready for put/get of pins'),
    'PRI_APL': ('Sample environment is not ready for put/get of plates', 'Sample environment is ready for put/get of plates'),
    'PRI_SOM': ('No sample detected on magnet', 'Sample detected on magnet'),
    'PLATE_ON_DIFF': ('No plate detected on diff', 'Plate detected on diffractometer'),
    'DIFF_PLATE_MODE': ('Diff not in plate mode', 'Diffractometer is in plate mode'),
    'CASSETTE_1_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_2_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_3_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_4_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_5_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_6_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_7_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_8_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'CASSETTE_9_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'LID_1_OPENED': ('LID_NOT_OPENED', 'LID_COMPLETELY_OPENED'),
    'LID_2_OPENED': ('LID_NOT_OPENED', 'LID_COMPLETELY_OPENED'),
    'LID_3_OPENED': ('LID_NOT_OPENED', 'LID_COMPLETELY_OPENED'),
    'TOOL_OPENED': ('TOOL_NOT_COMPLETELY_OPENED', 'TOOL_COMPLETELY_OPENED'),
    'TOOL_CLOSED': ('TOOL_NOT_COMPLETELY_CLOSED', 'TOOL_COMPLETELY_CLOSED'),
    'LIMSW1_ROT_GRIP_AXIS': ('GRIPPER_IN_THE_DIFFRACTOMETER_ANGULAR_POSITION', 'GRIPPER_NOT_IN_THE_DIFFRACTOMETER_ANGULAR_POSITION'),
    'LIMSW2_ROT_GRIP_AXIS': ('GRIPPER_IN_THE_DEWAR_ANGULAR_POSITION', 'GRIPPER_NOT_IN_THE_DEWAR_ANGULAR_POSITION'),
    'MODBUS_PLC_LIFE_BIT': ('---', '---'),
    'LIFE_BIT_COMING_FROM_PLC': ('---', '---'),
    'ACTIVE_LID_OPENED': ('LID_NOT_OPENED', 'LID_COMPLETELY_OPENED'),
    'NEW_ACTIVE_LID_OPENED': ('LID_NOT_OPENED', 'LID_COMPLETELY_OPENED'),
    'TOOL_CHANGER_OPENED': ('TOOL_CHANGER_RELEASED', 'TOOL_CHANGER_ENGAGED'),
    'ACTIVE_CASSETTE_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'NEW_ACTIVE_CASSETTE_PRESENCE': ('NO_CASSETTE', 'CASSETTE_IN_PLACE'),
    'ALL_LIDS_CLOSED': ('LID(S)_COMPLETELY_CLOSED', 'ALL_LIDS_NOT_OPENED'),
    'PROCESS_INPUT_5': ('---', '---'),
    'PROCESS_INPUT_6': ('---', '---'),
    'PROCESS_INPUT_7': ('---', '---'),
    'PROCESS_INPUT_8': ('---', '---'),
    'PROCESS_INPUT_9': ('---', '---'),
    'PROCESS_INPUT_10': ('---', '---'),
    'PROCESS_INPUT_11': ('---', '---'),
    'PROCESS_INPUT_12': ('---', '---'),
    'VIRTUAL_INPUT_90': ('---', '---'),
    'VIRTUAL_INPUT_91': ('---', '---'),
    'VIRTUAL_INPUT_92': ('---', '---'),
    'VIRTUAL_INPUT_93': ('---', '---'),
    'VIRTUAL_INPUT_94': ('---', '---'),
    'VIRTUAL_INPUT_95': ('---', '---'),
    'VIRTUAL_INPUT_96': ('---', '---'),
    'VIRTUAL_INPUT_97': ('---', '---'),
    'VIRTUAL_INPUT_98': ('---', '---'),
    'VIRTUAL_INPUT_99': ('---', '---')
}

do_help = {
    '.': ('---', '---'),
    'TOOL_CHANGER': ('TOOL_GRIPPED', 'TOOL_RELEASED'),
    'TOOL_OPEN_CLOSE': ('CLOSE_THE_TOOL', 'OPEN_THE_TOOL'),
    'FAST_OUTPUT': ('CONTACT_OPENED', 'CONTACT_CLOSED'),
    'PRO1_MON': ('Turn the smart magnet on', 'Turn the smart magnet off'),
    'PRO2_COL': ('No collision', 'A collision has occurred'),
    'PRO3_LNW': ('No liquid N2 warning has been triggered', 'Liquid N2 warning has been triggered'),
    'PRO4_LNA': ('No liquid N2 alarm has been triggered', 'Liquid N2 alarm has been triggered'),
    'GREEN_LIGHT': ('---', 'MODBUS_LINK_OK'),
    'PILZ_RELAY_RESET': ('---', 'RESET_OF_THE_RELAY'),
    'SERVO_CARD_ON': ('CARD_DISABLED', 'CARD_ON'),
    'SERVO_CARD_ROTATION_+-': ('TOWARDS_THE_DIFFRACTOMETER_POSITION', 'TOWARDS_THE_DEWAR_POSITION'),
    'CRYOGEN_VALVE_LN2_C': ('VALVE_CLOSED', 'VALVE_OPENED'),
    'CRYOGEN_VALVE_LN2_E': ('VALVE_CLOSED', 'VALVE_OPENED'),
    'CRYOGEN_VALVE_GN2_E': ('VALVE_CLOSED', 'VALVE_OPENED'),
    'HEATER_ON_OFF': ('HEATER_OFF', 'HEATER_ON'),
    'OPEN_CLOSE_LID_1_1': ('CLOSE_LID_1', 'OPEN_LID_1'),
    'OPEN_CLOSE_LID_1_2': ('OPEN_LID_1', 'CLOSE_LID_1'),
    'OPEN_CLOSE_LID_2_1': ('CLOSE_LID_2', 'OPEN_LID_2'),
    'OPEN_CLOSE_LID_2_2': ('OPEN_LID_2', 'CLOSE_LID_2'),
    'OPEN_CLOSE_LID_3_1': ('CLOSE_LID_3', 'OPEN_LID_3'),
    'OPEN_CLOSE_LID_3_2': ('OPEN_LID_3', 'CLOSE_LID_3'),
    'REQ_DEW1_POS_B1': ('---', '---'),
    'REQ_DEW1_POS_B2': ('---', '---'),
    'REQ_DEW1_POS_B3': ('---', '---'),
    'REQ_DEW1_POS_B4': ('---', '---'),
    'OPEN_LID': ('---', 'OPEN_ACTIVE_LID'),
    'CLOSE_LID': ('---', 'CLOSE_ACTIVE_LID'),
    'OPEN_NEW_LID': ('---', 'OPEN_NEW_ACTIVE_LID'),
    'CLOSE_NEW_LID': ('---', 'CLOSE_NEW_ACTIVE_LID'),
    'BARCODE_READER_CONTROL': ('---', 'ASK_FOR_A_BARCODE_READING'),
    'CLOSE_ALL_LIDS': ('---', 'CLOSE_ALL_LIDS'),
    'PRO5_IDL': ('The robot is executing a command', 'The robot is not executing any command'),
    'PRO6_RAH': ('Robot arm is running a trajectory', 'Robot is at home position'),
    'PRO7_RI1': ('Robot is not in area 1: (a) stop routine that checks RI2 and (b) enable motors', 'Robot is in area 1:  (a) start routine that checks RI2 and (b) disable motors'),
    'PRO8_RI2': ('The robot is not in area 2. So, the cryostream nozzle is allowed  at position 1 (~5 mm from sample)', 'The robot is in area 2. So, the cryostream nozzle is allowed  at position 2 (~40? mm from sample)'),
    'PRO9_LIO': ('No lid is open', 'Any lid is open'),
    'PROCESS_OUTPUT_10': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_11': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_12': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'REQ_DEW2_POS_B1': ('---', '---'),
    'REQ_DEW2_POS_B2': ('---', '---'),
    'REQ_DEW2_POS_B3': ('---', '---'),
    'REQ_DEW2_POS_B4': ('---', '---'),
    'CRYO_VALVE_LN2_C_DEW2': ('VALVE_CLOSED', 'VALVE_OPENED'),
    'CRYO_VALVE_LN2_E_DEW2': ('VALVE_CLOSED', 'VALVE_OPENED'),
    'CRYO_VALVE_GN2_E_DEW2': ('VALVE_CLOSED', 'VALVE_OPENED'),
    'OPEN_CLOSE_LID_3_1_DEW2': ('CLOSE_LID_3', 'OPEN_LID_3'),
    'OPEN_CLOSE_LID_3_2_DEW2': ('OPEN_LID_3', 'CLOSE_LID_3'),
    'OPEN_CLOSE_LID_4_1_DEW2': ('CLOSE_LID_4', 'OPEN_LID_4'),
    'OPEN_CLOSE_LID_4_2_DEW2': ('OPEN_LID_4', 'CLOSE_LID_4'),
    'PROCESS_OUTPUT_13': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_14': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_15': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'PROCESS_OUTPUT_16': ('OPEN_THE_CONTACT', 'CLOSE_THE_CONTACT'),
    'ROT_DEW_NEW_POS_CTRL_ROBOT_WORKING': ('---', 'Ask for a Dewar positioning on robot working lid'),
    'ROT_DEW_POS_CTRL_CASS_LOADING': ('---', 'Ask for the positioning on cassettes loading lid'),
    'ROT_DEW_POS_CTRL_ROBOT_WORKING': ('---', 'Ask for a Dewar positioning on robot working lid'),
}

message_help = {
    'BackUp is running': ('BackUp is running.', '/'),
    'BackUp error': ('BackUp error.', 'Make sure the USB Key is well plugged.'),
    'BackUp completed': ('BackUp completed.', '/'),
    'Restore is running': ('Restore is running.', '/'),
    'Restore error': ('Restore error.', 'Make sure the USB Key is well plugged or BackUp is stored on it.'),
    'Restore completed': ('Restore completed.', '/'),
    'doors opened': ('Door(s) is(are) opened.', 'Close the door(s) or switch to Manual Mode.'),
    'Manual brake control selected': ('Manual brake button is not 0 position.', 'Turn the manual brake button to the 0 position.'),
    'emerency stop or air pressure fault': ('One of emergency stops has been pressed or the compressed air pressure is too low.', 'Pull off the emergency stop or check the compressed air.'),
    'collision detection': ('The robot hit something.', 'Unlock the arm brakes, move the robot manually and then re-engaged the shock detector.'),
    'Modbus communication fault': ('Modbus communication fault.', 'Make sure that the Ethernet cable is well plugged on the CS8C controller and on the PLC (inside the electro-pneumatic racks). Make sure that the power of the CS8C controller and the PLC is on.'),
    'LOC menu not disabled': ('Menu LOC is selected on the Teach Pendant.', 'Quit the LOC menu of the Teach Pendant.'),
    'Remote Mode requested': ('Remote Mode is not selected.', 'Switch to Remorte Mode on the Teach Pendant.'),
    'Disable when path is running': ('A trajectory command has been sent to system which is already processing a task.', 'Wait fo rthe end of the path or abort the path which is running.'),
    'X- collision': ('The X- limit is reached in the frame World.', 'Modify the trajectory or readjust the limit.'),
    'X+ collision': ('The X+ limit is reached in the frame World.', 'Modify the trajectory or readjust the limit.'),
    'Y- collision': ('The Y- limit is reached in the frame World.', 'Modify the trajectory or readjust the limit.'),
    'Y+ collision': ('The Y+ limit is reached in the frame World.', 'Modify the trajectory or readjust the limit.'),
    'Z- collision': ('The Z- limit is reached in the frame World.', 'Modify the trajectory or readjust the limit.'),
    'Z+ collision': ('The Z+ limit is reached in the frame World.', 'Modify the trajectory or readjust the limit.'),
    'Robot foot collision': ('Collision with the foot of the robot arm.', 'Modify the trajectory.'),
    'low level alarm': ('LN2 level in the Dewar is low.', 'Check the LN2 supply.'),
    'high level alarm': ('LN2 level in the Dewar is too high.', 'Close the main valve of the LN2 supply and contact IRELEC support.'),
    'cryogenic incoherent signals': ('LN2 low level is false and LN2 high level is true.', 'Check the pressure of the LN2 supply and control the LN2 sensors.'),
    'cryogen sensors fault': ('Failure of the LN2 sensors.', 'Contact IRELEC support.'),
    'No LN2 available, regulation stopped': ('No LN2 detection by phase sensor, from the beginning of filling up.', 'Check LN2 main supply, check phase sensor, and contact IRELEC support.'),
    'FillingUp Timeout': ('Maximum time for filling up was exceeded.', 'Check LN2 main supply, check level sensor, and contact IRELEC support.')
}
