import math
import random
import tkinter as tk
import uuid
import winsound
from datetime import datetime
from enum import Enum
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

        if self.fsm.state == State.OFF or ((not self.fsm.state == State.THREAT_FAILURE) and self.playing_audio
                                           and not self.fsm.refrigerator.is_door_open) or self.fsm.state == State.MALFUNCTION:
            self.stop_audio()

    def play_audio(self):
        self.playing_audio = True
        winsound.PlaySound(self.file_name, winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC)

    def stop_audio(self):
        self.playing_audio = False
        winsound.PlaySound(None, winsound.SND_PURGE)


class State(Enum):
    OFF = "ОТКЛЮЧЕН"
    COOLING = "НОРМАЛЬНОЕ ОХЛАЖДЕНИЕ"
    HIGH_COOLING = "СИЛЬНОЕ ОХЛАЖДЕНИЕ"
    LOW_COOLING = "СЛАБОЕ ОХЛАЖДЕНИЕ"
    THREAT_FAILURE = "УГРОЗА ПОЛОМКИ"
    MALFUNCTION = "НЕИСПРАВНОСТЬ"
    DEFROSTING = "РАЗМОРОКА"


class Signal(Enum):
    TURN_ON = "ВКЛЮЧИТЬ"
    TURN_OFF = "ВЫКЛЮЧИТЬ"
    INCREASE_TEMPERATURE = "ПОВЫСИТЬ ТЕМПЕРАТУРУ"
    DECREASE_TEMPERATURE = "ПОНИЗИТЬ ТЕМПЕРАТУРУ"
    OPEN_DOOR_TOP = "ОТКРЫТЬ ВЕРХНЮЮ ДВЕРЬ"
    OPEN_DOOR_LOWER = "ОТКРЫТЬ НИЖНЮЮ ДВЕРЬ"
    CLOSE_DOOR_TOP = "ЗАКРЫТЬ ВЕРХНЮЮ ДВЕРЬ"
    CLOSE_DOOR_LOWER = "ЗАКРЫТЬ НИЖНЮЮ ДВЕРЬ"
    DOOR_OPEN_MORE_THAN_30 = "ДВЕРЬ ОТКРЫТА БОЛЬШЕ 30 СЕКУНД"
    DOOR_OPEN_MORE_THAN_120 = "ДВЕРЬ ОТКРЫТА БОЛЬШЕ 120 СЕКУНД"
    REPAIR = "ПОЧИНИТЬ"


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
        if self.state == State.OFF:
            if signal == Signal.TURN_ON:
                self.state = State.COOLING
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
        elif self.state == State.COOLING:
            if signal == Signal.INCREASE_TEMPERATURE:
                self.refrigerator.increase_temp()
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.refrigerator.decrease_temp()
            elif signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
        elif self.state == State.COOLING:
            if signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.INCREASE_TEMPERATURE:
                self.refrigerator.increase_temp()
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.refrigerator.decrease_temp()
        elif self.state == State.LOW_COOLING:
            if signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.INCREASE_TEMPERATURE:
                self.refrigerator.increase_temp()
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.refrigerator.decrease_temp()
        elif self.state == State.HIGH_COOLING:
            if signal == Signal.DOOR_OPEN_MORE_THAN_30:
                self.state = State.THREAT_FAILURE
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
            elif signal == Signal.INCREASE_TEMPERATURE:
                self.refrigerator.increase_temp()
            elif signal == Signal.DECREASE_TEMPERATURE:
                self.refrigerator.decrease_temp()
        elif self.state == State.THREAT_FAILURE:
            if signal == Signal.DOOR_OPEN_MORE_THAN_120:
                self.state = State.MALFUNCTION
            elif signal == Signal.CLOSE_DOOR_TOP and not self.refrigerator.is_freezer_door_open:
                self.state = State.COOLING
            elif signal == Signal.CLOSE_DOOR_LOWER and not self.refrigerator.is_door_open:
                self.state = State.COOLING
            elif signal == Signal.TURN_OFF:
                self.state = State.OFF
        elif self.state == State.MALFUNCTION:
            if signal == Signal.REPAIR:
                self.state = State.COOLING

    def update(self):
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
        self.time_to_threat_failure = 30
        self.time_to_malfunction = 120

    def update(self):
        if not self.is_started:
            return
        self.time += 1

        if self.time > self.time_to_threat_failure:
            self.fsm.send_signal(Signal.DOOR_OPEN_MORE_THAN_30)
        if self.time > self.time_to_malfunction:
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
        self.id = str(uuid.uuid4())
        self.name = name
        self.expiry_date = expiry_date

    def __str__(self):
        return f"name:{self.name}, expiry_date:{self.expiry_date}"

    def __repr__(self):
        return f"name:{self.name}, expiry_date:{self.expiry_date}"

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


class BaseWindow(tk.Toplevel):
    def __init__(self, root, title):
        super().__init__(root)
        w, h = 400, 400
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.transient(root)

        self.main_frame = tk.Frame(self, pady=10, padx=10)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        self.validation_errors = {}

    @staticmethod
    def create_label_entry(label_text, parent, default_value=""):
        frame = tk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        label = tk.Label(frame, text=label_text)
        label.pack(anchor="w")

        entry = tk.Entry(frame, textvariable=tk.StringVar(value=default_value))
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


class AddProductWindow(BaseWindow):
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


class RemoveProductWindow(BaseWindow):
    def __init__(self, root, products, on_remove_callback):
        self.products = products
        self.on_remove_callback = on_remove_callback
        super().__init__(root, "Удаление продукта")

        products_frame = tk.Frame(self.main_frame)
        products_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        tk.Label(products_frame, text="Выберите продукты для удаления:").pack(anchor="w")

        self.tree = ttk.Treeview(products_frame,
                                 columns=("id", "name", "expiry"),
                                 show="headings",
                                 selectmode="extended",
                                 displaycolumns=("name", "expiry")
                                 )

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
                product.id,
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


class SettingsAppWindow(BaseWindow):
    def __init__(self, root, timer):
        super().__init__(root, "Настройки")
        self.timer = timer
        product_frame = tk.Frame(self.main_frame)
        product_frame.pack(fill=tk.X, pady=5)

        self.expiry_entry_1, self.expiry_error_1 = self.create_label_entry("Время до угрозы поломки:", self.main_frame, self.timer.time_to_threat_failure)
        self.expiry_entry_1.bind('<KeyRelease>', self.validate_time_to_threat_failure)

        self.expiry_entry_2, self.expiry_error_2 = self.create_label_entry("Время до поломки:", self.main_frame, self.timer.time_to_malfunction)
        self.expiry_entry_2.bind('<KeyRelease>', self.validate_time_to_malfunction)

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        tk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Применить", command=self.apply_settings).pack(side=tk.RIGHT)

    def validate_time_to_threat_failure(self, event=None):
        date_str = self.expiry_entry_1.get().strip()
        if not (date_str.isdigit() and int(date_str) > 0):
            self.show_error('expiry', self.expiry_error_1, "время должно быть целым и больше нуля")
        else:
            self.clear_error('expiry', self.expiry_error_1)

    def validate_time_to_malfunction(self, event=None):
        time_to_threat_failure = self.expiry_entry_1.get().strip()
        date_str = self.expiry_entry_2.get().strip()
        if not (time_to_threat_failure.isdigit() and (
                date_str.isdigit() and int(date_str) > int(time_to_threat_failure))):
            self.show_error('expiry', self.expiry_error_2, "время должно быть целым и больше времени до угрозы поломки")
        else:
            self.clear_error('expiry', self.expiry_error_2)

    def apply_settings(self):
        self.validate_time_to_threat_failure()
        self.validate_time_to_malfunction()

        if not self.validate_form():
            messagebox.showerror("Ошибка", "Пожалуйста, исправьте ошибки в форме")
            return

        try:
            self.timer.time_to_threat_failure = int(self.expiry_entry_1.get().strip())
            self.timer.time_to_malfunction = int(self.expiry_entry_2.get().strip())
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить настройки: {str(e)}")


class RefrigeratorApp:
    def __init__(self, root):
        self.root = root
        # width = self.root.winfo_screenwidth()
        # height = self.root.winfo_screenheight()
        # self.root.geometry("%dx%d" % (width, height))
        w, h = 1280, 800
        ws = root.winfo_screenwidth()
        hs = root.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.root.title("Кончный Автомат Холодильника")

        self.temp_outside = 25
        self.refrigerator = Refrigerator(self.temp_outside)
        self.fsm = RefrigeratorFSM(self.refrigerator)
        self.timer = Timer(self.fsm)
        self.signaling = Signaling(self.fsm)

        self.products = self.load_products()

        self.refrigerator_open_on_img = PhotoImage(file="refrigerator_on_open.png")
        self.refrigerator_open_off_img = PhotoImage(file="refrigerator_off_open.png")
        self.refrigerator_close_off_img = PhotoImage(file="refrigerator_off_close.png")
        self.refrigerator_close_on_img = PhotoImage(file="refrigerator_on_close.png")
        self.refrigerator_open_on_top_img = PhotoImage(file="refrigerator_on_open_top.png")
        self.refrigerator_open_off_top_img = PhotoImage(file="refrigerator_off_open_top.png")
        self.refrigerator_open_on_lower_img = PhotoImage(file="refrigerator_on_open_lower.png")
        self.refrigerator_open_off_lower_img = PhotoImage(file="refrigerator_off_open_lower.png")

        self.image_milk_path = PhotoImage(file="image_food/Empty.png")
        self.image_kolb_path = PhotoImage(file="image_food/Empty.png")
        self.image_egg_path = PhotoImage(file="image_food/Empty.png")
        self.image_cheese_path = PhotoImage(file="image_food/Empty.png")
        self.image_oil_path = PhotoImage(file="image_food/Empty.png")
        self.image_jam_path = PhotoImage(file="image_food/Empty.png")
        self.image_meat_path = PhotoImage(file="image_food/Empty.png")
        self.image_pelmen_path = PhotoImage(file="image_food/Empty.png")

        menu_bar = tk.Menu(root)
        menu_bar.add_command(label="Настройки", command=self.open_settings)
        root.config(menu=menu_bar)

        self.temp_display_width = 80
        self.temp_display_height = 30
        self.temp_display_x = 65
        self.temp_display_y = 180

        self.food_position_x = 50
        self.food_position_y = 340

        container_frame = tk.Frame(root)
        container_frame.pack()

        self.canvas = tk.Canvas(container_frame, width=600, height=800)
        self.canvas.pack(side=tk.LEFT)

        right_side_frame = tk.Frame(container_frame)
        right_side_frame.pack(fill=tk.BOTH, anchor=tk.N, side=tk.RIGHT, pady=10, padx=10)

        control_frame = tk.Frame(right_side_frame, width=275)
        control_frame.pack(fill=tk.BOTH, expand=tk.TRUE)
        control_frame.pack_propagate(tk.OFF)

        self.state_label = tk.Label(control_frame, text=f"Состояние: {self.fsm.state.value}")
        self.state_label.pack(anchor=tk.W)

        self.outside_temp_label = tk.Label(control_frame, text=f"Температура снаружи: {self.temp_outside}°C")
        self.outside_temp_label.pack(anchor=tk.W)

        self.target_temp_label = tk.Label(control_frame,
                                          text=f"Заданная температура: {self.refrigerator.target_temperature}°C")
        self.target_temp_label.pack(anchor=tk.W)

        self.temp_label = tk.Label(control_frame, text=f"Текущая температура: {self.refrigerator.temperature}°C")
        self.temp_label.pack(anchor=tk.W)

        self.freezer_temp_label = tk.Label(control_frame,
                                           text=f"Текущая температура морозилки: {self.refrigerator.freezer_temperature}°C")
        self.freezer_temp_label.pack(anchor=tk.W)

        buttons = [
            (Signal.TURN_ON.value, self.turn_on),
            (Signal.TURN_OFF.value, self.turn_off),
            (Signal.INCREASE_TEMPERATURE.value, self.increase_temp),
            (Signal.DECREASE_TEMPERATURE.value, self.decrease_temp),
            (Signal.OPEN_DOOR_TOP.value, self.open_door_top),
            (Signal.CLOSE_DOOR_TOP.value, self.close_door_top),
            (Signal.OPEN_DOOR_LOWER.value, self.open_door_lower),
            (Signal.CLOSE_DOOR_LOWER.value, self.close_door_lower),
            (Signal.REPAIR.value, self.repair),
        ]

        for text, command in buttons:
            tk.Button(control_frame, text=text, command=command).pack(pady=2, fill=tk.X)

        tk.Button(control_frame, text="ДОБАВИТЬ ПРОДУКТ", command=self.add_product).pack(pady=2, fill=tk.X)
        tk.Button(control_frame, text="УДАЛИТЬ ПРОДУКТ", command=self.remove_product).pack(pady=2, fill=tk.X)

        self.expired_products_frame = tk.Frame(control_frame, pady=10)
        self.expired_products_frame.pack(fill=tk.X)

        self.expired_products_label = tk.Label(self.expired_products_frame, text="Просроченные продукты:")
        self.expired_products_label.pack(anchor=tk.W)

        self.expired_products = []
        self.update_expired_products()

        self.canvas.bind("<Button-1>", self.on_click)

        self.draw()
        self.update()

    def open_settings(self):
        SettingsAppWindow(self.root, self.timer)

    def draw(self):
        self.canvas.delete('all')

        self.draw_refrigerator()

    def update(self):
        self.draw()

        self.update_food()
        top, lower = self.refrigerator.is_door_open, self.refrigerator.is_freezer_door_open
        if top:
            self.draw_food()
        if lower:
            self.draw_freezer_food()

        self.state_label.config(text=f"Состояние: {self.fsm.state.value}")
        self.temp_label.config(text=f"Текущая температура: {self.refrigerator.temperature:.0f}°C")
        self.target_temp_label.config(text=f"Заданная температура: {self.refrigerator.target_temperature:.0f}°C")
        self.freezer_temp_label.config(
            text=f"Текущая температура морозилки: {self.refrigerator.freezer_temperature:.0f}°C")

        # if  self.fsm.state == State.OFF or self.fsm.state == State.MALFUNCTION:
        #     self.canvas.itemconfig(self.status_indicator, fill='white')
        # elif  self.fsm.state != State.OFF or  self.fsm.state != State.MALFUNCTION:
        #     self.canvas.itemconfig(self.status_indicator, fill='green')

        self.fsm.update()
        self.timer.update()
        self.signaling.update()
        self.root.after(1000, self.update)

    def draw_food(self):
        self.canvas.create_image(self.food_position_x, self.food_position_y, anchor=tk.NW, image=self.image_milk_path)
        if self.count_milk > 1:
            self.canvas.create_text(self.food_position_x, self.food_position_y, text=self.count_milk, anchor=tk.NW,
                                    fill="black", font=("Helvetica", 14))

        self.canvas.create_image(self.food_position_x + 40, self.food_position_y, anchor=tk.NW,
                                 image=self.image_egg_path)
        if self.count_egg > 1:
            self.canvas.create_text(self.food_position_x + 40, self.food_position_y, text=self.count_egg, anchor=tk.NW,
                                    fill="black", font=("Helvetica", 14))

        self.canvas.create_image(self.food_position_x + (50 * 2), self.food_position_y, anchor=tk.NW,
                                 image=self.image_kolb_path)
        if self.count_kolb > 1:
            self.canvas.create_text(self.food_position_x + (50 * 2), self.food_position_y, text=self.count_kolb,
                                    anchor=tk.NW, fill="black", font=("Helvetica", 14))

        self.canvas.create_image(self.food_position_x, self.food_position_y + 100, anchor=tk.NW,
                                 image=self.image_jam_path)
        if self.count_jam > 1:
            self.canvas.create_text(self.food_position_x, self.food_position_y + 100, text=self.count_jam, anchor=tk.NW,
                                    fill="black", font=("Helvetica", 14))

        self.canvas.create_image(self.food_position_x + 50, self.food_position_y + 100, anchor=tk.NW,
                                 image=self.image_oil_path)
        if self.count_oil > 1:
            self.canvas.create_text(self.food_position_x + 50, self.food_position_y + 100, text=self.count_oil,
                                    anchor=tk.NW, fill="black", font=("Helvetica", 14))

        self.canvas.create_image(self.food_position_x + (50 * 2), self.food_position_y + 100, anchor=tk.NW,
                                 image=self.image_cheese_path)
        if self.count_cheese > 1:
            self.canvas.create_text(self.food_position_x + (50 * 2), self.food_position_y + 100, text=self.count_cheese,
                                    anchor=tk.NW, fill="black", font=("Helvetica", 14))

    def draw_freezer_food(self):
        self.canvas.create_image(self.food_position_x + 5, self.food_position_y + 210, anchor=tk.NW,
                                 image=self.image_pelmen_path)
        if self.count_pelmen > 1:
            self.canvas.create_text(self.food_position_x + 5, self.food_position_y + 210, text=self.count_pelmen,
                                    anchor=tk.NW, fill="black", font=("Helvetica", 14))

        self.canvas.create_image(self.food_position_x + 5, self.food_position_y + 290, anchor=tk.NW,
                                 image=self.image_meat_path)
        if self.count_meat > 1:
            self.canvas.create_text(self.food_position_x + 5, self.food_position_y + 290, text=self.count_meat,
                                    anchor=tk.NW, fill="black", font=("Helvetica", 14))

    def update_food(self):
        PRODUCTS = ["Молоко", "Яйца", "Колбаса", "Сыр", "Масло подсолнечное", "Варенье", "Пельмени", "Мясо"]
        self.count_milk = len([prod for prod in self.products if prod.name == PRODUCTS[0]])
        self.count_egg = len([prod for prod in self.products if prod.name == PRODUCTS[1]])
        self.count_kolb = len([prod for prod in self.products if prod.name == PRODUCTS[2]])
        self.count_cheese = len([prod for prod in self.products if prod.name == PRODUCTS[3]])
        self.count_oil = len([prod for prod in self.products if prod.name == PRODUCTS[4]])
        self.count_jam = len([prod for prod in self.products if prod.name == PRODUCTS[5]])
        self.count_pelmen = len([prod for prod in self.products if prod.name == PRODUCTS[6]])
        self.count_meat = len([prod for prod in self.products if prod.name == PRODUCTS[7]])

        if self.count_milk == 0:
            self.image_milk_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_milk_path = PhotoImage(file="image_food/milk_1.png")

        if self.count_egg == 0:
            self.image_egg_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_egg_path = PhotoImage(file="image_food/egg_1.png")

        if self.count_kolb == 0:
            self.image_kolb_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_kolb_path = PhotoImage(file="image_food/kolb_1.png")

        if self.count_cheese == 0:
            self.image_cheese_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_cheese_path = PhotoImage(file="image_food/cheese_1.png")

        if self.count_oil == 0:
            self.image_oil_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_oil_path = PhotoImage(file="image_food/oil_1.png")

        if self.count_jam == 0:
            self.image_jam_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_jam_path = PhotoImage(file="image_food/jam_1.png")

        if self.count_meat == 0:
            self.image_meat_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_meat_path = PhotoImage(file="image_food/meat_1.png")

        if self.count_pelmen == 0:
            self.image_pelmen_path = PhotoImage(file="image_food/Empty.png")
        else:
            self.image_pelmen_path = PhotoImage(file="image_food/pelm_1.png")

    def add_product(self):
        AddProductWindow(self.root, on_add_callback=lambda value: self.set_products(self.products + [value]))

    def remove_product(self):
        RemoveProductWindow(self.root, self.products,
                            on_remove_callback=lambda value: self.set_products(self.filter_products(value)))

    def set_products(self, products):
        self.products = products
        self.update_expired_products()

    def update_expired_products(self):
        for p in self.expired_products:
            p.destroy()
        self.expired_products = []
        for product in self.get_expired_products():
            p_label = tk.Label(self.expired_products_frame, text=f"{product.name} | {product.expiry_date}")
            p_label.pack(anchor=tk.W)
            self.expired_products.append(p_label)

    def filter_products(self, product_ids):
        filtered_products = [product for product in self.products if not (product.id in product_ids)]
        return filtered_products

    def load_products(self):
        return [Product(name, f"01.01.20{random.randint(23, 25)}") for name in Product.PRODUCTS]

    def get_expired_products(self):
        return [product for product in self.products if product.is_expired()]

    def draw_refrigerator(self):
        top, lower = self.refrigerator.is_door_open, self.refrigerator.is_freezer_door_open
        if top and lower:
            self.draw_open_door()
        elif not top and not lower:
            self.draw_close_door()
        elif top:
            self.draw_open_door_top()
        elif lower:
            self.draw_open_door_lower()

    def draw_open_door(self):
        img = self.refrigerator_open_on_img if self.refrigerator.is_turn_on and self.fsm.state != State.MALFUNCTION else self.refrigerator_open_off_img
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)

    def draw_open_door_top(self):
        img = self.refrigerator_open_on_top_img if self.refrigerator.is_turn_on and self.fsm.state != State.MALFUNCTION else self.refrigerator_open_off_top_img
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)

    def draw_open_door_lower(self):
        img = self.refrigerator_open_on_lower_img if self.refrigerator.is_turn_on else self.refrigerator_open_off_lower_img
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.draw_temp_display()

    def draw_close_door(self):
        if self.fsm.state == State.MALFUNCTION:
            image = self.refrigerator_close_off_img
        elif self.refrigerator.is_turn_on:
            image = self.refrigerator_close_on_img
        else:
            image = self.refrigerator_close_off_img
        self.canvas.create_image(0, 0, anchor=tk.NW, image=image)

        self.draw_temp_display()

    def draw_temp_display(self):
        self.canvas.create_rectangle(
            self.temp_display_x, self.temp_display_y,
            self.temp_display_width + self.temp_display_x,
            self.temp_display_height + self.temp_display_y,
            fill='black'
        )

        if self.refrigerator.is_turn_on and self.fsm.state != State.MALFUNCTION:
            temp_text_x = self.temp_display_x + self.temp_display_width / 2
            temp_text_y = self.temp_display_y + self.temp_display_height / 2
            if self.refrigerator.temperature <= 0:
                color = 'cyan'
            else:
                color = 'lightgreen'
            self.canvas.create_text(temp_text_x, temp_text_y, text=f"{self.refrigerator.temperature:.0f}°C", fill=color)

    def open_door_top(self):
        if not self.refrigerator.is_door_open:
            self.fsm.send_signal(Signal.OPEN_DOOR_TOP)
            self.refrigerator.open_door()
        if not self.fsm.state == State.OFF and not self.timer.is_started:
            self.timer.start()

    def close_door_top(self):
        if self.refrigerator.is_door_open:
            self.fsm.send_signal(Signal.CLOSE_DOOR_TOP)
            self.refrigerator.close_door()
            self.timer.stop()

    def open_door_lower(self):
        if not self.refrigerator.is_freezer_door_open:
            self.fsm.send_signal(Signal.OPEN_DOOR_LOWER)
            self.refrigerator.open_freezer_door()
        if not self.fsm.state == State.OFF and not self.timer.is_started:
            self.timer.start()

    def close_door_lower(self):
        if self.refrigerator.is_freezer_door_open:
            self.fsm.send_signal(Signal.CLOSE_DOOR_LOWER)
            self.refrigerator.close_freezer_door()
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

    def repair(self):
        self.fsm.send_signal(Signal.REPAIR)

    def on_click(self, event):
        print(event.x, event.y)


if __name__ == "__main__":
    root = tk.Tk()
    app = RefrigeratorApp(root)
    root.mainloop()
