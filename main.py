import tkinter as tk
from enum import Enum, auto


class State(Enum):
    OFF = ("ВЫКЛЮЧЕН", auto())
    COOLING = ("ОХЛАЖДЕНИЕ", auto())
    DEFROSTING = ("РАЗМОРАЖИВАНИЕ", auto())
    MAINTAINING = ("ПОДДЕРЖКА ТЕМПЕРАТУРЫ", auto())
    ENERGY_SAVING = ("ЭНЕРГОСБЕРЕЖЕНИЕ", auto())
    EMERGENCY = ("АВАРИЙНЫЙ РЕЖИМ", auto())
    QUICK_FREEZE = ("БЫСТРАЯ ЗАМОРОЗКА", auto())

    def __init__(self, name_ru, auto_value):
        self.name_ru = name_ru
        self.auto_value = auto_value


class Signal(Enum):
    TURN_ON = ("ВКЛЮЧИТЬ", auto())
    TURN_OFF = ("ВЫКЛЮЧИТЬ", auto())
    TEMPERATURE_REACHED = ("ТЕМПЕРАТУРА ДОСТИГНУТА", auto())
    DEFROST_REQUIRED = ("ТРЕБУЕТСЯ РАЗМОРОЗКА", auto())
    MALFUNCTION = ("НЕИСПРАВНОСТЬ", auto())
    ENERGY_SAVE = ("ЭНЕРГОСБЕРЕЖЕНИЕ", auto())
    QUICK_FREEZE = ("БЫСТРАЯ ЗАМОРОЗКА", auto())

    def __init__(self, name_ru, auto_value):
        self.name_ru = name_ru
        self.auto_value = auto_value

class Refrigerator:
    def __init__(self):
        self.temperature = 20
        self.target_temperature = 4

    def cool(self):
        self.temperature = max(self.target_temperature, self.temperature - 1)

    def defrost(self):
        self.temperature = min(20, self.temperature + 1)

    def quick_freeze(self):
        self.temperature = max(-10, self.temperature - 2)

    def maintain(self):
        if self.temperature < self.target_temperature:
            self.temperature += 1
        elif self.temperature > self.target_temperature:
            self.temperature -= 1


class RefrigeratorFSM:
    def __init__(self, refrigerator):
        self.state = State.OFF
        self.refrigerator = refrigerator

    def send_signal(self, signal):
        if self.state == State.OFF:
            if signal == Signal.TURN_ON:
                self.state = State.COOLING
        elif self.state == State.COOLING:
            if signal == Signal.TEMPERATURE_REACHED:
                self.state = State.MAINTAINING
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.DEFROST_REQUIRED:
                self.state = State.DEFROSTING
            elif signal == Signal.QUICK_FREEZE:
                self.state = State.QUICK_FREEZE
        elif self.state == State.DEFROSTING:
            if signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.TEMPERATURE_REACHED:
                self.state = State.COOLING
            elif signal == Signal.QUICK_FREEZE:
                self.state = State.QUICK_FREEZE
        elif self.state == State.MAINTAINING:
            if signal == Signal.DEFROST_REQUIRED:
                self.state = State.DEFROSTING
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.ENERGY_SAVE:
                self.state = State.ENERGY_SAVING
        elif self.state == State.ENERGY_SAVING:
            if signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.TEMPERATURE_REACHED:
                self.state = State.MAINTAINING
        elif self.state == State.EMERGENCY:
            if signal == Signal.TURN_OFF:
                self.state = State.OFF
        elif self.state == State.QUICK_FREEZE:
            if signal == Signal.TEMPERATURE_REACHED:
                self.state = State.MAINTAINING
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF

        if signal == Signal.MALFUNCTION:
            self.state = State.EMERGENCY

    def update(self):
        if self.state == State.COOLING:
            self.refrigerator.cool()
        elif self.state == State.DEFROSTING:
            self.refrigerator.defrost()
        elif self.state == State.MAINTAINING:
            self.refrigerator.maintain()
        elif self.state == State.QUICK_FREEZE:
            self.refrigerator.quick_freeze()
        elif self.state == State.OFF:
            self.refrigerator.defrost()
        elif self.state == State.EMERGENCY:
            self.refrigerator.defrost()



class RefrigeratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Кончный Автомат Холодильника")
        self.refrigerator = Refrigerator()
        self.fsm = RefrigeratorFSM(self.refrigerator)

        container_frame = tk.Frame(root)
        container_frame.pack()

        self.canvas = tk.Canvas(container_frame, width=300, height=500)
        self.canvas.pack(side=tk.LEFT)

        control_frame = tk.Frame(container_frame)
        control_frame.pack(side=tk.RIGHT, padx=10)

        self.state_label = tk.Label(control_frame, text=f"Состояние: {self.fsm.state.name_ru}")
        self.state_label.pack()

        self.temp_label = tk.Label(control_frame, text=f"Температура: {self.refrigerator.temperature}°C")
        self.temp_label.pack()

        buttons = [
            (Signal.TURN_ON.name_ru, self.turn_on),
            (Signal.TURN_OFF.name_ru, self.turn_off),
            (Signal.TEMPERATURE_REACHED.name_ru, self.temp_reached),
            (Signal.DEFROST_REQUIRED.name_ru, self.defrost_required),
            (Signal.MALFUNCTION.name_ru, self.malfunction),
            (Signal.ENERGY_SAVE.name_ru, self.energy_save),
            (Signal.QUICK_FREEZE.name_ru, self.quick_freeze)
        ]

        for text, command in buttons:
            tk.Button(control_frame, text=text, command=command).pack(fill=tk.X)

        self.draw()
        self.update()

    def draw(self):
        self.canvas.create_rectangle(50, 50, 250, 450, fill='lightgray', width=2)
        self.canvas.create_rectangle(60, 60, 240, 440, fill='white', width=2)
        self.canvas.create_rectangle(220, 200, 235, 300, fill='gray', width=1)

        self.temp_display = self.canvas.create_rectangle(70, 70, 150, 100, fill='black')
        self.temp_text = self.canvas.create_text(110, 85, text="20°C", fill='green')
        self.status_indicator = self.canvas.create_oval(200, 70, 230, 100, fill='red')

    def update(self):
        self.state_label.config(text=f"Состояние: {self.fsm.state.name_ru}")
        self.temp_label.config(text=f"Температура: {self.refrigerator.temperature}°C")
        self.canvas.itemconfig(self.temp_text, text=f"{self.refrigerator.temperature}°C")

        if self.fsm.state == State.OFF:
            color = 'red'
        elif self.fsm.state == State.EMERGENCY:
            color = 'orange'
        else:
            color = 'green'
        self.canvas.itemconfig(self.status_indicator, fill=color)

        if self.refrigerator.temperature <= 0:
            color = 'blue'
        elif self.refrigerator.temperature >= 10:
            color = 'red'
        else:
            color = 'green'
        self.canvas.itemconfig(self.temp_text, fill=color)

        self.fsm.update()
        self.root.after(1000, self.update)

    def turn_on(self):
        self.fsm.send_signal(Signal.TURN_ON)

    def turn_off(self):
        self.fsm.send_signal(Signal.TURN_OFF)

    def temp_reached(self):
        self.fsm.send_signal(Signal.TEMPERATURE_REACHED)

    def defrost_required(self):
        self.fsm.send_signal(Signal.DEFROST_REQUIRED)

    def malfunction(self):
        self.fsm.send_signal(Signal.MALFUNCTION)

    def energy_save(self):
        self.fsm.send_signal(Signal.ENERGY_SAVE)

    def quick_freeze(self):
        self.fsm.send_signal(Signal.QUICK_FREEZE)


if __name__ == "__main__":
    root = tk.Tk()
    app = RefrigeratorApp(root)
    root.mainloop()
