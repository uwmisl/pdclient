import click
import math
import matplotlib.pyplot as plt
import numpy as np
import pdclient
import time


HISTORY = 60 # seconds
PERIOD = 0.2 # seconds
N_SAMPLES = math.ceil(HISTORY / PERIOD)


@click.command()
@click.argument('host')
def main(host):
    plt.style.use('ggplot')
    plt.ion()

    client = pdclient.PdClient(f'http://{host}:7000/rpc')

    time_vec = []
    cap_vec = []
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.xlim([-N_SAMPLES * PERIOD, 0])
    line, = ax.plot(time_vec, cap_vec, '-o')
    plt.ylabel('capacitance (pF)')
    plt.title('Live Active Capacitance')
    plt.show()

    while True:
        capacitance = client.active_capacitance()
        cap_vec.append(capacitance)
        if len(cap_vec) > N_SAMPLES:
            cut_size = min(30, int(math.ceil(N_SAMPLES/10)))
            cap_vec = cap_vec[cut_size:]
        time_vec = np.arange(0, -1 * len(cap_vec), -1) * PERIOD
        min_value = np.min(cap_vec)
        max_value = np.max(cap_vec)
        if min_value <= line.axes.get_ylim()[0] or max_value >= line.axes.get_ylim()[1]:
            plt.ylim([min_value - np.std(cap_vec), max_value + np.std(cap_vec)])
        line.set_xdata(time_vec)
        line.set_ydata(cap_vec)
        plt.pause(0.2)

if __name__ == '__main__':
    main()