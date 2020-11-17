# TODO: Сейчас выполненные задания отбираются только по дате старта, типо сегодня стартанул, значит действие сеодняшнее
# TODO: но заполняются они целиком, не рубятся до 23.59.59, то есть надо сделать чтобы при выполнении действия
# TODO: на стыки нескольких дней была разбика по действиям от 0:00 до 23:59:59

# TODO: Когда нажимаешь и держить и удаляется актион, то 2 записи в бд становится
# kivy version 1.11.1

# from kivy.config import Config
#
# Config.set('graphics', 'resizable', '1')
# Config.set('graphics', 'width', '360')
# Config.set('graphics', 'height', '640')

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.lang.builder import Builder
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import WidgetException
from datetime import datetime

from sqlite_requests import db


Builder.load_file('main.kv')


class MyScreenManager(ScreenManager):

    def __init__(self, **kwargs):
        super(MyScreenManager, self).__init__(**kwargs)

    def change_screen(self, new_screen):
        if new_screen == 'main':
            self.transition.direction = 'right'
            self.current = 'main'
        elif new_screen == 'result':
            self.transition.direction = 'left'
            self.current = 'result'


sm = MyScreenManager()


class MyActionButton(ToggleButton):
    long_press_time = Factory.NumericProperty(.5)

    def __init__(self, **kwargs):
        super(MyActionButton, self).__init__(**kwargs)

        self.date_start = 0
        self.group = 'action'
        self.my_parent = None
        self.pressing = False

    def set_in_process(self):
        if self.state == 'down':
            db.set_active(self.text, True)
        else:
            db.save_completed_action(self.text)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._clockev = Clock.schedule_once(self.remove_action, self.long_press_time)
            self.pressing = True

    def on_touch_up(self, touch):
        try:
            self._clockev.cancel()
        except AttributeError:
            pass

        if self.pressing:
            self.pressing = False
            super(MyActionButton, self).on_touch_down(touch)
        return super(MyActionButton, self).on_touch_up(touch)

    def remove_action(self, dt):
        db.save_completed_action(self.text)
        db.remove_current_action(self.text)
        self.my_parent.refresh_main_area()


class SearchTextInput(TextInput):

    def __init__(self, **kwargs):
        super(SearchTextInput, self).__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        if len(self.text) > 150:
            return True
        else:
            super(SearchTextInput, self).insert_text(substring, from_undo)


class SearchButton(Button):

    def __init__(self, **kwargs):
        super(SearchButton, self).__init__(**kwargs)


class SearchLine(BoxLayout):

    def __init__(self, **kwargs):
        super(SearchLine, self).__init__(**kwargs)

    @staticmethod
    def remove_action(action):
        db.remove_action(action)
        mb.refresh_search_actions(mb.search.text)


class RoundButton(Button):
    long_press_time = Factory.NumericProperty(.15)

    def __init__(self, **kwargs):
        super(RoundButton, self).__init__(**kwargs)

        self.my_function = None
        self.direction = ''
        self.allowed_to_move = False
        self.current_center = [Window.width * .8, Window.height * .3]
        self.touch_delta = [0, 0]

    def on_release(self):

        if self.allowed_to_move:
            self.allowed_to_move = False
            return

        if self.direction == '>':
            Clock.schedule_once(lambda *args: rb.refresh_result_area())

            open_animation = Animation(size=(Window.width/6, Window.width/6),
                                       center=rb.round_button.center.copy(), d=.6, t='out_back')
            close_animation = Animation(size=(0, 0), center=self.center.copy(), d=.2)
            close_animation.bind(on_complete=lambda *args: Clock.schedule_once(
                lambda *z: pause(self.delayed_animation, open_animation, rb.round_button, 'result'), .1))
            close_animation.start(self)

        else:
            open_animation = Animation(size=(Window.width / 6, Window.width / 6),
                                       center=mb.round_button.center.copy(), d=.6, t='out_back')
            close_animation = Animation(size=(0, 0), center=self.center.copy(), d=.2)
            close_animation.bind(on_complete=lambda *args: Clock.schedule_once(
                lambda *z: pause(self.delayed_animation, open_animation, mb.round_button, 'main'), .1))
            close_animation.start(self)

        return True

    def delayed_animation(self, animation, obj, new_screen):
        sm.change_screen(new_screen)
        Clock.schedule_once(lambda *args: animation.start(obj), .6)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._clockev = Clock.schedule_once(self.allow_to_move, self.long_press_time)
            self.touch_delta = [self.center_x - touch.x, self.center_y - touch.y]

        return super(RoundButton, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        try:
            self._clockev.cancel()
        except AttributeError:
            pass

        return super(RoundButton, self).on_touch_up(touch)

    def allow_to_move(self, *args):
        self.allowed_to_move = True

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos) and self.allowed_to_move:
            # TODO: сделать не чтобы где мышка там и центр, а чтобы изначально бралась разница touch.pos
            # TODO и центраи перемещалось так же (чтобы когда  перемещаешь за край кнопка не дергалась центом в мышку)
            self.current_center = touch.x + self.touch_delta[0], touch.y + self.touch_delta[1]

        return super(RoundButton, self).on_touch_move(touch)


def pause(func, *args):
    # TODO Зачем я это сделал? Надо понять, можно ли было использовать Clock.schedule_once
    func(*args)


class ResultLine(BoxLayout):
    long_press_time = Factory.NumericProperty(.5)

    def __init__(self, **kwargs):
        super(ResultLine, self).__init__(**kwargs)

        self.period_start = None
        self.period_finish = None
        self.action = ''

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._clockev = Clock.schedule_once(self.remove_completed_action, self.long_press_time)

        return super(ResultLine, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        try:  # self._clockev может и не быть вообще
            self._clockev.cancel()
        except AttributeError:
            pass

        return super(ResultLine, self).on_touch_up(touch)

    def remove_completed_action(self, *args):
        db.remove_completed_action(self.action, self.period_start, self.period_finish)
        rb.refresh_result_area()


class ResultSettingsDD(DropDown):

    def __init__(self, **kwargs):
        super(ResultSettingsDD, self).__init__(**kwargs)

    def change_show_variant(self, variant):
        rb.show_variant = variant
        rb.refresh_result_area()
        self.dismiss()


class MainBox(BoxLayout):

    def __init__(self, **kwargs):
        super(MainBox, self).__init__(**kwargs)

        self.main_area = self.ids.main_area
        self.search = self.ids.search
        self.drop_down = DropDown()
        self.drop_down.auto_dismiss = False
        self.round_button = RoundButton()
        self.round_button.direction = '>'

        self.main_cols = 1

        self.refresh_main_area()

    def refresh_search_actions(self, search_text):

        self.drop_down.clear_widgets()

        btn = SearchButton(text='Create new action', size_hint_y=None, height=Window.height / 10)
        btn.bind(on_press=self.create_new_action)
        self.drop_down.add_widget(btn)

        for action in db.actions(search_text):
            line = SearchLine()
            line.ids.action.text = str(action[0])
            line.ids.action.bind(on_press=self.choose_search_action)
            self.drop_down.add_widget(line)

    def choose_search_action(self, instance):
        self.drop_down.dismiss()
        self.append_current_action(instance.text, False)
        self.refresh_main_area()
        self.search.text = ""

    def show_search_actions(self, focused):
        if focused:
            try:
                self.drop_down.open(self.search)
            except WidgetException:
                # Возникает в случае, когда несколько раз вызывается открытие виджета
                pass
        else:
            self.drop_down.dismiss()

    def create_new_action(self, instance):
        if self.search.text == "":
            self.drop_down.dismiss()
            return
        db.create_new_action(self.search.text)
        self.choose_search_action(self.search)

    @staticmethod
    def append_current_action(action, in_progress=True):
        db.append_current_action(datetime.now(), action, in_progress)

    def refresh_main_area(self):

        self.main_area.clear_widgets()
        actions = db.current_actions()
        self.set_cols(len(actions))

        for action in actions:
            act_butt = MyActionButton(text=str(action[1]), state='down' if action[2] == 'True' else 'normal')
            act_butt.date_start = action[0]
            act_butt.my_parent = self
            self.main_area.add_widget(act_butt)

    def set_cols(self, qty):
        if qty > 5:
            self.main_cols = 2
        else:
            self.main_cols = 1


mb = MainBox()


class ResultBox(BoxLayout):

    def __init__(self, **kwargs):
        super(ResultBox, self).__init__(**kwargs)

        self.result_area = self.ids.result_area
        self.show_variant = 'in total'  # 'in detail', etc
        self.drop_down = ResultSettingsDD()

        self.round_button = RoundButton()
        center = self.round_button.center.copy()
        self.round_button.size = (0, 0)
        self.round_button.center = center
        self.round_button.direction = '<'

    def refresh_result_area(self, *args):
        date_start = datetime.strptime(self.ids.date_start.text, "%d.%m.%Y")
        date_start = date_start.combine(date_start.date(), date_start.min.time())
        date_finish = datetime.strptime(self.ids.date_finish.text, "%d.%m.%Y")
        date_finish = date_finish.combine(date_finish.date(), date_finish.max.time())
        results = db.results(date_start, date_finish, self.show_variant)

        self.result_area.clear_widgets()

        for result in results:

            time = int(result[1]) // 60

            if time < 1:
                continue

            action = str(result[0])

            if self.show_variant == 'in total':
                result_date_start = date_start
                result_date_finish = date_finish
                text = str(action)
            elif self.show_variant == 'in detail':
                result_date_start_str = result[2]
                result_date_finish_str = result[3]
                result_date_start = datetime.strptime(result_date_start_str, '%Y-%m-%d %H:%M:%S.%f')
                result_date_finish = datetime.strptime(result_date_finish_str, '%Y-%m-%d %H:%M:%S.%f')
                text = '{} - {}:\n{}'.format(datetime.strftime(result_date_start, '%H:%M %d.%m'),
                                             datetime.strftime(result_date_finish, '%H:%M %d.%m'),
                                             str(action))
            else:
                result_date_start = None
                result_date_finish = None
                text = str(action)
                print("Ошибка 1 main.py: не выбран вариант отображения")

            result_line = ResultLine()
            result_line.action = str(action)
            result_line.period_start = result_date_start
            result_line.period_finish = result_date_finish if self.show_variant == 'in total' else result_date_start
            result_line.ids.action.text = text

            time = int(result[1])

            time = time // 60

            result_line.ids.minutes.text = str(time % 60)  # Минуты без часов

            time = time // 60
            result_line.ids.hours.text = str(time % 24)  # Часы без дней

            time = time // 24
            result_line.ids.days.text = str(time)

            self.result_area.add_widget(result_line)

    def open_settings(self, obj):
        self.drop_down.open(obj)
        self.drop_down.auto_width = False
        self.drop_down.width = Window.width / 2
        self.drop_down.x = Window.width / 2


rb = ResultBox()


# region Screen managing
class MainScreen(Screen):

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.add_widget(mb)
        self.add_widget(mb.round_button)


class ResultScreen(Screen):

    def __init__(self, **kwargs):
        super(ResultScreen, self).__init__(**kwargs)

        self.add_widget(rb)
        self.add_widget(rb.round_button)


sm.add_widget(MainScreen(name='main'))
sm.add_widget(ResultScreen(name='result'))
# endregion


if __name__ == "__main__":
    class TimeControlApp(App):
        def __init__(self, **kwargs):
            super(TimeControlApp, self).__init__(**kwargs)

        def build(self):
            return sm


    TimeControlApp().run()
