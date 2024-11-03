import math
import random
import tkinter as tk
# import winsound
from datetime import datetime
from enum import Enum, auto
from tkinter import PhotoImage, messagebox
from tkinter import ttk


class Signaling:
    def __init__(self, fsm):
        self.fsm = fsm
        #   Файл с сигнализацией
        self.file_name = "alarm.wav"
        self.playing_audio = False

    def update(self):
        if not self.fsm.state == State.OFF and ((self.fsm.state == State.THREAT_FAILURE) and not self.playing_audio):
            self.play_audio()

        if self.fsm.state == State.OFF or ((
                                                   not self.fsm.state == State.THREAT_FAILURE) and self.playing_audio and not self.fsm.refrigerator.is_door_open):
            self.stop_audio()

    def play_audio(self):
        self.playing_audio = True
        # winsound.PlaySound(self.file_name, winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC)

    def stop_audio(self):
        self.playing_audio = False
        # winsound.PlaySound(None, winsound.SND_PURGE)


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
        self.target_temperature = 0
        self.freezer_temperature = initial_temperature
        self.freezer_target_temperature = -18
        self.temp_outside = initial_temperature
        self.is_door_open = False
        self.is_freezer_door_open = False
        self.is_turn_on = False
        self.max_temperature = 18
        self.min_temperature = -6

    def cool(self):
        self.temperature = max(self.target_temperature,
                               self.temperature - (1 / math.sqrt(self.temp_outside - self.temperature + 1)))
        self.freezer_temperature = max(self.freezer_target_temperature, self.freezer_temperature - (1 / math.sqrt(
            self.temp_outside - self.freezer_temperature + 1
        )))

    def low_cool(self):
        self.temperature = min(self.target_temperature,
                               self.temperature + 0.2 * math.sqrt(self.temp_outside - self.temperature + 1))
        self.freezer_temperature = min(self.freezer_target_temperature, self.freezer_temperature + 0.2 * math.sqrt(
            self.temp_outside - self.freezer_temperature + 1
        ))

    def high_cool(self):
        self.temperature = max(self.target_temperature,
                               self.temperature - (1 / math.sqrt(self.temp_outside - self.temperature + 1)))
        self.freezer_temperature = max(self.freezer_target_temperature, self.freezer_temperature - (1 / math.sqrt(
            self.temp_outside - self.freezer_temperature + 1
        )))

    def cool_turn_off(self):
        self.temperature = min(self.temp_outside,
                               self.temperature + 0.2 * math.sqrt(self.temp_outside - self.temperature + 1))
        self.freezer_temperature = min(self.temp_outside, self.freezer_temperature + 0.2 * math.sqrt(
            self.temp_outside - self.freezer_temperature + 1))

    def defrost(self):
        self.temperature = min(self.temp_outside, self.temperature + 1)
        self.freezer_temperature = min(self.freezer_target_temperature, self.freezer_temperature + 1)

    def increase_temp(self):
        self.target_temperature = min(self.max_temperature, self.target_temperature + 1)

    def decrease_temp(self):
        self.target_temperature = max(self.min_temperature, self.target_temperature - 1)

    def open_door(self):
        self.is_door_open = True

    def close_door(self):
        self.is_door_open = False

    def open_freezer_door(self):
        self.is_freezer_door_open = True

    def close_freezer_door(self):
        self.is_freezer_door_open = False

    def turn_on(self):
        self.is_turn_on = True

    def turn_off(self):
        self.is_turn_on = False

    def is_need_high_cool(self):
        return self.temperature > self.target_temperature or self.freezer_temperature > self.freezer_target_temperature

    def is_need_low_cool(self):
        return self.temperature < self.target_temperature or self.freezer_temperature < self.freezer_target_temperature


class RefrigeratorFSM:
    def __init__(self, refrigerator):
        self.state = State.OFF
        self.refrigerator = refrigerator

    def send_signal(self, signal):
        if self.state == State.MALFUNCTION:
            return
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
        elif self.state == State.HIGH_COOLING:
            if signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
        elif self.state == State.THREAT_FAILURE:
            if signal == Signal.DOOR_OPEN_MORE_THAN_120:
                self.state = State.MALFUNCTION
            elif signal == Signal.CLOSE_DOOR:
                self.state = State.COOLING
        elif self.state == State.DEFROSTING:
            if signal == Signal.CLOSE_DOOR:
                self.state = State.OFF

        if self.state != State.OFF and (self.state != State.MALFUNCTION or self.state != State.THREAT_FAILURE):
            if signal == Signal.INCREASE_TEMPERATURE:
                self.refrigerator.increase_temp()
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.refrigerator.decrease_temp()

        if signal == Signal.TURN_OFF:
            self.state = State.OFF

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
            self.refrigerator.cool_turn_off()
        elif not self.refrigerator.is_turn_on:
            self.refrigerator.turn_on()

        if (
                self.state == State.LOW_COOLING or
                self.state == State.HIGH_COOLING or
                self.state == State.COOLING
        ):
            if self.refrigerator.is_need_high_cool():
                self.state = State.HIGH_COOLING
            elif self.refrigerator.is_need_low_cool():
                self.state = State.LOW_COOLING
            else:
                self.state = State.COOLING

        if self.state == State.COOLING:
            self.refrigerator.cool()

        elif self.state == State.LOW_COOLING:
            self.refrigerator.low_cool()

        elif self.state == State.HIGH_COOLING:
            self.refrigerator.high_cool()

        elif self.state == State.DEFROSTING:
            self.refrigerator.defrost()
        elif self.state == State.MALFUNCTION:
            self.refrigerator.cool_turn_off()


class Timer:
    def __init__(self, fsm):
        self.time = 0
        self.fsm = fsm
        self.is_started = False

    def update(self):
        if not self.is_started:
            return
        self.time += 1

        # if self.time > 30:
        #     self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_30)
        # elif self.time > 120:
        #     self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_120)
        if self.time > 3:
            self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_30)
        if self.time > 10:
            self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_120)
        if self.fsm.state == State.OFF:
            self.stop()

    def start(self):
        self.is_started = True
        self.reset()

    def stop(self):
        self.is_started = False
        self.reset()

    def reset(self):
        self.time = 0


class Product:
    PRODUCTS = ["Молоко", "Яйца", "Колбаса", "Сыр", "Масло подсолнечное", "Варенье", "Пельмени", "Мясо"]

    def __init__(self, name, expiry_date):
        self.name = name
        self.expiry_date = expiry_date

    def __str__(self):
        return f"{self.name}, {self.expiry_date}"

    def __repr__(self):
        return f"{self.name}, {self.expiry_date}"

    def to_dict(self):
        return {
            "name": self.name,
            "expiry_date": self.expiry_date,
        }

    def is_expired(self):
        return datetime.strptime(self.expiry_date, "%d.%m.%Y") < datetime.now()

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            expiry_date=data["expiry_date"],
        )

    @staticmethod
    def validate_expiry_date(date_str):
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_quantity(quantity):
        try:
            qty = int(quantity)
            return qty > 0
        except ValueError:
            return False

    @staticmethod
    def validate_weight(weight):
        try:
            wgt = float(weight)
            return wgt > 0
        except ValueError:
            return False


class BaseProductWindow(tk.Toplevel):
    def __init__(self, root, title):
        super().__init__(root)
        self.title(title)
        self.geometry("400x400")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.transient(root)

        self.main_frame = tk.Frame(self, pady=10, padx=10)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        self.validation_errors = {}

    @staticmethod
    def create_label_entry(label_text, parent):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        label = tk.Label(frame, text=label_text)
        label.pack(anchor="w")

        entry = tk.Entry(frame)
        entry.pack(fill=tk.X)

        error_label = tk.Label(frame, text="", foreground="red")
        error_label.pack(anchor="w")

        return entry, error_label

    def show_error(self, field, error_label, message):
        self.validation_errors[field] = True
        error_label.config(text=message)

    def clear_error(self, field, error_label):
        self.validation_errors.pop(field, None)
        error_label.config(text="")

    def validate_form(self):
        return len(self.validation_errors) == 0


class AddProductWindow(BaseProductWindow):
    def __init__(self, root, on_add_callback):
        self.on_add_callback = on_add_callback
        super().__init__(root, "Добавление продукта")

        product_frame = tk.Frame(self.main_frame)
        product_frame.pack(fill=tk.X, pady=5)
        tk.Label(product_frame, text="Выберите продукт:").pack(anchor="w")
        self.product_combo = ttk.Combobox(product_frame, values=Product.PRODUCTS, state="readonly")
        self.product_combo.pack(fill=tk.X)
        self.product_combo.current(0)

        self.expiry_entry, self.expiry_error = self.create_label_entry("Срок годности (ДД.ММ.ГГГГ):", self.main_frame)
        self.expiry_entry.bind('<KeyRelease>', self.validate_expiry)

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        tk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Добавить", command=self.add_product).pack(side=tk.RIGHT)

    def validate_expiry(self, event=None):
        date_str = self.expiry_entry.get().strip()
        if not date_str:
            self.show_error('expiry', self.expiry_error, "Срок годности обязателен")
        elif not Product.validate_expiry_date(date_str):
            self.show_error('expiry', self.expiry_error, "Неверный формат даты")
        else:
            self.clear_error('expiry', self.expiry_error)

    def add_product(self):
        self.validate_expiry()

        if not self.validate_form():
            messagebox.showerror("Ошибка", "Пожалуйста, исправьте ошибки в форме")
            return

        try:
            product = Product(
                name=self.product_combo.get(),
                expiry_date=self.expiry_entry.get().strip(),
            )

            self.on_add_callback(product)
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить продукт: {str(e)}")


class RemoveProductWindow(BaseProductWindow):
    def __init__(self, root, products, on_remove_callback):
        self.products = products
        self.on_remove_callback = on_remove_callback
        super().__init__(root, "Удаление продукта")

        products_frame = tk.Frame(self.main_frame)
        products_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        tk.Label(products_frame, text="Выберите продукты для удаления:").pack(anchor="w")

        self.tree = ttk.Treeview(products_frame, columns=("name", "expiry"), show="headings", selectmode="extended")

        self.tree.heading("name", text="Название")
        self.tree.heading("expiry", text="Срок годности")

        self.tree.column("name", width=100)
        self.tree.column("expiry", width=100)

        scrollbar = tk.Scrollbar(products_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        tk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Удалить выбранные", command=self.remove_products).pack(side=tk.RIGHT)

        self.update_product_list()

    def update_product_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for product in self.products:
            self.tree.insert("", "end", values=(
                product.name,
                product.expiry_date,
            ))

    def remove_products(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Предупреждение", "Выберите продукты для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить выбранные продукты?"):
            selected_products = []
            for item in selected_items:
                values = self.tree.item(item)["values"]
                selected_products.append(values[0])

            self.on_remove_callback(selected_products)
            self.destroy()


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

        self.refrigerator_open_img = PhotoImage(file="refrigerator_open.png")
        self.refrigerator_close_off_img = PhotoImage(file="refrigerator_off.png")
        self.refrigerator_close_on_img = PhotoImage(file="refrigerator_on.png")

        self.temp_display_width = 80
        self.temp_display_height = 30
        self.temp_display_x = 65
        self.temp_display_y = 180

        container_frame = tk.Frame(root)
        container_frame.pack()

        self.canvas = tk.Canvas(container_frame, width=600, height=800)
        self.canvas.pack(side=tk.LEFT)

        right_side_frame = tk.Frame(container_frame, width=300, height=512)
        right_side_frame.pack(anchor=tk.N, side=tk.RIGHT, pady=10, padx=10)

        control_frame = tk.Frame(right_side_frame)
        control_frame.pack()

        self.state_label = tk.Label(control_frame, text=f"Состояние: {self.fsm.state.name_ru}")
        self.state_label.pack(anchor=tk.W)

        self.outside_temp_label = tk.Label(control_frame, text=f"Температура снаружи: {self.temp_outside}°C")
        self.outside_temp_label.pack(anchor=tk.W)

        self.target_temp_label = tk.Label(control_frame,
                                          text=f"Заданная температура: {self.refrigerator.target_temperature}°C")
        self.target_temp_label.pack(anchor=tk.W)

        self.temp_label = tk.Label(control_frame, text=f"Текущая температура: {self.refrigerator.temperature}°C")
        self.temp_label.pack(anchor=tk.W)

        self.freezer_temp_label = tk.Label(control_frame, text=f"Текущая температура морозилки: {self.refrigerator.freezer_temperature}°C")
        self.freezer_temp_label.pack(anchor=tk.W)

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

        tk.Button(control_frame, text="Добавить продукт", command=self.add_product).pack(fill=tk.X)
        tk.Button(control_frame, text="Удалить продукт", command=self.remove_product).pack(fill=tk.X)

        self.expired_products_frame = tk.Frame(right_side_frame, pady=10)
        self.expired_products_frame.pack(fill=tk.X)

        self.expired_products_label = tk.Label(self.expired_products_frame, text="Просроченные продукты:")
        self.expired_products_label.pack(anchor=tk.W)

        for product in self.get_expired_products():
            tk.Label(self.expired_products_frame, text=f"{product.name} | {product.expiry_date}").pack(anchor=tk.W)

        self.canvas.bind("<Button-1>", self.on_click)

        self.draw()
        self.update()

    def draw(self):
        self.canvas.delete('all')

        self.draw_refrigerator()

    def add_product(self):
        AddProductWindow(self.root, on_add_callback=lambda value: print(value))

    def remove_product(self):
        products = self.get_products()
        RemoveProductWindow(self.root, products, on_remove_callback=lambda value: print(value))

    def get_products(self):
        return [Product(name, f"01.01.20{random.randint(23, 25)}") for name in Product.PRODUCTS]

    def get_expired_products(self):
        return [product for product in self.get_products() if product.is_expired()]

    def draw_refrigerator(self):
        if self.refrigerator.is_door_open:
            self.draw_open_door()
        else:
            self.draw_close_door()

    def draw_open_door(self):
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.refrigerator_open_img)

    def draw_close_door(self):
        self.canvas.create_image(0, 0, anchor=tk.NW,
                                 image=self.refrigerator_close_on_img if self.refrigerator.is_turn_on else self.refrigerator_close_off_img)

        self.temp_display = self.canvas.create_rectangle(
            self.temp_display_x, self.temp_display_y,
            self.temp_display_width + self.temp_display_x,
            self.temp_display_height + self.temp_display_y,
            fill='black'
        )

        temp_text_x = self.temp_display_x + self.temp_display_width / 2
        temp_text_y = self.temp_display_y + self.temp_display_height / 2
        self.temp_text = self.canvas.create_text(temp_text_x, temp_text_y,
                                                 text=f"{self.refrigerator.temperature:.0f}°C")

        # status_indicator_x = 36
        # status_indicator_y = 183
        # status_indicator_width = 25
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
        self.freezer_temp_label.config(text=f"Текущая температура морозилки: {self.refrigerator.freezer_temperature:.0f}°C")

        if self.refrigerator.temperature <= 0:
            color = 'cyan'
        else:
            color = 'lightgreen'
        self.canvas.itemconfig(self.temp_text, fill=color)

        # if  self.fsm.state == State.OFF or self.fsm.state == State.MALFUNCTION:
        #     self.canvas.itemconfig(self.status_indicator, fill='white')
        # elif  self.fsm.state != State.OFF or  self.fsm.state != State.MALFUNCTION:
        #     self.canvas.itemconfig(self.status_indicator, fill='green')

        self.fsm.update()
        self.timer.update()
        self.signaling.update()
        self.root.after(1000, self.update)

    def open_door(self):
        if not self.refrigerator.is_door_open:
            self.fsm.send_signal(Signal.OPEN_DOOR)
            self.refrigerator.open_door()
        if not self.fsm.state == State.OFF:
            self.timer.start()

    def close_door(self):
        if self.refrigerator.is_door_open:
            self.fsm.send_signal(Signal.CLOSE_DOOR)
            self.refrigerator.close_door()
            self.timer.stop()

    def turn_on(self):
        self.fsm.send_signal(Signal.TURN_ON)
        if self.refrigerator.is_door_open:
            self.timer.start()

    def turn_off(self):
        self.fsm.send_signal(Signal.TURN_OFF)

    def increase_temp(self):
        self.fsm.send_signal(Signal.INCREASE_TEMPERATURE)

    def decrease_temp(self):
        self.fsm.send_signal(Signal.DECREASE_TEMPERATURE)

    def on_click(self, event):
        print(event.x, event.y)


if __name__ == "__main__":
    root = tk.Tk()
    app = RefrigeratorApp(root)
    root.mainloop()
