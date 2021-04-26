import socket
import struct
from threading import Lock


__all__ = ['CS8Connection', 'di_params', 'do_params', 'state_params',
           'position_params']


MODEL_CATS, MODEL_ISARA = (0, 1)
MODELS = {
    MODEL_CATS: "CATS",
    MODEL_ISARA: "ISARA",
}

PUCK_IGNORE, PUCK_SPINE, PUCK_UNIPUCK = (0, 1, 2)

RECOVER_GET_FAILED = 1

state_params = [
    'POWER_1_0',
    'AUTO_MODE_STATUS_1_0',
    'DEFAULT_STATUS_1_0',
    'TOOL_NUM_OR_NAME',
    'PATH_NAME',
    'LID_NUM_SAMPLE_MOUNTED_ON_TOOL',
    'NUM_SAMPLE_ON_TOOL',
    'LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER',
    'NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER',
    'NUM_OF_PLATE_ON_TOOL',
    'WELL_NUM',
    'BARCODE_NUM',
    'PATH_RUNNING_1_0',
    'LN2_REGULATION_RUNNING_1_0',
    'LN2_WARMING_RUNNING_1_0',
    'ROBOT_SPEED_RATIO',
    'PUCK_DET_RESULT_DEW1',
    'PUCK_DET_RESULT_DEW2',
    'POSITION_NUM_DEW1',
    'POSITION_NUM_DEW2',
    'LID_NUM_SAMPLE_MOUNTED_ON_TOOL2',
    'NUM_SAMPLE_ON_TOOL2',
    'CURR_NUM_SOAKING',
    'PUCK_TYPE_LID1',
    'PUCK_TYPE_LID2',
    'PUCK_TYPE_LID3']

di_params = [
    'CRYOGEN_SENSORS_OK',
    'ESTOP_AND_AIRPRES_OK',
    'COLLISION_SENSOR_OK',
    'CRYOGEN_HIGH_LEVEL_ALARM',
    'CRYOGEN_HIGH_LEVEL',
    'CRYOGEN_LOW_LEVEL',
    'CRYOGEN_LOW_LEVEL_ALARM',
    'CRYOGEN_LIQUID_DETECTION',
    'PRI_GFM',
    'PRI_API',
    'PRI_APL',
    'PRI_SOM',
    'CASSETTE_1_PRESENCE',
    'CASSETTE_2_PRESENCE',
    'CASSETTE_3_PRESENCE',
    'CASSETTE_4_PRESENCE',
    'CASSETTE_5_PRESENCE',
    'CASSETTE_6_PRESENCE',
    'CASSETTE_7_PRESENCE',
    'CASSETTE_8_PRESENCE',
    'CASSETTE_9_PRESENCE',
    'LID_1_OPENED',
    'LID_2_OPENED',
    'LID_3_OPENED',
    'TOOL_OPENED',
    'TOOL_CLOSED',
    'LIMSW1_ROT_GRIP_AXIS',
    'LIMSW2_ROT_GRIP_AXIS',
    'MODBUS_PLC_LIFE_BIT',
    '.',
    '.',
    'LIFE_BIT_COMING_FROM_PLC',
    'ACTIVE_LID_OPENED',
    'NEW_ACTIVE_LID_OPENED',
    'TOOL_CHANGER_OPENED',
    'ACTIVE_CASSETTE_PRESENCE',
    'NEW_ACTIVE_CASSETTE_PRESENCE',
    'ALL_LIDS_CLOSED',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    'PROCESS_INPUT_5',
    'PROCESS_INPUT_6',
    'PROCESS_INPUT_7',
    'PROCESS_INPUT_8',
    'PROCESS_INPUT_9',
    'PROCESS_INPUT_10',
    'PROCESS_INPUT_11',
    'PROCESS_INPUT_12',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    'VIRTUAL_INPUT_90',
    'VIRTUAL_INPUT_91',
    'VIRTUAL_INPUT_92',
    'VIRTUAL_INPUT_93',
    'VIRTUAL_INPUT_94',
    'VIRTUAL_INPUT_95',
    'VIRTUAL_INPUT_96',
    'VIRTUAL_INPUT_97',
    'VIRTUAL_INPUT_98',
    'VIRTUAL_INPUT_99']

# di information for isara is somehow different -
#   SOM  (SOM is in
#   CASSETTE_X_PRESENCE have no meaning
di_params_isara = [
    'CRYOGEN_SENSORS_OK',
    'ESTOP_AND_AIRPRES_OK',
    'COLLISION_SENSOR_OK',
    'CRYOGEN_HIGH_LEVEL_ALARM',
    'CRYOGEN_HIGH_LEVEL',
    'CRYOGEN_LOW_LEVEL',
    'CRYOGEN_LOW_LEVEL_ALARM',
    'CRYOGEN_LIQUID_DETECTION',
    'PRI_GFM',
    'DIFF_PLATE_MODE',
    'PRI_SOM',
    'PLATE_ON_DIFF',
    'CASSETTE_1_PRESENCE',
    'CASSETTE_2_PRESENCE',
    'CASSETTE_3_PRESENCE',
    'CASSETTE_4_PRESENCE',
    'CASSETTE_5_PRESENCE',
    'CASSETTE_6_PRESENCE',
    'CASSETTE_7_PRESENCE',
    'CASSETTE_8_PRESENCE',
    'CASSETTE_9_PRESENCE',
    'LID_1_OPENED',
    'LID_2_OPENED',
    'LID_3_OPENED',
    'TOOL_OPENED',
    'TOOL_CLOSED',
    'LIMSW1_ROT_GRIP_AXIS',
    'LIMSW2_ROT_GRIP_AXIS',
    'MODBUS_PLC_LIFE_BIT',
    '.',
    '.',
    'LIFE_BIT_COMING_FROM_PLC',
    'ACTIVE_LID_OPENED',
    'NEW_ACTIVE_LID_OPENED',
    'TOOL_CHANGER_OPENED',
    'ACTIVE_CASSETTE_PRESENCE',
    'NEW_ACTIVE_CASSETTE_PRESENCE',
    'ALL_LIDS_CLOSED',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    'PROCESS_INPUT_5',
    'PROCESS_INPUT_6',
    'PROCESS_INPUT_7',
    'PROCESS_INPUT_8',
    'PROCESS_INPUT_9',
    'PROCESS_INPUT_10',
    'PROCESS_INPUT_11',
    'PROCESS_INPUT_12',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    'VIRTUAL_INPUT_90',
    'VIRTUAL_INPUT_91',
    'VIRTUAL_INPUT_92',
    'VIRTUAL_INPUT_93',
    'VIRTUAL_INPUT_94',
    'VIRTUAL_INPUT_95',
    'VIRTUAL_INPUT_96',
    'VIRTUAL_INPUT_97',
    'VIRTUAL_INPUT_98',
    'VIRTUAL_INPUT_99']

do_params = [
    'TOOL_CHANGER',
    'TOOL_OPEN_CLOSE',
    'FAST_OUTPUT',
    '.',
    'PRO1_MON',
    'PRO2_COL',
    'PRO3_LNW',
    'PRO4_LNA',
    'GREEN_LIGHT',
    'PILZ_RELAY_RESET',
    'SERVO_CARD_ON',
    'SERVO_CARD_ROTATION_+-',
    'CRYOGEN_VALVE_LN2_C',
    'CRYOGEN_VALVE_LN2_E',
    'CRYOGEN_VALVE_GN2_E',
    'HEATER_ON_OFF',
    'OPEN_CLOSE_LID_1_1',
    'OPEN_CLOSE_LID_1_2',
    'OPEN_CLOSE_LID_2_1',
    'OPEN_CLOSE_LID_2_2',
    'OPEN_CLOSE_LID_3_1',
    'OPEN_CLOSE_LID_3_2',
    '.',
    '.',
    '.',
    'REQ_DEW1_POS_B1',
    'REQ_DEW1_POS_B2',
    'REQ_DEW1_POS_B3',
    'REQ_DEW1_POS_B4',
    '.',
    '.',
    '.',
    'OPEN_LID',
    'CLOSE_LID',
    'OPEN_NEW_LID',
    'CLOSE_NEW_LID',
    'BARCODE_READER_CONTROL',
    'CLOSE_ALL_LIDS',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    'PRO5_IDL',
    'PRO6_RAH',
    'PRO7_RI1',
    'PRO8_RI2',
    'PRO9_LIO',
    'PROCESS_OUTPUT_10',
    'PROCESS_OUTPUT_11',
    'PROCESS_OUTPUT_12',
    '.',
    '.',
    '.',
    '.',
    'REQ_DEW2_POS_B1',
    'REQ_DEW2_POS_B2',
    'REQ_DEW2_POS_B3',
    'REQ_DEW2_POS_B4',
    '.',
    '.',
    'CRYO_VALVE_LN2_C_DEW2',
    'CRYO_VALVE_LN2_E_DEW2',
    'CRYO_VALVE_GN2_E_DEW2',
    '.',
    'OPEN_CLOSE_LID_3_1_DEW2',
    'OPEN_CLOSE_LID_3_2_DEW2',
    'OPEN_CLOSE_LID_4_1_DEW2',
    'OPEN_CLOSE_LID_4_2_DEW2',
    'PROCESS_OUTPUT_13',
    'PROCESS_OUTPUT_14',
    'PROCESS_OUTPUT_15',
    'PROCESS_OUTPUT_16',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    '.',
    'ROT_DEW_NEW_POS_CTRL_ROBOT_WORKING',
    'ROT_DEW_POS_CTRL_CASS_LOADING',
    'ROT_DEW_POS_CTRL_ROBOT_WORKING']


position_params = [
    'X_POSITION_IN_MM',
    'Y_POSITION_IN_MM',
    'Z_POSITION_IN_MM',
    'RX_POSITION_IN_MM',
    'RY_POSITION_IN_MM',
    'RZ_POSITION_IN_MM']


TOOL_FLANGE = 0
TOOL_CRYOTONG = 1
TOOL_EMBL_ESRF = 2
TOOL_PLATES = 3
TOOL_PUCK = 4


class CS8Connection():
    def __init__(self, host=None, operate_port=None, monitor_port=None,
                 tango_logger=None, model=None):
        self._init_logging(tango_logger)
        self.sock_op = None
        self.lock_op = Lock()
        self.sock_mon = None
        self.lock_mon = Lock()

        self.model = MODEL_CATS  # default.  set_model() to change it

        # info for checking path safe condition for diffractometer
        self.pathinfo = {'safe': False, 'running': False}

        self.is_running = False
        self.is_safe = False
        self.ri1_count = 0
        self.ri2_count = 0
        self.is_inr1 = False
        self.is_inr2 = False
        self.executing_recovery = False

        # grp1 contains paths with one single passage through diffr areas
        self.check_paths_grp1 = ['get', 'put', 'put_bcrd', 'get_HT', 'put_HT']

        # grp2 contains paths with two passages through diffr areas
        # note: for unipuck double gripper still it is only one pass for all
        self.check_paths_grp2 = ['getput', 'getput_bcrd', 'getput_HT']

        # get contains paths including a get operation (to detect recovery
        # needed)
        self.check_paths_get = [
            'getput',
            'getput_bcrd',
            'getput_HT',
            'get',
            'get_HT']

        self.check_paths_all = self.check_paths_grp1 + self.check_paths_grp2

        # use set_puck_types() or property puck_types in device server to
        # change
        self.nb_pucks = 9  # Default 9 pucks
        self.puck_types = [PUCK_SPINE, ] * self.nb_pucks  # default SPINE pucks
        self.puck_presence = [False, ] * self.nb_pucks

        if host is not None and operate_port is not None and monitor_port is not None:
            self.connect(host, operate_port, monitor_port)

        # variables for recovery routines
        self.sample_before_path = -1
        self.lid_before_path = -1
        self.puck_before_path = -1
        self.latest_path = ""

        self._last_command_sent = ""

        self.info("Init CATS connection object")

    def __del__(self):
        self.disconnect()

    def _init_logging(self, logger):
        if logger:
            self.debug = logger.debug
            self.info = logger.info
            self.warn = logger.warn
            self.error = logger.error
            self.debug("Injecting log to tango logger")
        else:
            import logging
            logger = logging.Logger(__name__)
            ch = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s")
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            self.debug = logger.debug
            self.info = logger.info
            self.warn = logger.warning
            self.error = logger.error
            self.debug("Creating new logger %s" % __name__)

    def set_model(self, model):
        if model in ["Isara", "isara", "i"]:
            self.model = MODEL_ISARA

    def get_model(self):
        if self.model in MODELS:
            return MODELS[self.model]
        return "Unknown"

    def set_puck_types(self, puck_types):
        self.nb_pucks = len(puck_types)
        self.puck_types = [None, ] * self.nb_pucks

        for i in range(self.nb_pucks):
            puck_typ = puck_types[i]
            if puck_typ == '2':
                self.puck_types[i] = PUCK_UNIPUCK
            elif puck_typ == '1':
                self.puck_types[i] = PUCK_SPINE
            elif puck_typ == '0':
                self.puck_types[i] = PUCK_IGNORE
            else:
                print("Unknown puck type %s. Puck is ignored " % puck_typ)
                self.puck_types[i] = PUCK_IGNORE

    def get_number_pucks(self):
        return self.nb_pucks

    def get_puck_types(self):
        p_types = self.puck_types
        return p_types

    def get_puck_presence(self):
        return self.puck_presence

    def is_path_safe(self):
        return self.is_safe

    def connect(self, host, operate_port, monitor_port):
        self.host = host
        self.operate_port = operate_port
        self.monitor_port = monitor_port

        # Operate the CATS system
        self.sock_op = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_op.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_LINGER,
            struct.pack(
                'ii',
                1,
                0))
        self.sock_op.connect((self.host, self.operate_port))
        # Monitor the CATS system
        self.sock_mon = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_mon.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_LINGER,
            struct.pack(
                'ii',
                1,
                0))
        self.sock_mon.connect((self.host, self.monitor_port))

        self.debug("Operation socket created (host = %s , port = %s" % (
            self.host, self.operate_port))
        self.debug("Monitor socket created (host = %s , port = %s" % (
            self.host, self.monitor_port))

    def disconnect(self):
        if self.sock_op is not None:
            self.sock_op.close()
            self.sock_op = None
        if self.sock_mon is not None:
            self.sock_mon.close()
            self.sock_mon = None
        # if you disconnect and connect immediately, some times you recieve
        # '[Errno 104] Connection reset by peer'
        import time
        time.sleep(0.05)
        self.debug("Disconnected from CATS server")

    def _query(self, sock, cmd):
        _cmd = cmd + '\r'
        sock.send(_cmd.encode())
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
        received = received.decode('utf-8')
        received = received.replace('\r', '')
        cmd_name = (cmd.find('(') > 0 and cmd[:cmd.find('(')]) or cmd
        if not received.startswith(cmd_name) and cmd != 'message':
            msg = 'Answer is not the one expected.\nCmd: %s\nAns: %s' % (
                cmd, received)
            self.error(msg)
            raise Exception(msg)
        else:
            #        self.debug("Cmd: %s\nAns: %s" % (cmd, received))
            pass
        return received

    ### OPERATE HELPER FUNCTIONS ###
    def operate(self, cmd):
        with self.lock_op:
            #      return self._query(self.sock_op, cmd)
            received = self._query(self.sock_op, cmd)
            self.debug("Cmd: %s, Ans: %s" % (cmd, received))
            self._last_command_sent = cmd
            return received

    # 3.6.5.1 General commands
    def powerOn(self): return self.operate('on')

    def powerOff(self): return self.operate('off')

    def panic(self): return self.operate('panic')

    def abort(self): return self.operate('abort')

    def pause(self): return self.operate('pause')

    def reset(self): return self.operate('reset')

    def restart(self): return self.operate('restart')

    def backup(self, usbport): return self.operate('backup(%s)' % usbport)

    def restore(self, usbport): return self.operate('restore(%s)' % usbport)

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

    def trajectory(
            self,
            cmd,
            tool,
            puck_lid=0,
            sample=0,
            newpuck_lid=0,
            newsample=0,
            plate=0,
            well=0,
            type=0,
            drop=0,
            toolcal=0,
            x_shift=0,
            y_shift=0,
            z_shift=0,
            angle=0,
            oscillations=0,
            exp_time=0,
            step=0,
            final_angle=0,
            spare_18=0,
            spare_19=0):

        # Some checks
        tool = int(tool)
        if cmd in ['setdiffr', 'settool', 'settool2']:
            args = [tool, puck_lid, sample]
            args_str = ','.join(map(str, args))
            cmd_and_args = cmd + '(' + args_str + ')'
            self.debug("sending operation: %s" % cmd_and_args)
        else:
            allowed_tools = (2, 3, 5)
            if cmd in ['home', 'safe']:
                allowed_tools = (0, 2, 3, 5)

            if tool not in allowed_tools:
                raise Exception(
                    'Allowed tools are %s (current is %s)' %
                    (allowed_tools, tool))
            args = [
                tool,
                puck_lid,
                sample,
                newpuck_lid,
                newsample,
                plate,
                well,
                type,
                drop,
                toolcal,
                x_shift,
                y_shift,
                z_shift,
                angle,
                oscillations,
                exp_time,
                step,
                final_angle,
                spare_18,
                spare_19]
            args_str = ','.join(map(str, args))
            cmd_and_args = cmd + '(' + args_str + ')'
        return self.operate(cmd_and_args)

    def home(self, tool):
        return self.trajectory('home', tool)

    def recover(self, tool):
        return self.trajectory('recover', tool)

    def safe(self, tool):
        return self.trajectory('safe', tool)

    def put(
            self,
            tool,
            puck_lid,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift):
        if self.model == MODEL_ISARA:
            toolcal = 0
        return self.trajectory(
            'put',
            tool,
            puck_lid,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def put_bcrd(
            self,
            tool,
            puck_lid,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift):
        if self.model == MODEL_ISARA:
            toolcal = 0
        return self.trajectory(
            'put_bcrd',
            tool,
            puck_lid,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def put_HT(self, tool, sample, type, toolcal, x_shift, y_shift, z_shift):
        return self.trajectory(
            'put_HT',
            tool,
            100,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def get(self, tool, toolcal, x_shift, y_shift, z_shift):
        if self.model == MODEL_ISARA:
            toolcal = 0
        return self.trajectory(
            'get',
            tool,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def getput(
            self,
            tool,
            puck_lid,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift):
        if self.model == MODEL_ISARA:
            toolcal = 0
        return self.trajectory(
            'getput',
            tool,
            puck_lid,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def get_HT(self, tool, toolcal, x_shift, y_shift, z_shift):
        return self.trajectory(
            'get_HT',
            tool,
            100,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def getput_HT(
            self,
            tool,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift):
        return self.trajectory(
            'getput_HT',
            tool,
            100,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def getput_bcrd(
            self,
            tool,
            puck_lid,
            sample,
            type,
            toolcal,
            x_shift,
            y_shift,
            z_shift):
        if self.model == MODEL_ISARA:
            toolcal = 0
        return self.trajectory(
            'getput_bcrd',
            tool,
            puck_lid,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            toolcal,
            x_shift,
            y_shift,
            z_shift)

    def barcode(self, tool, puck_lid, newsample, type, toolcal=None):
        if self.model == MODEL_ISARA:
            return self.trajectory(
                'barcode', tool, puck_lid, newsample, 0, 0, 0, 0, type)
        else:
            return self.trajectory(
                'barcode',
                tool,
                0,
                0,
                puck_lid,
                newsample,
                0,
                0,
                type,
                0,
                toolcal)

    def back(self, tool, toolcal=None):
        if self.model is MODEL_ISARA:
            return self.trajectory('back', tool)
        else:
            return self.trajectory('back', tool, 0, 0, 0, 0, 0, 0, 0, toolcal)

    def transfer(
            self,
            tool,
            puck_lid,
            sample,
            newpuck_lid,
            newsample,
            type,
            toolcal):
        if self.model is MODEL_ISARA:
            raise Exception(
                'Transfer command not available for ISARA Sample Changer')
        return self.trajectory(
            'transfer',
            tool,
            puck_lid,
            sample,
            newpuck_lid,
            newsample,
            0,
            0,
            type,
            0,
            toolcal)

    def soak(self, tool, puck_lid=None):
        if self.model is MODEL_ISARA:
            return self.trajectory('soak', tool)
        else:
            return self.trajectory('soak', tool, puck_lid)

    def dry(self, tool):
        return self.trajectory('dry', tool)

    def dryhome(self, tool):
        if self.model is MODEL_ISARA:
            raise Exception(
                'dryhome command not available for ISARA Model Sample Changer')
        return self.trajectory('dryhome', tool)

    def gotodif(self, tool, puck_lid, sample, type, toolcal):
        if self.model is MODEL_ISARA:
            return self.trajectory(
                'gotodif', tool, puck_lid, sample, 0, 0, 0, 0, type)
        else:
            return self.trajectory(
                'gotodif',
                tool,
                puck_lid,
                sample,
                0,
                0,
                0,
                0,
                type,
                0,
                toolcal)

    def pick(self, tool, puck_or_lid, sample, type):
        return self.trajectory(
            'pick',
            tool,
            puck_or_lid,
            sample,
            0,
            0,
            0,
            0,
            type)

    def getputpick(
            self,
            tool,
            puck_lid,
            sample,
            type,
            x_shift,
            y_shift,
            z_shift):
        if self.model is MODEL_ISARA:
            raise Exception(
                'getpuckpick command not available for ISARA Model Sample Changer')
        return self.trajectory(
            'getputpick',
            tool,
            puck_lid,
            sample,
            0,
            0,
            0,
            0,
            type,
            0,
            0,
            x_shift,
            y_shift,
            z_shift)

    def rd_position(self, tool, puck_lid):
        if self.model is MODEL_ISARA:
            raise Exception(
                'rd_position command not available for ISARA Sample Changer')
        return self.trajectory('rd_position', tool, puck_lid)

    def rd_load(self, tool, newpuck_lid):
        if self.model is MODEL_ISARA:
            raise Exception(
                'rd_load command not available for ISARA Sample Changer')
        return self.trajectory('rd_load', tool, 0, 0, newpuck_lid)

    def puckdetect(self, puck_lid, toolcal):
        if self.model is MODEL_ISARA:
            raise Exception(
                'puckdetect command not available for ISARA Sample Changer')
        return self.trajectory(
            'puckdetect',
            4,
            puck_lid,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal)

    def setondiff(self, puck_lid, sample, type):
        print((
            "Setting info for sample on diff to %s:%s - type = %s" %
            (puck_lid, sample, type)))
        ret = self.trajectory('setdiffr', puck_lid, sample, type)
        print(("   - returns:  %s" % ret))
        return ret

    def cap_on_lid(self, tool):
        if self.model is MODEL_ISARA:
            raise Exception(
                'capOnLid command not available for ISARA Model Sample Changer')
        return self.trajectory('capOnLid', tool)

    def cap_off_lid(self, tool):
        if self.model is MODEL_ISARA:
            raise Exception(
                'capOffLid command not available for ISARA Model Sample Changer')
        return self.trajectory('capOffLid', tool)

    def toolcalibration(self, tool):
        return self.trajectory('toolcal', tool)

    # 3.6.5.3 Crystallization plate commands
    def putplate(self, tool, plate, well=None, type=None, toolcal=None):
        if self.model is MODEL_ISARA:
            return self.trajectory('putplate', tool, 0, 0, 0, 0, plate)
        else:
            return self.trajectory(
                'putplate',
                tool,
                0,
                0,
                0,
                0,
                plate,
                well,
                type,
                0,
                toolcal)

    def getplate(self, tool=None, drop=None, toolcal=None):
        if self.model is MODEL_ISARA:
            return self.trajectory('getplate', tool)
        else:
            return self.trajectory(
                'getplate', tool, 0, 0, 0, 0, 0, 0, 0, drop, toolcal)

    def getputplate(
            self,
            tool,
            plate,
            well=None,
            type=None,
            drop=None,
            toolcal=None):
        if self.model is MODEL_ISARA:
            return self.trajectory('getputplate', tool, 0, 0, 0, 0, plate)
        else:
            return self.trajectory(
                'getputplate',
                tool,
                0,
                0,
                0,
                0,
                plate,
                well,
                type,
                drop,
                toolcal)

    def goto_well(self, tool, plate, well, toolcal):
        if self.model is MODEL_ISARA:
            raise Exception(
                'goto_well command not available for ISARA Sample Changer')
        return self.trajectory(
            'goto_well',
            tool,
            0,
            0,
            0,
            0,
            plate,
            well,
            0,
            0,
            toolcal)

    def adjust(self, tool, toolcal, x_shift, y_shift):
        if self.model is MODEL_ISARA:
            raise Exception(
                'adjust command not available for ISARA Sample Changer')
        return self.trajectory(
            'adjust',
            tool,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            x_shift,
            y_shift)

    def focus(self, tool, toolcal, z_shift):
        if self.model is MODEL_ISARA:
            raise Exception(
                'focus command not available for ISARA Sample Changer')
        return self.trajectory(
            'focus',
            tool,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            0,
            0,
            z_shift)

    def expose(self, tool, toolcal, angle, oscillations, exp_time, step):
        if self.model is MODEL_ISARA:
            raise Exception(
                'expose command not available for ISARA Sample Changer')
        return self.trajectory(
            'expose',
            tool,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            0,
            0,
            0,
            angle,
            oscillations,
            exp_time,
            step)

    def collect(
            self,
            tool,
            toolcal,
            angle,
            oscillations,
            exp_time,
            step,
            final_angle):
        if self.model is MODEL_ISARA:
            raise Exception(
                'collect command not available for ISARA Sample Changer')
        return self.trajectory(
            'collect',
            tool,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            0,
            0,
            0,
            angle,
            oscillations,
            exp_time,
            step,
            final_angle)

    def setplateangle(self, tool, toolcal, angle):
        if self.model is MODEL_ISARA:
            raise Exception(
                'setplateangle command not available for ISARA Sample Changer')
        return self.trajectory(
            'setplateangle',
            tool,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            toolcal,
            0,
            0,
            0,
            angle)

    def settool(self, puck_lid, sample, type):
        return self.trajectory('settool', puck_lid, sample, type)

    def settool2(self, puck_lid, sample, type):
        return self.trajectory('settool2', puck_lid, sample, type)

    # GOTODIF ALREADY DEFINED FOR PINS!!!!
    # def gotodif(self, tool, plate, well, type, toolcal):
    # return self.trajectory('gotodif',tool, 0, 0, 0, 0, plate, well, type, 0,
    # toolcal)

    # 3.6.5.4 Virtual Inputs

    def vdi9xon(self, input): return self.operate('vdi%don' % input)

    def vdi9xoff(self, input): return self.operate('vdi%doff' % input)

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

    def opentool2(self): return self.operate('opentool2')

    def closetool2(self): return self.operate('closetool2')

    def magneton(self): return self.operate('magneton')

    def magnetoff(self): return self.operate('magnetoff')

    def heateron(self): return self.operate('heateron')

    def heateroff(self): return self.operate('heateroff')

    def initdew1(self): return self.operate('initdew1')

    def initdew2(self): return self.operate('initdew2')

    def onestaticdw(self): return self.operate('1staticdw')

    def tworotatingdw(self): return self.operate('2rotatingdw')

    def openlid(self): return self.operate('openlid')

    def closelid(self): return self.operate('closelid')

    def clearbcrd(self): return self.operate('clearbcrd')

    def remotespeedon(self): return self.operate('remotespeedon')

    def remotespeedoff(self): return self.operate('remotespeedoff')

    def speedup(self): return self.operate('speedup')

    def speeddown(self): return self.operate('speeddown')

    # These 3 methods are not in the official documentation (ALBA specific)
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

    def di2(self): return self.monitor('di2')

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

        if self.model is MODEL_ISARA:
            di2_ans = self.di2()

        position_ans = self.position()
        message_ans = self.message()
        status_dict = {}

        # State
        state_values = state_ans[state_ans.find('(') + 1:-1].split(',')
        for i, v in enumerate(state_values):
            key = state_params[i]
            # Make flags boolean :-D
            if key.endswith('_1_0'):
                v = v == '1'
            # Make numbers integer :-D
            elif key in ['LID_NUM_SAMPLE_MOUNTED_ON_TOOL',
                         'NUM_SAMPLE_ON_TOOL',
                         'LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER',
                         'NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER',
                         'NUM_OF_PLATE_ON_TOOL',
                         'WELL_NUM',
                         'PUCK_DET_RESULT_DEW1',
                         'PUCK_DET_RESULT_DEW2',
                         'POSITION_NUM_DEW1',
                         'POSITION_NUM_DEW2',
                         'PUCK_NUM_SAMPLE_MOUNTED_ON_TOOL2',
                         'NUM_SAMPLE_ON_TOOL2',
                         'CURR_NUM_SOAKING',
                         'PUCK_TYPE_LID1',
                         'PUCK_TYPE_LID2',
                         'PUCK_TYPE_LID3']:
                if v == '':
                    v = -1
                else:
                    v = int(v)
            elif key == 'ROBOT_SPEED_RATIO':
                v = float(v)

            if self.model is MODEL_ISARA and key == 'LID_NUM_SAMPLE_MOUNTED_ON_TOOL':
                status_dict['PUCK_NUM_SAMPLE_MOUNTED_ON_TOOL'] = v
            elif self.model is MODEL_ISARA and key == 'LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER':
                status_dict['PUCK_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER'] = v
            status_dict[key] = v

        # DI
        di_str = di_ans[di_ans.find('(') + 1:-1]
        di_values = [x == '1' for x in di_str]

        if self.model is MODEL_ISARA:
            pars = di_params_isara
        else:
            pars = di_params

        for i, v in enumerate(di_values):
            key = pars[i]
            if key != '.':
                status_dict[key] = v

        # DO
        do_str = do_ans[do_ans.find('(') + 1:-1]
        do_values = [x == '1' for x in do_str]
        for i, v in enumerate(do_values):
            key = do_params[i]
            if key != '.':
                status_dict[key] = v

        # POSITION
        position_values = position_ans[position_ans.find(
            '(') + 1:-1].split(',')
        for i, v in enumerate(position_values):
            key = position_params[i]
            status_dict[key] = float(v)

        # MESSAGE
        status_dict['MESSAGE'] = message_ans

        # DETERMINE CASETTE PRESENCE INFO
        if self.model is MODEL_ISARA:
            try:
                di2_ans = di2_ans[4:-1]  # remove di2( and final ) from answer
                if len(di2_ans) != len(self.puck_types):
                    self.puck_presence = [False, ] * len(self.nb_pucks)
                else:
                    self.puck_presence = list(
                        map(bool, [int(ch) for ch in di2_ans]))
            except BaseException:
                self.puck_presence = [False, ] * len(self.nb_pucks)
        else:
            self.puck_presence = [False, ] * self.nb_pucks
            for i in range(self.nb_pucks):
                st_key = "CASSETTE_%d_PRESENCE" % (i + 1)
                self.puck_presence[i] = status_dict[st_key]

        is_running = status_dict['PATH_RUNNING_1_0']

        if is_running and not self.pathinfo['running']:
            # new path started
            # save current sample on diffr (for recovery purposes)
            self.sample_before_path = status_dict["NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER"]
            if self.model is MODEL_ISARA:
                self.puck_before_path = status_dict["PUCK_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER"]
            else:
                self.lid_before_path = status_dict["LID_NUM_SAMPLE_MOUNTED_ON_DIFFRACTOMETER"]
            self.latest_path = status_dict["PATH_NAME"]

        self.pathinfo['idle'] = status_dict['PRO5_IDL']
        self.pathinfo['home'] = status_dict['PRO6_RAH']
        self.pathinfo['in_area1'] = status_dict['PRO7_RI1']
        self.pathinfo['in_area2'] = status_dict['PRO8_RI2']
        self.is_som = status_dict['PRI_SOM']
        self.is_idle = status_dict['PRO5_IDL']

        self.current_tool = status_dict['TOOL_NUM_OR_NAME']

        if self.executing_recovery:
            self.pathinfo['running'] = True
            self.pathinfo['pathname'] = "recovery"
        else:
            self.pathinfo['running'] = is_running
            self.pathinfo['pathname'] = status_dict['PATH_NAME']

        self.pathinfo['double_gripper'] = (
            self.current_tool.strip().lower() == 'double')
        self.pathinfo['safe'] = self.pathInSafeArea()

        self.check_recovery_needed()

        if self.executing_recovery:
            self.follow_recovery_process()

        if self.pathinfo['running']:
            print((
                "path running   '%(double_gripper)s %(pathname)8s / idle=%(idle)s / home=%(home)s / ri1=%(in_area1)s / ri2 = %(in_area2)s / safe = %(safe)s'" %
                self.pathinfo))

        return status_dict

    def check_recovery_needed(self):
            # if command being executed is of type "get" and
        if self.ri1_count == 1 and self.pathinfo['pathname'] in self.check_paths_get:
            if self.is_som:
                self.recovery_type = RECOVER_GET_FAILED
                self._is_recovery_needed = True
                self.warn("RECOVER_GET_FAILED needed!")
                return

        self._is_recovery_needed = False
        return False

    def is_recovery_needed(self):
        return self._is_recovery_needed

    def get_last_command_sent(self):
        return self._last_command_sent

    def start_recovery(self):
        if not self._is_recovery_needed:
            return "nothing done"

        self.executing_recovery = True
        self.recovery_phase = 0
        return "started"

    def follow_recovery_process(self):
        if self.recovery_type == RECOVER_GET_FAILED:
                #
            if self.recovery_phase == 0:
                # abort
                self.abort()
                self.warn("Recovering from GET_FAILED. Phase0 (abort)")
                self.recovery_phase = 1
            elif self.recovery_phase == 1:
                self.warn("Recovering from GET_FAILED. Phase1 (waiting abort)")
                # waiting abort to finish
                if self.is_idle:
                    self.recovery_phase = 2
            elif self.recovery_phase == 2:
                # restore sample info on diff
                if self.model is MODEL_ISARA:
                    puck_lid = self.puck_before_path
                else:
                    puck_lid = self.lid_before_path
                sample = self.sample_before_path
                # get the type of sample from lid and cassette type if not ISARA
                sample_type = 0
                if not MODEL_ISARA:
                    # Get type by lid [2,2,2,1,1,1,2,2,2] -> [2,1,2]
                    sample_type_by_lid = self.get_puck_types()[0::3]
                    # Map spine/unipuck definitions:
                    # IRELEC-CATS server: 0-spine/1-unipuck
                    # PyCATS TANGO: 1-spine/2-unipuck (cassette_type)
                    sample_type = sample_type_by_lid[puck_lid - 1] - 1
                self.warn(
                    "Recovering from GET_FAILED. Phase2 (setondiff %s, %s, %s)" %
                    (puck_lid, sample, sample_type))
                self.setondiff(puck_lid, sample, sample_type)
                # home
                self.home(2)
                self.recovery_phase = 3
            else:
                self.warn("recovering from GET_FAILED. Phase3 (end recovery)")
                self.executing_recovery = False

    def pathInSafeArea(self):

        if not self.pathinfo['running']:
            self.is_running = False
            self.is_safe = True
            self.ri1_count = 0
            self.ri2_count = 0
            self.is_inr1 = False
            self.is_inr2 = False
            return

        if self.pathinfo['running'] and self.is_running is False:
            self.is_running = True

            if self.pathinfo['pathname'] not in self.check_paths_all:
                self.is_safe = True
            else:
                self.is_safe = False
                self.ri1_count = 0
                self.ri2_count = 0
                self.is_inr1 = False
                self.is_inr2 = False

        if self.pathinfo['pathname'] not in self.check_paths_all:
            return self.is_safe

        # area1 became True
        if self.pathinfo['in_area1'] and not self.is_inr1:
            self.is_inr1 = True

        # area1 became False
        if not self.pathinfo['in_area1'] and self.is_inr1:
            self.ri1_count += 1
            self.is_inr1 = False

        # area2 became True
        if self.pathinfo['in_area2'] and not self.is_inr2:
            self.is_inr2 = True

        # area2 became False
        if not self.pathinfo['in_area2'] and self.is_inr2:
            self.ri2_count += 1
            self.is_inr2 = False

            if self.pathinfo['double_gripper']:
                if self.ri2_count > 0:
                    self.is_safe = True
            elif self.pathinfo['pathname'] in self.check_paths_grp1:
                if self.ri2_count > 0:
                    self.is_safe = True
            elif self.pathinfo['pathname'] in self.check_paths_grp2:
                if self.ri2_count > 1:
                    self.is_safe = True

        return self.is_safe


######################################################
# Just for testing
if __name__ == '__main__':
    import time
    cs8 = CS8Connection()
    cs8.connect('bl13cats.cells.es', 1000, 10000)

    print('1) Check monitoring')
    print(cs8.state())
    print(cs8.di())
    print(cs8.do())
    print(cs8.position())
    print(cs8.message())
    #
    # print
    # print '2) Check operation'
    # print cs8.di()
    # print cs8.openlid1()
    # time.sleep(4)
    # print cs8.di()
    # print cs8.closelid1()
    # time.sleep(4)
    # print cs8.di()
