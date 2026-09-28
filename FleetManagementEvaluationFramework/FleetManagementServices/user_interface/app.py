import datetime
import json
import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import log_config.log

from api.api_config import set_service_urls
from api.client_api import send_new_order_info, get_system_time, \
    add_amr_basedatamanagement_api, add_amr_systemdatamanagement_api, add_amr_simulation_api, set_amr_to_pause_sim_api, \
    set_amr_to_pause_system_api, get_make_span_api, set_dispatching_strategy_api, set_path_planning_strategy_api, \
    set_collision_detection_api, reset_order_management, reset_amr_simulation, reset_system_state_management, \
    reset_base_data_management, reset_task_assignment, reset_cpu_time_measurement, get_computational_time, \
    send_new_order_info_to_simulation, run_simulation_step, \
    set_dispatching_strategy_in_system_state_management, \
    set_dispatching_strategy_in_amr_simulation, visualize_full_mapd_scenario, \
    set_system_time_from_extern_in_system_state_management, set_system_time_from_extern_in_amr_simulation
import config.config_file
from data.enums import OrderStatus
from data.models import Dimension, NewOrderInfo, NewAMRSystemRequest, \
    NewAMRRequest, LoadDimension, AMRPauseRequest, MakeSpanRequest, DispatchingStrategy, PathPlanningStrategy, \
    CollisionDetection, SystemTimeResponse
from logic.get_dataframe_functions import get_amr_df, get_df_single_amr, \
    get_orders_df_with_computed_start_and_end_times
from logic.get_info_functions import get_amr_list, get_next_order_id, get_node_and_stations_list, get_next_amr_id, \
    get_order_id_list, get_amr_list_for_map, check_all_orders_finish
from logic.reset_storage_location_tracking_functions import reset_storage_location_tracking
from figures.map_figures import create_map_figure_hovering
from logic.general_functions import get_order_span, transform_str_to_datetime
import config.config_file
from logic.set_microservice_input_data import set_lif_object_from_file_in_travel_time_service, \
    create_system_state_and_base_state_object_from_file, send_system_state_objects, create_system_state_object_from_file

if "enable_refresh" not in st.session_state:
    st.session_state.enable_refresh = False  # Normally true
if st.session_state.enable_refresh:
    count = st_autorefresh(interval=1000, key="refresh_key")

logger = log_config.log.set_logger(config.config_file.LOGGER_NAME)

class Dashboard:
    def start_dashboard(self):
        """
        :return: method to create a streamlit dashboard for FlexTools, this means an user interface
                 for the fleet management system for amr
        """
        st.sidebar.image('./images/flextools.png', use_column_width=True)
        st.sidebar.markdown("# *:green[Fleet-Management UI]*")
        st.sidebar.markdown("## Overview:")

        label_select_box1 = "Which topic: "
        select_box1 = st.sidebar.selectbox(label_select_box1, ('Orders', 'AMRs', 'Configurations'))

        if select_box1 == 'Orders':  # Orders main overview page
            col1, col2 = st.columns([9, 1])
            with col2:
                st.image('./images/FZI_Logo-Vektor.svg', use_column_width=True)
            st.markdown("## :green[Orders Overview]")

            st.table(get_orders_df_with_computed_start_and_end_times())
            button1 = st.button(label="Add new order")
            if button1:
                st.session_state.enable_refresh = False
                st.session_state.show_add_new_order = True
                st.rerun()
            if st.session_state.get("show_add_new_order", False):
                self.__add_new_order()

            order_id_start, order_id_end = get_order_span()
            if order_id_start is not None and order_id_end is not None and order_id_start < order_id_end:
                col1, col2 = st.columns(2)
                with col1:
                    order_span = st.slider(label='Compute Makespan:', min_value=order_id_start,
                                           max_value=order_id_end, value=[order_id_start, order_id_end], step=1)
                with col2:
                    button_get_makespan = st.button(label='Compute Makespan')
                if button_get_makespan:
                    makespan_request = MakeSpanRequest(earliestOrderId= str(order_span[0]),
                                                       latestOrderId=str(order_span[1]))
                    makespan_response = get_make_span_api(makespan_request).json()
                    m, s = divmod(makespan_response['time'], 60)
                    h, m = divmod(m, 60)
                    st.text(str('Makespan = ' + str(h) + ' Hours ' + str(m) + ' Minutes ' + str(s) + ' Seconds'))
                    comp_time_response = get_computational_time().json()
                    st.text(str('Computational time for path planning ' + comp_time_response['compTime'].replace('PT',
                                                                                                                  '')
                            [0:7] + ' seconds'))
                button_visualize_sim = st.button(label='Visualization Scenario')
                st.session_state['run_visualization'] = button_visualize_sim
                if st.session_state.get('run_visualization', False):
                    if 'layout' in st.session_state:
                        visualize_full_mapd_scenario(st.session_state['layout'])
                    st.session_state['run_visualization'] = False

        elif select_box1 == 'AMRs':  # AMRs main page
            label_select_box2 = "Option: "
            select_box2 = st.sidebar.selectbox(label_select_box2, ('Total AMR Overview', 'Single AMR Data'))
            if select_box2 == 'Total AMR Overview':
                col1, col2 = st.columns([9, 1])
                with col2:
                    st.image('./images/FZI_Logo-Vektor.svg', use_column_width=True)

                st.markdown("## :green[AMR / Map Overview]")
                col1, col2, col3 = st.columns(3)
                with col1:
                    amr_id_list = get_amr_list_for_map()
                    if 'select_amr_map' not in st.session_state:
                        st.session_state['select_amr_map'] = 0
                    select_box_amr = st.selectbox(label='AMRs:', options=amr_id_list,
                                                  index=st.session_state['select_amr_map'])
                    st.session_state['select_amr_map'] = amr_id_list.index(select_box_amr)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if 'current_paths' not in st.session_state:
                        st.session_state['current_paths'] = False
                    current_paths = st.checkbox(label="Current planned paths", value=st.session_state['current_paths'])
                    st.session_state['current_paths'] = current_paths
                with col2:
                    if 'previous_paths' not in st.session_state:
                        st.session_state['previous_paths'] = False
                    previous_paths = st.checkbox(label="Previous paths", value=st.session_state['previous_paths'])
                    st.session_state['previous_paths'] = previous_paths
                with col3:
                    if 'future_orders' not in st.session_state:
                        st.session_state['future_orders'] = False
                    future_orders = st.checkbox(label="Future orders", value=st.session_state['future_orders'])
                    st.session_state['future_orders'] = future_orders
                map_fig = create_map_figure_hovering(st.session_state['previous_paths'],
                                                     st.session_state['current_paths'],
                                                     str(st.session_state['select_amr_map']),
                                                     st.session_state['future_orders'])
                if map_fig is not None:
                    fig = st.plotly_chart(map_fig)
                disable_add = False
                if map_fig is None:
                    disable_add = True

                amr_table = st.table(get_amr_df())
                button3 = st.button(label="Add new AMR", disabled=disable_add)

                if button3:
                    st.session_state.enable_refresh = False
                    st.session_state.show_add_new_amr = True
                    st.rerun()
                if st.session_state.get("show_add_new_amr", False):
                    self.__add_new_amr()

            elif select_box2 == 'Single AMR Data':  # Single AMR data page
                label_select_box3 = "Which AMR: "
                amr_list = get_amr_list()
                select_box3 = st.sidebar.selectbox(label_select_box3, amr_list)
                # Page single AMR
                col1, col2 = st.columns([9, 1])
                with col2:
                    st.image('./images/FZI_Logo-Vektor.svg', use_column_width=True)
                if select_box3 is not None:
                    st.markdown(f"## :green[Overview of {select_box3}:]")
                    df_single_amr, df_actions, battery_charge, charging, reach, df_planned_order\
                        = get_df_single_amr(select_box3)
                    single_amr_table = st.table(df_single_amr)
                    st.markdown(f"### Action Overview of Current Order:")
                    actions_table = st.table(df_actions)
                    st.markdown(f"### Battery State Overview:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.progress(value=battery_charge, text=f'Battery charge: {battery_charge} %')
                    with col2:
                        if charging is True:
                            st.markdown(':green[Battery is charging]')
                        else:
                            st.markdown(':orange[Battery is not charging]')
                    with col3:
                        st.markdown(f'Remaining distance: {reach} m')

                    st.markdown(f"### Next Orders:")
                    planned_order_table = st.table(df_planned_order)
                    if df_single_amr['Pause'][0] == 'False':
                        label_button_4 = f"Start Pause {select_box3}"
                    else:
                        label_button_4 = f"End Pause {select_box3}"
                    button4 = st.button(label=label_button_4)
                    if button4:
                        if label_button_4 == f"Start Pause {select_box3}":
                            amr_pause_request = AMRPauseRequest(amrId=select_box3.replace('AMR ', ''), pause=True)
                            st.info(f'{select_box3} still executes all scheduled orders and does not accept any new orders'
                                    f' until the pause mode is ended', icon="ℹ️")
                        else:
                            amr_pause_request = AMRPauseRequest(amrId=select_box3.replace('AMR ', ''), pause=False)
                        set_amr_to_pause_sim_api(amr_pause_request)
                        set_amr_to_pause_system_api(amr_pause_request)
        elif select_box1 == 'Configurations':  # Configuration page
            col1, col2 = st.columns([9, 1])
            with col2:
                st.image('./images/FZI_Logo-Vektor.svg', use_column_width=True)
            st.markdown(f"## :green[Fleet-Management Configurations:]")
            st.markdown(f"### Select Scenario with Orders:")
            uploaded_file = st.file_uploader("Select a json file with multiple orders for planning:",
                                             accept_multiple_files=False, type=['json'])
            button2 = st.button(label="Plan orders from uploaded file")
            if button2:
                if uploaded_file is not None:
                    self.__add_orders_from_json_file(uploaded_file)
            st.divider()
            st.markdown(f"### Task Assignment Strategy:")
            dispatching_options = ['Push-Back', 'Greedy', 'Token-Passing', 'Greedy-Completion-Time', 'Central']
            if 'dispatching_strategy' not in st.session_state:
                st.session_state['dispatching_strategy'] = 0
            select_box_dispatching = st.selectbox(label='Task Assignment Strategy',
                                                  options=dispatching_options,
                                                  index=st.session_state['dispatching_strategy'])
            st.session_state['dispatching_strategy'] = dispatching_options.index(select_box_dispatching)
            if select_box_dispatching == 'Greedy':
                if 'use_improvement' not in st.session_state:
                    st.session_state['use_improvement'] = True
                improvement_dispatching = st.checkbox(label='Use 2-opt for improve strategy',
                                                      value=st.session_state['use_improvement'])
                st.session_state['use_improvement'] = improvement_dispatching
            else:
                improvement_dispatching = None
            st.markdown(f"### Path-Planning Strategy:")
            if 'pathplanning_strategy' not in st.session_state:
                st.session_state['pathplanning_strategy'] = 0

            path_planning_dict = {'Push-Back': ['Dijkstra'], 'Greedy': ['Dijkstra'],
                                  'Greedy-Completion-Time': ['Dijkstra'],
                                  'Token-Passing': ['Cooperative_A_Star'], 'Central': ['CBS', 'ECBS',
                                                                                       'CBS_DJS', 'ECBS_DJS',
                                                                                       'I_CBS', 'I_ECBS']}
            # path_planning_options = ['Dijkstra', 'Cooperative_A_Star', 'CBS', 'ECBS', 'CBS_DJS', 'ECBS_DJS',
            #                          'Interval_CBS']
            select_box_path_planning = st.selectbox(label='Path-Planning strategy',
                                                    options=path_planning_dict[select_box_dispatching],
                                                    index=st.session_state['pathplanning_strategy'],
                                                    disabled=False)
            st.session_state['pathplanning_strategy'] = path_planning_dict[select_box_dispatching].index(select_box_path_planning)
            if select_box_path_planning == 'ECBS' or select_box_path_planning == 'ECBS_DJS':
                if 'omega' not in st.session_state:
                    st.session_state['omega'] = 1.3
                omega_ecbs = st.number_input(label='Max. Error w ECBS:', min_value=1.0, max_value=2.0,
                                             value=st.session_state['omega'], step=0.1)
                st.session_state['omega'] = omega_ecbs
            st.markdown(f"### AMR Simulation:")
            if 'consider_collisions' not in st.session_state:
                st.session_state['consider_collisions'] = True
            col1, col2 = st.columns(2)
            with col1:
                amr_simulation_collisions = st.checkbox(label='Consider collisions',
                                                        value=st.session_state['consider_collisions'])
                st.session_state['consider_collisions'] = amr_simulation_collisions
            with col2:
                st.write('<p style="font-size: 10px;">Simulation considers collisions, i.e. that each node or edge can '
                         'only be occupied by one AMR. In the other case, the AMR must wait'
                         ' until the node or edge is free.</p>',
                         unsafe_allow_html=True)
            configuration_button = st.button('Save Configurations')
            if configuration_button:
                set_dispatching_strategy_api(DispatchingStrategy(dispatchingStrategy=select_box_dispatching.lower().replace('-', '_'),
                                                                 useImprovement=improvement_dispatching))
                set_dispatching_strategy_in_system_state_management(DispatchingStrategy(
                    dispatchingStrategy=select_box_dispatching.lower().replace('-', '_')))
                set_dispatching_strategy_in_amr_simulation(DispatchingStrategy(
                    dispatchingStrategy=select_box_dispatching.lower().replace('-', '_')))
                set_collision_detection_api(CollisionDetection(collisionDetection=amr_simulation_collisions))

                path_planning_string = select_box_path_planning.lower()

                if 'omega' in st.session_state:
                    set_path_planning_strategy_api(PathPlanningStrategy(
                        pathPlanningStrategy=path_planning_string,
                        boundary=st.session_state['omega']
                    ))
                else:
                    set_path_planning_strategy_api(PathPlanningStrategy(
                        pathPlanningStrategy=path_planning_string
                    ))
            st.divider()
            st.markdown(f"### LIF File:")

            lif_file = st.file_uploader("Select a LIF file:",
                                        accept_multiple_files=False, type=['json'])
            button_lif = st.button(label="Add LIF file")
            if button_lif:
                if lif_file is not None:
                    layout_list = set_lif_object_from_file_in_travel_time_service(lif_file)
                    st.session_state['layout'] = layout_list[0]  # Work at the moment with one layout
            st.markdown(f"### System- and Base State File:")

            system_state_file = st.file_uploader("Select a system state file:",
                                                 accept_multiple_files=False, type=['json'])
            base_state_file = st.file_uploader("Select a base state file:",
                                               accept_multiple_files=False, type=['json'])

            button_system_base_state = st.button(label="Add system- and base state files")
            if button_system_base_state:
                if system_state_file is not None and base_state_file is not None:
                    system_state_objects, base_state_objects = create_system_state_and_base_state_object_from_file(
                        system_state_file, base_state_file)
                    st.session_state['system_state_object'] = system_state_objects
                    st.session_state['base_state_object'] = base_state_objects
                elif system_state_file is not None and 'base_state_object' in st.session_state:
                    system_state_objects = create_system_state_object_from_file(
                        system_state_file)
                    st.session_state['system_state_object'] = system_state_objects

                send_system_state_objects(st.session_state['system_state_object'],
                                          st.session_state['base_state_object'])

            st.divider()
            reset_button = st.button('Reset Services')
            if reset_button:
                if 'run_until_order' in st.session_state:
                    st.session_state['run_until_order'] = 0
                if config.config_file.STORAGE_LOCATION_TRACKING is True:
                    reset_storage_location_tracking()
                reset_order_management()
                reset_cpu_time_measurement()
                reset_task_assignment()
                reset_base_data_management()
                reset_amr_simulation()
                reset_system_state_management()
                if 'system_state_object' in st.session_state and 'base_state_object' in st.session_state:
                    send_system_state_objects(st.session_state['system_state_object'],
                                              st.session_state['base_state_object'])


        st.sidebar.divider()
        st.sidebar.markdown("## System Time:")
        sys_time = get_system_time().json()
        system_time = st.sidebar.markdown(str(sys_time['timestamp'])[0:19].replace('T', ' '))
        sim_run = st.sidebar.toggle("Run simulation", value=False, key='sim_run',
                                    on_change=self.run_simulation_monitoring)
        order_id_list = get_order_id_list()
        if 'run_until_order' not in st.session_state:
            st.session_state['run_until_order'] = 0
        sim_run_until_order = st.sidebar.selectbox(label='Run simulation until finish order:', options=order_id_list,
                                                   index=st.session_state['run_until_order'])
        if st.session_state['run_until_order'] != order_id_list.index(sim_run_until_order):
            st.session_state['run_until_order'] = order_id_list.index(sim_run_until_order)
        st.sidebar.divider()
        with st.sidebar:
            col1, col2 = st.columns(2)
            with col1:
                st.image('./images/flextools_förder_logo.jpg', use_column_width=True)
            with col2:
                st.markdown("Finanziert durch die Europäische Union – NextGenerationEU")


    @staticmethod
    def run_simulation_monitoring():
        if st.session_state.sim_run is True:
            order_id_list = get_order_id_list()
            run_until_order_id = order_id_list[st.session_state['run_until_order']]
            finished_percentage = -1
            all_orders_finish = False
            simulation_res = {'simulationFinish': False, 'percentageFinish': 0}
            start_time_evaluation = time.time()
            while (simulation_res['simulationFinish'] is False and st.session_state.sim_run is True and
                   all_orders_finish is False):
                try:
                    simulation_res = run_simulation_step().json()
                except Exception as e:
                    logger.exception(f'Error in simulation step {e}')
                    break
                if finished_percentage != simulation_res['percentageFinish']:
                    finished_percentage = simulation_res['percentageFinish']
                    logger.info(f'Around {finished_percentage}% of simulated orders are finished executed')
                evaluation_duration = time.time() - start_time_evaluation
                if evaluation_duration > config.config_file.MAX_EVALUATION_TIME:
                    logger.info('Info: Simulation finish run after exceeding max evaluation time')
                    break
                all_orders_finish = check_all_orders_finish(run_until_order_id)
            logger.info('Info: Simulation finish run')
        return

    @staticmethod
    def __add_orders_from_json_file(data):
        """
        :param data: data from json-file
        :return: start scenario from json files with defined orders
        """
        json_file = json.load(data)
        sys_time = get_system_time().json()
        system_time = transform_str_to_datetime(sys_time['timestamp'])
        next_order_id = get_next_order_id()
        for i, order in enumerate(json_file):
            if 'publishTime' in order.keys():
                publish_time_order = transform_str_to_datetime(order['publishTime'])
                publish_time = max(publish_time_order, system_time)
                if i == 0:
                    set_system_time_from_extern_in_system_state_management(SystemTimeResponse(timestamp=publish_time_order))
                    set_system_time_from_extern_in_amr_simulation(SystemTimeResponse(timestamp=publish_time_order))
            else:
                publish_time = system_time

            start_time_order = transform_str_to_datetime(order['startTime'])
            due_time_order = transform_str_to_datetime(order['dueTime'])
            duration_order = due_time_order - start_time_order

            start_time = max(start_time_order, publish_time+datetime.timedelta(hours=1))
            due_time = start_time + duration_order

            new_order_info = NewOrderInfo(orderId=next_order_id, sourceId=order['sourceId'],
                                          sinkId=order['sinkId'],
                                          startTime=start_time_order, dueTime=due_time_order,
                                          publishTime=publish_time,
                                          layoutId=order['layoutId'],
                                          pickupTime=order['pickupTime'], dropoffTime=order['dropoffTime'],
                                          dimension=Dimension(x=order['dimension']['x'], y=order['dimension']['y'],
                                                              z=order['dimension']['z'],
                                                              weight=order['dimension']['weight']),
                                          status=OrderStatus.NEW)
            if config.config_file.SIMULATION_ACTIVE is True:
                send_new_order_info_to_simulation(new_order_info)
            else:
                send_new_order_info(new_order_info)
            next_order_id = str(int(next_order_id) + 1)

        st.rerun()

    @st.experimental_dialog("Add new order")
    def __add_new_order(self):
        """
        :return: method for create new order for fleet management system
        """
        st.session_state.show_add_new_order = False
        next_order_id = get_next_order_id()
        order_id = st.text_input(label="Order id: ", value=next_order_id, disabled=True)
        node_list = get_node_and_stations_list()
        node_list.append('None')
        source_node = st.selectbox(label="Source node id: ", options=node_list)
        if config.config_file.STORAGE_LOCATION_TRACKING is True:
            node_list.append('Unknown')
        sink_node = st.selectbox(label="Sink node id: ", options=node_list)
        item_id = st.text_input(label="Item id: ", value=None)
        col1, col2 = st.columns(2)
        sys_time = get_system_time().json()
        system_time = transform_str_to_datetime(sys_time['timestamp'])
        with col1:
            start_date = st.date_input(label="Start date: ", value=system_time.date(), key='start_date')
        with col2:
            start_time = st.time_input(label="Start time: ", value=(system_time + datetime.timedelta(minutes=1)).time(),
                                       key='start_time')
        col1, col2 = st.columns(2)
        with col1:
            due_date = st.date_input(label="Due date: ", value=system_time.date(), key='due_date')
        with col2:
            due_time = st.time_input(label="Due time: ", value=(system_time + datetime.timedelta(hours=3)).time(),
                                     key='due_time')
        col1, col2 = st.columns(2)
        with col1:
            pickup_duration = st.text_input('Pickup Duration [s]:', '60', max_chars=3)
        with col2:
            dropoff_duration = st.text_input('Dropoff Duration [s]:', '60', max_chars=3)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            x = st.text_input("Length [cm]: ", 10)
        with col2:
            y = st.text_input("Width [cm]: ", 10)
        with col3:
            z = st.text_input("Height [cm]: ", 10)
        with col4:
            weight = st.text_input("Weight [kg]: ", 0.1)
        if st.button(label="Submit order"):
            start_time_full = datetime.datetime.combine(start_date, start_time)
            due_time_full = datetime.datetime.combine(due_date, due_time)
            if sink_node == 'Unknown':
                sink_node = None
            if source_node == 'None':
                source_node = None

            new_order_info = NewOrderInfo(orderId=order_id, sourceId=source_node, sinkId=sink_node,
                                          startTime=start_time_full, dueTime=due_time_full,
                                          publishTime=start_time_full,
                                          itemSkuId=str(item_id),
                                          layoutId=config.config_file.MAP_ID_DEFAULT,
                                          pickupTime=int(pickup_duration), dropoffTime=int(dropoff_duration),
                                          dimension=Dimension(x=x, y=y, z=z, weight=weight), status=OrderStatus.NEW)
            if config.config_file.SIMULATION_ACTIVE is True:
                send_new_order_info_to_simulation(new_order_info)
            else:
                send_new_order_info(new_order_info)
            st.session_state.enable_refresh = False
            st.rerun()

    @st.experimental_dialog("Add new AMR")
    def __add_new_amr(self):
        """
        :return method for add new amr to fleet management system:
        """
        st.session_state.show_add_new_amr = False
        next_amr_id = get_next_amr_id()
        amr_id = st.text_input(label="AMR id: ", value=next_amr_id, disabled=False)
        col1, col2 = st.columns(2)
        with col1:
            series_name = st.text_input(label="Name AMR series: ", value='A-Series')
        with col2:
            agv_class_list = ['CARRIER', 'FORKLIFT', ' CONVEYOR']
            agv_class = st.selectbox(label="AMR Type: ", options=agv_class_list, index=0)
        col1, col2, col3 = st.columns(3)
        with col1:
            node_list = get_node_and_stations_list()
            start_node = st.selectbox(label="Start node: ", options=node_list)
        with col2:
            max_speed = st.number_input(label="Max. velocity [m/s]: ", value=3.0, step=0.1)
        with col3:
            max_reach = st.number_input(label="Max. reach battery [m]: ", value=10000, step=100)

        st.text('AMR Size:')
        col1, col2, col3 = st.columns(3)
        with col1:
            length = st.number_input(label="Length [cm]: ", value=50, step=1)
        with col2:
            width = st.number_input(label="Width [cm]: ", value=50, step=1)
        with col3:
            height = st.number_input(label="Height [cm]: ", value=40, step=1)

        st.text('AMR Load Specifications:')
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            max_length_load = st.number_input(label="Max. length [cm]: ", value=40, step=1)
        with col2:
            max_width_load = st.number_input(label="Max. width [cm]: ", value=40, step=1)
        with col3:
            max_height_load = st.number_input(label="Max. height [cm]: ", value=30, step=1)
        with col4:
            max_weight_load = st.number_input(label="Max. weight [kg]: ", value=10, step=1)

        if st.button(label="Add AMR"):
            new_amr_request = NewAMRSystemRequest(amrId=amr_id, lastNodeId=start_node,
                                                  layoutId=config.config_file.MAP_ID_DEFAULT,
                                                  maxReachBattery=int(max_reach))
            new_amr_base_data_request = NewAMRRequest(amrId=amr_id, seriesName=series_name, agvClass=agv_class,
                                                      maxLoadMass=max_weight_load, maxSpeed=max_speed,
                                                      loadDimension=LoadDimension(length=max_length_load,
                                                                                  width=max_width_load,
                                                                                  height=max_height_load),
                                                      length=length, width=width, height=height)
            add_amr_basedatamanagement_api(new_amr_base_data_request)
            add_amr_systemdatamanagement_api(new_amr_request)
            add_amr_simulation_api(new_amr_request)
            st.session_state.enable_refresh = False
            st.rerun()


set_service_urls()

if __name__ == '__main__':
    dashboard = Dashboard()
    dashboard.start_dashboard()

