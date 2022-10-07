pid_Linelist = PIDCtrl()
list_Lines = RmList()
list_markers = RmList()
variable_X = 0
variable_state = 0
variable_speed = 0
variable_heart = 0
def user_defined_run():
    global variable_X
    global variable_state
    global variable_speed
    global variable_heart
    global list_Lines
    global list_markers
    global pid_Linelist
    list_Lines=RmList(vision_ctrl.get_line_detection_info())
    if len(list_Lines) == 42 and list_Lines[2] >= 1:
        variable_X = list_Lines[19]
        pid_Linelist.set_error(variable_X - 0.5)
        gimbal_ctrl.rotate_with_speed(pid_Linelist.get_output(),0)
        chassis_ctrl.set_trans_speed(variable_speed)
        chassis_ctrl.move(0)
    else:
        gimbal_ctrl.rotate_with_speed(0,0)
        chassis_ctrl.set_trans_speed(0)
        chassis_ctrl.move(0)
def start():
    global variable_X
    global variable_state
    global variable_speed
    global variable_heart
    global list_Lines
    global list_markers
    global pid_Linelist
    robot_ctrl.set_mode(rm_define.robot_mode_chassis_follow)
    gimbal_ctrl.rotate_with_degree(rm_define.gimbal_down,20)
    vision_ctrl.enable_detection(rm_define.vision_detection_line)
    vision_ctrl.line_follow_color_set(rm_define.line_follow_color_blue)
    pid_Linelist.set_ctrl_params(330,0,28)
    variable_state = 1
    variable_speed = 0.1
    while not variable_state == 0:
        while not (sensor_adapter_ctrl.get_sensor_adapter_adc(1, 2) < 200 or sensor_adapter_ctrl.get_sensor_adapter_adc(2, 1) > 600 or (sensor_adapter_ctrl.check_condition(rm_define.cond_sensor_adapter1_port1_high_event))):
            user_defined_run()

        gimbal_ctrl.rotate_with_speed(0,0)
        chassis_ctrl.set_trans_speed(0)
        chassis_ctrl.move(0)
        time.sleep(1)
        if sensor_adapter_ctrl.get_sensor_adapter_adc(1, 2) < 200 or sensor_adapter_ctrl.get_sensor_adapter_adc(2, 1) > 600 or (sensor_adapter_ctrl.check_condition(rm_define.cond_sensor_adapter1_port1_high_event)):
            variable_state = 0
    if variable_state == 0:
        led_ctrl.set_flash(rm_define.armor_all, 2)
        variable_speed = 0.2
        vision_ctrl.enable_detection(rm_define.vision_detection_marker)
        vision_ctrl.set_marker_detection_distance(0.5)
    while not (vision_ctrl.check_condition(rm_define.cond_recognized_marker_trans_red_heart)):
        user_defined_run()

    gimbal_ctrl.rotate_with_speed(0,0)
    chassis_ctrl.set_trans_speed(0)
    chassis_ctrl.move(0)
