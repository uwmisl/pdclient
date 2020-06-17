import threading
import time

class PIDControl(object):
    """A single channel PID controller for temperature
    """
    def __init__(self, kP: float, tI: float, tD:float, yMax: float, yMin: float, iMax: float):
        self.kP = kP
        self.tI = tI
        self.tD = tD
        self.yMax = yMax
        self.yMin = yMin
        self.iMax = iMax
        self.accum = 0.0
        self.prev_error = 0.0
        self.last_run_time = time.monotonic()

    def run(self, error: float, feed_forward=0.0):
        cur_time = time.monotonic()
        delta_t = cur_time - self.last_run_time
        self.last_run_time = cur_time

        y = feed_forward

        # Clamp integral term (in output units) to +/- iMax
        if self.accum >= self.iMax / self.kP:
            self.accum = self.iMax / self.kP
        elif self.accum <= -self.iMax / self.kP:
            self.accum = -self.iMax / self.kP

        y += self.kP * (error + self.accum + self.tD / delta_t * (error - self.prev_error))

        limit_up = False
        limit_down = False
        if y >= self.yMax:
            y = self.yMax
            limit_up = True
        if y <= self.yMin:
            y = self.yMin
            limit_down = True

        # Integrate, unless we're on one of the limits then don't integrate in that direction
        if error > 0 and not limit_up or \
           error < 0 and not limit_down:
            self.accum += delta_t / self.tI * error

        return y

    def integral_out(self):
        return self.accum * self.kP

class TemperatureControl(object):
    """Provides a full temperature controller for a purple drop heater

    It controls all heating channels to maintain a constant temperature at all
    electrodes.

    Generally, you should use the factory function for the electrode board
    configuratin you're using, e.g. `get_v4_controller()`, as this will
    instantiate a TemperatureControl object for you with the appropriate
    channels and gains.

    Once instantiated, the application can either call `run` periodically to
    update the controller output (perhaps every 0.5 to 1.5seconds), or call
    `start` to launch a background thread to periodically run the controller.
    """
    def __init__(self, client, channel_gains, ymax, kP, tI, tD, alpha_drop, k_drop, ambient_temp=None):
        self.client = client
        self.channel_gains = channel_gains
        self.alpha_drop = alpha_drop
        self.k_drop = k_drop
        if ambient_temp is None:
            self.ambient = 20.0
        else:
            self.ambient = ambient_temp
        self.setpoint = 0.0
        self.drop_temperature = 0.0
        self._pids = []
        self.thread = None
        self.stop_flag = False
        self.last_run_time = time.monotonic()

        for i, g in enumerate(channel_gains):
            ch_ymax = 0
            try:
                ch_ymax = ymax[i]
            except TypeError:
                ch_ymax = ymax
            pid = PIDControl(kP=g*kP, tI=tI, tD=tD, yMax=ch_ymax, yMin=0.0, iMax=50.0*g)
            self._pids.append(pid)

    def set_target(self, target):
        self.setpoint = target

    def integrals(self):
        return [p.integral_out() for p in self._pids]

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Called start() on TemperatureControl, but a thread is already running")

        self.stop_flag = False
        self.thread = threading.Thread(
            name="TemperatureControl",
            target=self.__thread_entry,
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.stop_flag = True
        if self.thread is not None:
            self.thread.join()
            self.thread = None

    def run(self):
        N = len(self._pids)
        outputs = [0.0] * N
        cur_time = time.monotonic()
        delta_t = cur_time - self.last_run_time
        self.last_run_time = cur_time

        temperatures = self.client.temperatures()
        if len(temperatures) < N:
            raise ValueError(f"Only got {len(temperatures)} temperatures")

        # The setpoint given is for the drop, but there is a known temperature
        # drop from the sensors to the drop. This delta is characterized by the
        # k_drop coefficient.
        sensor_setpoint = (self.setpoint - self.k_drop * self.ambient) / (1.0 - self.k_drop)

        for i in range(N):
            error = sensor_setpoint - temperatures[i]
            outputs[i] = self._pids[i].run(error, feed_forward=(sensor_setpoint - self.ambient) * self.channel_gains[i])
            self.client.set_pwm_duty_cycle(i, outputs[i])

        sensor_avg = sum(temperatures) / len(temperatures)
        drop_adjusted = sensor_avg - self.k_drop * (sensor_avg - self.ambient)
        k_filter = self.alpha_drop * delta_t
        if(k_filter > 1.0):
            k_filter = 1.0
        self.drop_temperature = self.drop_temperature * (1 - k_filter) + drop_adjusted * k_filter
        return outputs

    def __thread_entry(self):
        RUN_PERIOD = 0.5
        last_run_time = 0.0
        while True:
            if self.stop_flag:
                return
            cur_time = time.time()
            if cur_time - last_run_time > RUN_PERIOD:
                last_run_time = cur_time
                self.run()
            time.sleep(0.1)

def get_v4_controller(client, output_scale = 1.0):
    """Create a TemperatureControl designed for the v4 electrode board
    """
    # The deg per deg drop between sensor and heated water drop
    # i.e. T_drop = T_sensor - (T_sensor - T_ambient) * K_DROP
    K_DROP = 0.10
    # ALPHA_DROP is the gain of a single tap IIR low-pass filter used to
    # generate the estimated drop temperature
    # i.e. T_drop_filt[n] = T_drop[n-1] * (1-ALPHA_DROP) + T_drop[n] * ALPHA_DROP * dt
    ALPHA_DROP = 0.18
    # These parameters were determined experimentally using a rev4 electrode board and
    # a 6um mylar film dielectric.

    # Channel gains are intended to normalize the differences in electrodes,
    # and they are determined by observing the steady state duty_cycle per
    # deg C temperature rise
    return TemperatureControl(
        client,
        channel_gains=[0.007, 0.003, 0.003, 0.007],
        ymax=[0.98, 0.5, 0.5, 0.98],
        kP=18.0,
        tI=6.0, # seconds
        tD=0.8,
        alpha_drop=ALPHA_DROP,
        k_drop=K_DROP,
    )
