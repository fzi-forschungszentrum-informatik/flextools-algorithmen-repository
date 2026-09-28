import copy

import pandas as pd
import matplotlib

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

matplotlib.use("TkAgg")


def create_amr_status_figure(data, title, save_path, save=False, show_figure=True):
    df = copy.deepcopy(data)

    df['Start Time'] = pd.to_datetime(df['Start Time'])
    df['End Time'] = pd.to_datetime(df['End Time'])
    start_0 = df['Start Time'].min()
    span = df['End Time'].max()-df['Start Time'].min()
    time_range = pd.timedelta_range(start=0, end=span, freq='1s')

    result = []

    for t in time_range:
        status_counts = {'Zeit': t, 'WAITING': 0, 'EMPTY_DRIVING': 0, 'DRIVING': 0, 'WAITING_ORDERS': 0,
                         'WORKING_ORDERS': 0}
        for _, row in df.iterrows():
            start_rel = row['Start Time'] - start_0
            end_rel = row['End Time'] - start_0
            if start_rel <= t < end_rel:
                for col in df.columns[4:]:
                    status = row[col]
                    status_counts[status] += 1
                status_counts['WAITING_ORDERS'] += row['Number of current waiting orders']
                status_counts['WORKING_ORDERS'] += row['Number of current working orders']
        total = status_counts['WAITING'] + status_counts['EMPTY_DRIVING'] + status_counts['DRIVING']
        if total > 0:
            for key in ['WAITING', 'EMPTY_DRIVING', 'DRIVING']:
                status_counts[key] = 100 * status_counts[key] / total
        result.append(status_counts)

    df_plot = pd.DataFrame(result)

    df_plot['Zeitschritt'] = range(1, len(df_plot) + 1)
    df_plot.set_index('Zeitschritt', inplace=True)

    fig, ax1 = plt.subplots(figsize=(12, 6))
    stack_plot = plt.stackplot(df_plot.index, df_plot['DRIVING'], df_plot['EMPTY_DRIVING'], df_plot['WAITING'],
                               labels=['Loaded Driving', 'Empty Driving', 'Waiting'], colors=['green', 'blue', 'gray'])

    ax2 = ax1.twinx()
    line_waiting_orders, = ax2.plot(df_plot.index, df_plot['WAITING_ORDERS'], color='red',
                                    label='Number of waiting orders in the system')
    line_working_orders, = ax2.plot(df_plot.index, df_plot['WORKING_ORDERS'], color='orange',
                                    label='Number of working orders in the system')
    ax2.set_ylabel('Current number of working/waiting orders in system', fontsize=14)
    lines = stack_plot + [line_waiting_orders] + [line_working_orders]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right', bbox_to_anchor=(1.65, 1), borderaxespad=0)
    ax1.set_ylabel('Relative Distribution [%]', fontsize=14)
    ax1.set_xlabel('Simulation Time [Time steps]', fontsize=14)
    plt.title(title, fontsize=14, fontweight='bold')
    ax1.tick_params(axis='x', labelsize=14)
    ax1.tick_params(axis='y', labelsize=14)
    ax2.tick_params(axis='y', labelsize=14)
    ax1.margins(x=0, y=0)
    ax2.margins(x=0, y=0)
    plt.subplots_adjust(right=0.68)
    plt.tight_layout()
    if save is True:
        fig.savefig(save_path, dpi=300)
    if show_figure is True:
        plt.show()
    plt.close(fig)
    return
