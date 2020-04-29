#!/usr/bin/env python
import sys
import datetime
import click

from PyQt5.QtWidgets import (QVBoxLayout, QGridLayout, QLabel, QFrame,
                             QDoubleSpinBox, QLineEdit, QCheckBox, QScrollArea,
                             QApplication, QTextEdit)
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, QSize
from tango import DeviceProxy

from ..core import di_params, do_params, state_params, position_params
from ..help import di_help, do_help, message_help


class CS8State(QObject):

    paramChanged = pyqtSignal('QString')

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.state = []
        for v in state_params:
            if v.endswith('NAME'):
                # IT IS A 'STRING' VALUE
                self.state.append('a_name')
            elif v.endswith('1_0'):
                # IT IS A BOOLEAN VALUE, BUT WE PUT 0/1
                self.state.append('0')
            else:
                # IT IS A NUMBER VALUE, AND WE WILL PUT A 0
                self.state.append('0')
        self.di = []
        for v in di_params:
            self.di.append('0')
        self.do = []
        for v in do_params:
            self.do.append('0')
        self.position = []
        for v in position_params:
            self.position.append('0')
        self.message = 'No message here...'

    def get(self, param):
        index, values = self.get_index_and_values(param)
        if values is not None:
            return values[index]
        elif param == 'message':
            return self.message
        else:
            return None

    def set(self, param, value):
        index, values = self.get_index_and_values(param)
        if values is not None:
            previous_value = values[index]
            values[index] = value
            if previous_value != value:
                self.paramChanged.emit(str(param))
        if param == 'message':
            prev_message = self.message
            self.message = value
            if prev_message != self.message:
                self.paramChanged.emit(str(param))

    def set_values(self, params_list, values):
        for i in range(len(params_list)):
            p = params_list[i]
            if p != '.':
                self.set(p, values[i])

    def get_index_and_values(self, param):
        if param in state_params:
            index = state_params.index(param)
            return (index, self.state)
        elif param in di_params:
            index = di_params.index(param)
            return (index, self.di)
        elif param in do_params:
            index = do_params.index(param)
            return (index, self.do)
        elif param in position_params:
            index = position_params.index(param)
            return (index, self.position)

        return (None, None)

    def getMessageHelp(self, message):
        if message not in message_help:
            return None
        return message_help[message]


class CS8_Panel(QFrame):
    """ """

    def __init__(self, parent=None, cs8=None):
        """ """
        QFrame.__init__(self, parent)
        self.cs8 = cs8

        self.widget_controllers = {}
        self.build_contents()
        self.setMinimumSize(QSize(1180, 700))
        self.cs8.paramChanged.connect(self.paramChanged)

    @pyqtSlot('QString')
    def paramChanged(self, param):
        param = str(param)
        controller = self.widget_controllers[param]
        value = self.cs8.get(param)
        if param == 'message':
            value = value.replace('\r', '')
            # value CAN BE EXTENDED WITH 'WHY' AND 'WHAT'
            message_help = self.cs8.getMessageHelp(value)
            if message_help is not None:
                why = message_help[0]
                what = message_help[1]
                value = '%s WHY:%s WHAT:%s' % (value, why, what)
        controller.valueChanged(value)
        # UPDATE LOG AREA WITH INFO
        timestamp = datetime.datetime.now().strftime('%Y/%m/%d_%H:%M:%S')
        value_str = str(value)
        log_message = "%s: %s <--- %s" % (timestamp, param, value_str)

        if param in di_params:
            param_help = di_help[param]
            help_str = '\t(0: "%s" 1: "%s")' % (param_help[0], param_help[1])
            log_message += help_str
        elif param in do_params:
            param_help = do_help[param]
            help_str = '\t(0: "%s" 1: "%s")' % (param_help[0], param_help[1])
            log_message += help_str

        # WE WILL IGNORE SOME PARAMETERS
        ignored_params = ['LIFE_BIT_COMING_FROM_PLC']
        ignored_params += position_params
        if param not in ignored_params:
            self.log.append(log_message)

    def build_contents(self):
        """Initialize all the ui components."""
        # self.setLayout(QGridLayout())
        # self.layout().setContentsMargins(0,0,0,0)
        self.setLayout(QVBoxLayout())

        # --- POSITION ---
        position_frame = QFrame()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        position_frame.setLayout(grid_layout)
        col = 0
        for p in position_params:
            if p != '.':
                value = self.cs8.get(p)
                label_text = p
                label = QLabel(label_text)
                label.font().setPointSize(8)
                widget = QDoubleSpinBox()
                widget.setFixedWidth(100)
                widget.setMinimum(-99999)
                widget.setMaximum(99999)
                widget.setValue(float(value))
                controller = WidgetController(self, p, widget)
                widget.setEnabled(False)
                grid_layout.addWidget(label, 0, col)
                grid_layout.addWidget(widget, 1, col)
                col += 1
                self.widget_controllers[p] = controller
        # self.layout().addWidget(position_frame,0,0)
        self.layout().addWidget(position_frame)

        # --- STATE ---
        state_frame = QFrame()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        state_frame.setLayout(grid_layout)
        row = 0
        col = 0
        for p in state_params:
            value = self.cs8.get(p)
            label_text = None
            if len(p) < 30:
                label_text = p
            elif len(p) < 50:
                label_text = p[:25] + '\n' + p[25:]
            elif len(p) < 75:
                label_text = p[:25] + '\n' + p[25:50] + '\n' + p[50:]
            elif len(p) < 100:
                label_text = p[:25] + '\n' + p[25:50] + \
                    '\n' + p[50:75] + '\n' + p[75:]
            label = QLabel(label_text)
            label.font().setPointSize(8)
            controller = None

            if p.endswith('NAME'):
                widget = QLineEdit()
                widget.setFixedWidth(100)
                controller = WidgetController(self, p, widget)
                widget.setEnabled(False)
            elif p.endswith('1_0'):
                # It is a boolean flag
                widget = QCheckBox()
                widget.setFixedSize(15, 15)
                checked = (value == '1')
                widget.setChecked(checked)
                controller = WidgetController(self, p, widget)
                widget.setEnabled(False)
            else:
                widget = QDoubleSpinBox()
                widget.setFixedWidth(100)
                widget.setMinimum(-99999.0)
                widget.setMaximum(99999.0)
                widget.setValue(float(value))
                controller = WidgetController(self, p, widget)
                widget.setEnabled(False)
            grid_layout.addWidget(label, row, col)
            grid_layout.addWidget(widget, row, col + 1)
            col += 2
            if col == 8:
                col = 0
                row += 1
            self.widget_controllers[p] = controller
        state_sa = QScrollArea(self)
        state_sa.setWidget(state_frame)
        state_label = QLabel('State')
        # self.layout().addWidget(state_sa,1,0)
        self.layout().addWidget(state_sa)

        # --- DI ---
        di_frame = QFrame()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        di_frame.setLayout(grid_layout)
        row = 0
        col = 0
        for p in di_params:
            if p != '.':
                value = self.cs8.get(p)
                label_text = p
                label = QLabel(label_text)
                label.font().setPointSize(8)
                if label_text.startswith('PRI'):
                    label.font().setBold(True)
                widget = QCheckBox()
                widget.setFixedSize(15, 15)
                checked = (value == '1')
                widget.setChecked(checked)
                param_help = di_help[p]
                tooltip = 'Unchecked: %s\nChecked: %s' % (
                    param_help[0], param_help[1])
                widget.setToolTip(tooltip)
                label.setToolTip(tooltip)
                controller = WidgetController(self, p, widget)
                widget.setEnabled(False)
                di_frame.layout().addWidget(widget, row, col)
                di_frame.layout().addWidget(label, row, col + 1)
                col += 2
                if col == 12:
                    col = 0
                    row += 1
                self.widget_controllers[p] = controller

        di_sa = QScrollArea(self)
        di_sa.setWidget(di_frame)
        di_label = QLabel('Digital Inputs')
        # self.layout().addWidget(di_sa,2,0)
        self.layout().addWidget(di_sa)

        # --- DO ---
        do_frame = QFrame()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        do_frame.setLayout(grid_layout)
        row = 0
        col = 0
        for p in do_params:
            if p != '.':
                value = self.cs8.get(p)
                label_text = p
                label = QLabel(label_text)
                label.font().setPointSize(8)
                # 01/06/2011 JJ requirement, for USED PROs, set it bold
                if label_text.startswith(
                        'PRO') and not label_text.startswith('PROCESS'):
                    label.font().setBold(True)
                widget = QCheckBox()
                widget.setFixedSize(15, 15)
                checked = (value == '1')
                widget.setChecked(checked)
                param_help = do_help[p]
                tooltip = 'Unchecked: %s\nChecked: %s' % (
                    param_help[0], param_help[1])
                widget.setToolTip(tooltip)
                label.setToolTip(tooltip)
                controller = WidgetController(self, p, widget)
                widget.setEnabled(False)
                grid_layout.addWidget(widget, row, col)
                grid_layout.addWidget(label, row, col + 1)
                col += 2
                if col == 14:
                    col = 0
                    row += 1
                self.widget_controllers[p] = controller
        do_sa = QScrollArea(self)
        do_sa.setWidget(do_frame)
        do_label = QLabel('Digital Outputs')
        # self.layout().addWidget(do_sa,3,0)
        self.layout().addWidget(do_sa)

        # --- LOG ---
        self.log = QTextEdit()
        # self.layout().addWidget(self.log,4,0)
        self.layout().addWidget(self.log)

        # --- STATUS MESSAGE ---
        self.msg_lbl = QLabel()
        p = 'message'
        controller = WidgetController(self, p, self.msg_lbl)
        self.widget_controllers[p] = controller
        # self.layout().addWidget(self.msg_lbl,5,0)
        self.layout().addWidget(self.msg_lbl)


class WidgetController:
    def __init__(self, parent, param, widget):
        self.parent = parent
        self.param = param
        self.widget = widget
        self.reset_stylesheet_timer = None

    def valueChanged(self, value):
        if isinstance(self.widget, QCheckBox):
            flag = (int(value) == 1)
            self.widget.setChecked(flag)
            widget_class = 'QCheckBox'
        elif isinstance(self.widget, QLineEdit):
            self.widget.setText(value)
            widget_class = 'QLineEdit'
        elif isinstance(self.widget, QDoubleSpinBox):
            if value == '' or value is None:
                value = 'nan'
            self.widget.setValue(float(value))
            widget_class = 'QDoubleSpinBox'
        elif isinstance(self.widget, QLabel):
            self.widget.setText(value)
            widget_class = 'QLabel'
        else:
            return
        if self.param == 'LIFE_BIT_COMING_FROM_PLC':
            return
        self.widget.setStyleSheet(
            '%s { background-color: yellow }' %
            widget_class)
        if self.reset_stylesheet_timer is not None:
            self.reset_stylesheet_timer.timeout.disconnect(self.resetStyleSheet)
        self.reset_stylesheet_timer = QTimer(self.parent)
        self.reset_stylesheet_timer.setSingleShot(True)
        self.reset_stylesheet_timer.timeout.connect(self.resetStyleSheet)
        self.reset_stylesheet_timer.start(10000)

    def resetStyleSheet(self):
        self.widget.setStyleSheet('')
        self.reset_stylesheet_timer.timeout.disconnect(self.resetStyleSheet)


class MonitorCS8(QApplication):
    def __init__(self, *args, device=None):
        QApplication.__init__(self, *args)
        self.cs8 = CS8State()
        cs8_panel = CS8_Panel(cs8=self.cs8)
        cs8_panel.setWindowTitle('CS8 Monitoring')
        cs8_panel.show()
        if not device:
            sys.exit()
        self.cats_dev = DeviceProxy(device)

        update_timer = QTimer()
        update_timer.timeout.connect(self.update_status)
        update_timer.start(500)
        sys.exit(self.exec_())

    def update_status(self):
        try:
            ans = self.cats_dev.mon_state()
            state_values = ans[ans.find('(') + 1:ans.find(')')].split(',')
            self.cs8.set_values(state_params, state_values)

            ans = self.cats_dev.mon_di()
            di_values = list(ans[ans.find('(') + 1:ans.find(')')])
            self.cs8.set_values(di_params, di_values)

            ans = self.cats_dev.mon_do()
            do_values = list(ans[ans.find('(') + 1:ans.find(')')])
            self.cs8.set_values(do_params, do_values)

            ans = self.cats_dev.mon_position()
            position_values = ans[ans.find('(') + 1:ans.find(')')].split(',')
            self.cs8.set_values(position_params, position_values)

            message = self.cats_dev.mon_message()
            self.cs8.set('message', message)

        except Exception as e:
            print('Oups, some error updating state:\n', e)
            import traceback
            traceback.print_exc()


@click.command()
@click.option('--device',
              type=click.STRING,
              prompt='CATS Tango device name',
              help='The Tango device name for the CATS')
def run(device):
    app = MonitorCS8(sys.argv, device=device)


if __name__ == '__main__':
    run()
