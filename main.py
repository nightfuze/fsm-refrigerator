import math
import tkinter as tk
from enum import Enum, auto
import winsound


class Signaling:
    def __init__(self, fsm):
        self.fsm = fsm
        #   Файл с сигнализацией
        self.file_name = "alarm.wav"
        self.playing_audio = False

    def update(self):
        if (self.fsm.state == State.THREAT_FAILURE or self.fsm.state == State.MALFUNCTION) and not self.playing_audio:
            self.play_audio()

        if (not self.fsm.state == State.THREAT_FAILURE and not self.fsm.state == State.MALFUNCTION) and  self.playing_audio:
            self.stop_audio()

    def play_audio(self):
        self.playing_audio = True
        winsound.PlaySound(self.file_name, winsound.SND_FILENAME | winsound.SND_LOOP| winsound.SND_ASYNC)


    def stop_audio(self):
        self.playing_audio = False
        winsound.PlaySound(None, winsound.SND_PURGE)

class State(Enum):
    OFF = ("ОТКЛЮЧЕН", auto())
    COOLING = ("НОРМАЛЬНОЕ ОХЛАЖДЕНИЕ", auto())
    HIGH_COOLING = ("СИЛЬНОЕ ОХЛАЖДЕНИЕ", auto())
    LOW_COOLING = ("СЛАБОЕ ОХЛАЖДЕНИЕ", auto())
    THREAT_FAILURE = ("УГРОЗА ПОЛОМКИ", auto())
    MALFUNCTION = ("НЕИСПРАВНОСТЬ", auto())
    DEFROSTING = ("РАЗМОРОКА", auto())

    def __init__(self, name_ru, auto_value):
        self.name_ru = name_ru
        self.auto_value = auto_value


class Signal(Enum):
    TURN_ON = ("ВКЛЮЧИТЬ", auto())
    TURN_OFF = ("ВЫКЛЮЧИТЬ", auto())
    INCREASE_TEMPERATURE = ("ПОВЫСИТЬ ТЕМПЕРАТУРУ", auto())
    DECREASE_TEMPERATURE = ("ПОНИЗИТЬ ТЕМПЕРАТУРУ", auto())
    OPEN_DOOR = ("ОТКРЫТЬ ДВЕРЬ", auto())
    CLOSE_DOOR = ("ЗАКРЫТЬ ДВЕРЬ", auto())
    DOOR_OPEN_MORE_THAN_30 = ("ДВЕРЬ ОТКРЫТА БОЛЬШЕ 30 СЕКУНД", auto())
    DOOR_OPEN_MORE_THAN_120 = ("ДВЕРЬ ОТКРЫТА БОЛЬШЕ 120 СЕКУНД", auto())

    def __init__(self, name_ru, auto_value):
        self.name_ru = name_ru
        self.auto_value = auto_value


class Refrigerator:
    def __init__(self, initial_temperature):
        self.temperature = initial_temperature
        self.target_temperature = initial_temperature
        self.temp_outside = initial_temperature
        self.is_door_open = False
        self.is_light_on = False
        self.is_turn_on = False

    #   Температура увеличивается и уменьшается по параболе
    def cool(self):
        self.temperature = max(self.target_temperature, self.temperature - (1 / math.sqrt(self.temp_outside - self.temperature + 1)))

    def low_cool(self):
        self.temperature = min(self.target_temperature, self.temperature + 0.2 * math.sqrt(self.temp_outside - self.temperature + 1))

    def high_cool(self):
        self.temperature = max(self.target_temperature, self.temperature - (1 / math.sqrt(self.temp_outside - self.temperature + 1)))

    def turn_off(self):
        self.temperature = min(self.temp_outside, self.temperature + 0.2 * math.sqrt(self.temp_outside - self.temperature + 1))

    def defrost(self):
        self.temperature = min(self.temp_outside, self.temperature + 1)

    #   Максимальная заданная температура
    def increase_temp(self):
        if self.target_temperature < 15:
            self.target_temperature += 1

    #   Минимальная заданная температура
    def decrease_temp(self):
        if self.target_temperature > -2:
            self.target_temperature -= 1

    def open_door(self):
        self.is_door_open = True

    def close_door(self):
        self.is_door_open = False

    def turn_on(self):
        self.is_turn_on = True

    def turn_off(self):
        self.is_turn_on = False


class RefrigeratorFSM:
    def __init__(self, refrigerator):
        self.state = State.OFF
        self.refrigerator = refrigerator

    def send_signal(self, signal):
        if self.state == State.OFF:
            if signal == Signal.TURN_ON:
                self.state = State.COOLING
        elif self.state == State.COOLING:
            if signal == Signal.INCREASE_TEMPERATURE:
                self.state = State.LOW_COOLING
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.state = State.HIGH_COOLING
            elif signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
            elif signal == Signal.TURN_OFF and self.refrigerator.is_door_open:
                self.state = State.DEFROSTING
        elif self.state == State.COOLING:
            if signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
        elif self.state == State.LOW_COOLING:
            if signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
        elif self.state == State.THREAT_FAILURE:
            if signal == Signal.DOOR_OPEN_MORE_THAN_120:
                self.state = State.MALFUNCTION
            #   Логика для выключения звуковой сигналки
            if signal == Signal.CLOSE_DOOR:
                self.state = State.COOLING
        # Из разморозки во включенное состояние
        elif self.state == State.DEFROSTING:
            if signal == signal.TURN_ON and not self.refrigerator.is_door_open:
                self.state = State.COOLING
                self.refrigerator.cool()



        if self.state != State.OFF:
            if signal == Signal.INCREASE_TEMPERATURE:
                self.refrigerator.increase_temp()
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.refrigerator.decrease_temp()


    # То что тут было изначально работало странно(Состояния не переключались, не охлаждался и не нагревался)

    def update(self):
        # if self.state != State.OFF or self.state != State.MALFUNCTION or self.state != State.THREAT_FAILURE:
        #     if self.refrigerator.temperature == self.refrigerator.target_temperature:
        #         self.state = State.COOLING
        #     elif self.refrigerator.temperature < self.refrigerator.target_temperature:
        #         self.state = State.LOW_COOLING
        #     elif self.refrigerator.temperature > self.refrigerator.target_temperature:
        #         self.state = State.HIGH_COOLING


        if self.state == State.OFF:
            self.refrigerator.turn_off()

        elif self.state == State.COOLING:
            if self.refrigerator.temperature < self.refrigerator.target_temperature:
                self.refrigerator.low_cool()
                self.state = State.LOW_COOLING
            elif self.refrigerator.temperature == self.refrigerator.target_temperature:
                self.state= State.COOLING
                self.refrigerator.cool()
            elif self.refrigerator.temperature > self.refrigerator.target_temperature:
                self.refrigerator.high_cool()
                self.state = State.HIGH_COOLING

        elif self.state == State.LOW_COOLING:
            if self.refrigerator.temperature < self.refrigerator.target_temperature:
                self.refrigerator.low_cool()
                self.state = State.LOW_COOLING
            elif self.refrigerator.temperature == self.refrigerator.target_temperature:
                self.state= State.COOLING
                self.refrigerator.cool()
            elif self.refrigerator.temperature > self.refrigerator.target_temperature:
                self.refrigerator.high_cool()
                self.state = State.HIGH_COOLING

        elif self.state == State.HIGH_COOLING:
            if self.refrigerator.temperature > self.refrigerator.target_temperature:
                self.refrigerator.high_cool()
                self.state = State.HIGH_COOLING
            elif self.refrigerator.temperature == self.refrigerator.target_temperature:
                self.state= State.COOLING
            elif self.refrigerator.temperature < self.refrigerator.target_temperature:
                self.refrigerator.low_cool()
                self.state = State.LOW_COOLING

        elif self.state == State.DEFROSTING:
            self.refrigerator.defrost()


class Timer:
    def __init__(self, fsm):
        self.time = 0
        self.fsm = fsm
        self.is_started = False

    def update(self):
        if not self.is_started:
            return
        self.time += 1

        if self.time > 30:
            self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_30)
        elif self.time > 120:
            self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_120)
        # if self.time > 3:
        #     self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_30)
        # if self.time > 10:
        #     self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_120)

    def start(self):
        self.is_started = True
        self.reset()

    def stop(self):
        self.is_started = False
        self.reset()

    def reset(self):
        self.time = 0


class RefrigeratorApp:
    def __init__(self, root):
        self.root = root
        # width = self.root.winfo_screenwidth()
        # height = self.root.winfo_screenheight()
        # self.root.geometry("%dx%d" % (width, height))
        self.root.geometry("1280x800")
        self.root.title("Кончный Автомат Холодильника")

        self.temp_outside = 25
        self.refrigerator = Refrigerator(self.temp_outside)
        self.fsm = RefrigeratorFSM(self.refrigerator)
        self.timer = Timer(self.fsm)
        self.signaling = Signaling(self.fsm)

        self.pos_x = 250
        self.pos_y = 50
        self.width = 200
        self.height = 400
        self.padding = 10

        self.door_handle_x = self.pos_x + self.width - self.padding * 4
        self.door_handle_y = self.pos_y + self.height / 2
        self.door_handle_width = 15
        self.door_handle_height = 80

        container_frame = tk.Frame(root)
        container_frame.pack()

        self.canvas = tk.Canvas(container_frame, width=500, height=500)
        self.canvas.pack(side=tk.LEFT)

        control_frame = tk.Frame(container_frame)
        control_frame.pack(side=tk.RIGHT, padx=10)

        self.state_label = tk.Label(control_frame, text=f"Состояние: {self.fsm.state.name_ru}")
        self.state_label.pack(anchor=tk.W)

        self.outside_temp_label = tk.Label(control_frame, text=f"Температура снаружи: {self.temp_outside}°C")
        self.outside_temp_label.pack(anchor=tk.W)

        self.target_temp_label = tk.Label(control_frame,
                                          text=f"Заданная температура: {self.refrigerator.target_temperature}°C")
        self.target_temp_label.pack(anchor=tk.W)

        self.temp_label = tk.Label(control_frame, text=f"Текущая температура: {self.refrigerator.temperature}°C")
        self.temp_label.pack(anchor=tk.W)

        buttons = [
            (Signal.TURN_ON.name_ru, self.turn_on),
            (Signal.TURN_OFF.name_ru, self.turn_off),
            (Signal.INCREASE_TEMPERATURE.name_ru, self.increase_temp),
            (Signal.DECREASE_TEMPERATURE.name_ru, self.decrease_temp),
            (Signal.OPEN_DOOR.name_ru, self.open_door),
            (Signal.CLOSE_DOOR.name_ru, self.close_door),
        ]

        for text, command in buttons:
            tk.Button(control_frame, text=text, command=command).pack(fill=tk.X)

        self.draw()
        self.update()

    def draw(self):
        self.canvas.delete('all')

        self.draw_refrigerator()

    def draw_refrigerator(self):
        if self.refrigerator.is_door_open:
            self.draw_open_door()
        else:
            self.draw_close_door()

    def draw_open_door(self):
        self.canvas.create_rectangle(
            self.pos_x, self.pos_y,
            self.pos_x + self.width,
            self.pos_y + self.height,
            fill='lightgray', width=2
        )
        self.canvas.create_rectangle(
            self.pos_x + self.padding,
            self.pos_y + self.padding,
            self.pos_x + self.width - self.padding,
            self.pos_y + self.height - self.padding,
            fill='white', width=2
        )
        pos_x = self.pos_x - self.width
        self.canvas.create_rectangle(
            pos_x, self.pos_y,
            pos_x + self.width,
            self.pos_y + self.height,
            fill='lightgray', width=2
        )
        self.canvas.create_rectangle(
            pos_x + self.padding,
            self.pos_y + self.padding,
            pos_x + self.width - self.padding,
            self.pos_y + self.height - self.padding,
            fill='white', width=2
        )

    def draw_close_door(self):
        self.canvas.create_rectangle(
            self.pos_x, self.pos_y,
            self.pos_x + self.width,
            self.pos_y + self.height,
            fill='lightgray', width=2
        )
        self.canvas.create_rectangle(
            self.pos_x + self.padding,
            self.pos_y + self.padding,
            self.pos_x + self.width - self.padding,
            self.pos_y + self.height - self.padding,
            fill='white', width=2
        )
        self.canvas.create_rectangle(
            self.door_handle_x, self.door_handle_y,
            self.door_handle_x + self.door_handle_width,
            self.door_handle_y + self.door_handle_height,
            fill='gray', width=1
        )

        temp_display_x = self.pos_x + self.padding + 10
        temp_display_y = self.pos_y + self.padding + 10
        temp_display_width = 80
        temp_display_height = 30
        self.temp_display = self.canvas.create_rectangle(
            temp_display_x, temp_display_y,
            temp_display_width + temp_display_x,
            temp_display_height + temp_display_y,
            fill='black'
        )

        temp_text_x = temp_display_x + temp_display_width / 2
        temp_text_y = temp_display_y + temp_display_height / 2
        self.temp_text = self.canvas.create_text(temp_text_x, temp_text_y,
                                                 text=f"{self.refrigerator.temperature:.0f}°C", fill='green')

        # status_indicator_x = self.pos_x + self.width - self.padding - 40
        # status_indicator_y = self.pos_y + self.padding + 10
        # status_indicator_width = 30
        # self.status_indicator = self.canvas.create_oval(
        #     status_indicator_x, status_indicator_y,
        #     status_indicator_x + status_indicator_width,
        #     status_indicator_y + status_indicator_width,
        #     fill='cyan'
        # )

    def update(self):
        self.draw()

        self.state_label.config(text=f"Состояние: {self.fsm.state.name_ru}")
        self.temp_label.config(text=f"Текущая температура: {self.refrigerator.temperature:.0f}°C")
        self.target_temp_label.config(text=f"Заданная температура: {self.refrigerator.target_temperature:.0f}°C")

        if self.refrigerator.temperature <= 0:
            color = 'cyan'
        elif self.refrigerator.temperature >= 10:
            color = 'red'
        else:
            color = 'lightgreen'
        self.canvas.itemconfig(self.temp_text, fill=color)

        # if not self.refrigerator.is_turn_on:
        #     self.canvas.itemconfig(self.status_indicator, fill='white')
        # elif self.refrigerator.is_turn_on:
        #     self.canvas.itemconfig(self.status_indicator, fill='green')

        self.fsm.update()
        self.timer.update()
        self.signaling.update()
        self.root.after(1000, self.update)


    def open_door(self):
        if not self.refrigerator.is_door_open:
            #   Отправка сигнала
            self.fsm.send_signal(Signal.OPEN_DOOR)
            self.refrigerator.open_door()
            self.timer.start()

    def close_door(self):
        if self.refrigerator.is_door_open:
            #   Отправка сигнала
            self.fsm.send_signal(Signal.CLOSE_DOOR)
            self.refrigerator.close_door()
            self.timer.stop()

    def turn_on(self):
        self.fsm.send_signal(Signal.TURN_ON)

    def turn_off(self):
        self.fsm.send_signal(Signal.TURN_OFF)

    def increase_temp(self):
        self.fsm.send_signal(Signal.INCREASE_TEMPERATURE)

    def decrease_temp(self):
        self.fsm.send_signal(Signal.DECREASE_TEMPERATURE)


if __name__ == "__main__":
    root = tk.Tk()
    app = RefrigeratorApp(root)
    root.mainloop()
