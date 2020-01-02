import click
import os
import sys
import time

from pdclient import PdClient


@click.command()
@click.option('--horiz/--vert', default=False, help="Choose direction of motion")
@click.option('--freq', type=float, default=0.2)
@click.option('--host')
@click.argument("startx", type=int)
@click.argument("starty", type=int)
@click.argument("size", type=int)
def main(horiz, startx, starty, size, freq, host):
    print([horiz, startx, starty, size, freq, host])

    phase = 0
    if host is None:
        host = os.environ.get('PD_HOST')
    if host is None:
        print("Error: No --host provided, and no PD_HOST env variable found")
        sys.exit(-1)

    client = PdClient(host)
    while True:
        x = startx
        y = starty

        if phase < size: # counting up
            offset = phase
        else: # counting down
            offset = size - (phase % size)
        
        if horiz:
            x += offset
        else:
            y += offset

        client.enable_positions([(x, y)])
        phase = (phase + 1) % (size*2)

        time.sleep(1 / freq)


if __name__ == '__main__':
    main()