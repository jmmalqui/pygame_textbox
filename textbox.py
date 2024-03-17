import enum
import time
import pygame

cursor_blink = pygame.event.custom_type()


class EventBroker:
    def __init__(self) -> None:
        self.event_list = {}

    def subscribe(self, event_name, callback):
        if event_name in self.event_list:
            self.event_list[event_name].append(callback)
        else:
            self.event_list[event_name] = [callback]

    def emit(self, event_name, data):
        if event_name in self.event_list:
            for callback in self.event_list[event_name]:
                callback(data)

    def unsubscribe(self, event_name):
        self.event_list.pop(event_name)


class TextBox:
    def __init__(self, e: EventBroker, rect: pygame.Rect):
        self.e = e
        self.roundness = 8
        self.rect = rect
        self.text_rect = pygame.Rect(
            self.rect.left + (self.roundness // 2),
            self.rect.top + (self.roundness // 2),
            self.rect.width - self.roundness,
            self.rect.height - self.roundness,
        )
        self.cursor = 0
        self.text: list[str] = []
        self.active = True
        self.background_color = [30, 30, 30]
        self.e.subscribe(pygame.MOUSEBUTTONDOWN, lambda data: self.toggle(data))
        self.e.subscribe(pygame.MOUSEBUTTONDOWN, lambda data: self.click(data))
        self.e.subscribe(pygame.MOUSEBUTTONUP, lambda data: self.mouseup(data))
        self.e.subscribe(pygame.MOUSEMOTION, lambda data: self.motion(data))

        self.e.subscribe(pygame.KEYDOWN, lambda data: self.text_actions(data))
        self.e.subscribe(pygame.TEXTINPUT, lambda data: self.text_input(data))
        self.e.subscribe(cursor_blink, lambda data: self.cursor_blink(data))
        self.font = pygame.font.SysFont("ubuntu", 40)
        self.text_surface = self.make_text_surface()
        self.advance = 0
        self.cursor_color = [0, 200, 255]
        self.select_started = False
        self.select_cursor_begin = self.cursor
        self.select_advance_begin = self.advance
        self.motion_click_x_start = 0

    def mouseup(self, data):
        print(self.cursor)

    def motion(self, data):
        if data.buttons[0] != 1:
            return
        pre_cursor = self.get_cursor_from_mouse_x_position(data.pos[0])
        if pre_cursor != self.cursor:
            self.motion_started = True
            self.cursor = pre_cursor

        if data.pos[0] < self.motion_click_x_start:
            self.cursor -= 1

        self.select_started = True
        self.update_advance()

    def get_cursor_from_mouse_x_position(self, mouse_x: int):
        advance = mouse_x - self.text_rect.left
        m = self.font.metrics("".join(self.text))
        accum = 0
        cursor = 0
        if advance > self.text_surface.get_width():
            self.cursor = len(self.text)
            self.update_advance()
            return self.cursor
        for idx, _ in enumerate(m):
            accum += _[4]
            if accum >= advance:
                thisadvance = m[idx][4]

                if advance - (accum - thisadvance) < thisadvance // 2:
                    cursor = idx
                else:
                    cursor = idx + 1

                break
        if cursor < 0:
            cursor == 0
        return cursor

    def click(self, data):
        # esto tiene que ser cambiado para cuando tengamos que recortar la superficie
        if not self.active:
            return
        self.motion_click_x_start = data.pos[0]
        if not self.text:
            return

        self.cursor = self.get_cursor_from_mouse_x_position(data.pos[0])
        self.select_cursor_begin = self.cursor
        self.select_advance_begin = self.advance
        if self.select_started:
            self.select_started = False
        self.update_advance()

    def cursor_blink(self, data):
        if self.cursor_color == [0, 122, 255]:
            self.cursor_color = [0, 200, 255]
        else:
            self.cursor_color = [0, 122, 255]

    def update_advance(self):
        if self.cursor == 0:
            self.advance = 0
            return
        m = self.font.metrics("".join(self.text))
        self.advance = sum(_[4] for _ in m[: self.cursor])

    def delete_selected_subtext(self):
        cursor = max(self.cursor, self.select_cursor_begin)
        for _ in range(abs(self.select_cursor_begin - self.cursor)):
            self.text.pop(cursor - 1)
            cursor -= 1
        self.cursor = min(self.cursor, self.select_cursor_begin)
        self.update_advance()
        self.text_surface = self.make_text_surface()

    def save_scrapped_text(self):
        pygame.scrap.put_text(
            "".join(
                self.text[
                    min(self.cursor, self.select_cursor_begin) : max(
                        self.cursor, self.select_cursor_begin
                    )
                ]
            )
        )

    def make_text_surface(self):
        return self.font.render("".join(self.text), True, "white")

    def text_input(self, data):
        if not self.active:
            return
        if self.select_started:
            self.delete_selected_subtext()
            self.select_started = False
        self.text.insert(self.cursor, data.text)
        self.text_surface = self.make_text_surface()

        self.cursor += 1
        self.update_advance()

    def text_actions(self, data):
        if not self.active:
            return

        if data.mod == pygame.KMOD_LCTRL and data.key == pygame.K_LEFT:
            if self.cursor == 0:
                return
            cursor = self.cursor - 1
            a_found = False
            while True:
                curr_char = self.text[cursor]
                if curr_char != " ":
                    a_found = True
                elif a_found and curr_char == " ":
                    self.cursor = cursor + 1
                    break
                if cursor == 0:
                    self.cursor = 0
                    break
                cursor -= 1
            self.update_advance()
        elif data.mod == pygame.KMOD_LCTRL and data.key == pygame.K_RIGHT:
            if self.cursor == len(self.text):
                return
            cursor = self.cursor
            a_found = False
            while True:
                curr_char = self.text[cursor]
                if curr_char != " ":
                    a_found = True

                elif a_found and curr_char == " ":
                    self.cursor = cursor
                    break
                if cursor == len(self.text) - 1:
                    self.cursor = len(self.text)
                    break
                cursor += 1
            self.update_advance()
        elif data.mod == pygame.KMOD_LCTRL and data.key == pygame.K_v:
            if self.select_started:
                self.delete_selected_subtext()
            for char in pygame.scrap.get_text():
                self.text.insert(self.cursor, char)
                self.cursor += 1
            self.text_surface = self.make_text_surface()
            self.update_advance()
            self.select_started = False
        elif data.mod == pygame.KMOD_LCTRL and data.key == pygame.K_c:
            if self.select_started:
                self.save_scrapped_text()
        elif data.mod == pygame.KMOD_LCTRL and data.key == pygame.K_x:
            if self.select_started:
                self.save_scrapped_text()
                self.delete_selected_subtext()
                self.select_started = False
        elif data.mod == pygame.KMOD_LCTRL and data.key == pygame.K_a:
            self.select_started = True
            self.select_cursor_begin = 0
            self.select_advance_begin = 0
            self.cursor = len(self.text)
            self.update_advance()
        elif data.mod == pygame.KMOD_LSHIFT and data.key == pygame.K_LEFT:
            if self.cursor == 0:
                return
            if not self.select_started:
                self.select_cursor_begin = self.cursor
                self.select_advance_begin = self.advance
            self.select_started = True
            self.cursor -= 1
            self.update_advance()
        elif data.mod == pygame.KMOD_LSHIFT and data.key == pygame.K_RIGHT:
            if self.cursor == len(self.text):
                return
            if not self.select_started:
                self.select_cursor_begin = self.cursor
                self.select_advance_begin = self.advance
            self.select_started = True
            self.cursor += 1
            self.update_advance()
        elif data.key == pygame.K_LEFT:
            if self.select_started:
                self.select_started = False
                if self.select_cursor_begin < self.cursor:
                    self.cursor = self.select_cursor_begin
                self.update_advance()
                return
            if self.cursor == 0:
                return

            self.cursor -= 1
            self.update_advance()
        elif data.key == pygame.K_RIGHT:
            if self.select_started:
                self.select_started = False
                if self.select_cursor_begin > self.cursor:
                    self.cursor = self.select_cursor_begin
                self.update_advance()

                return
            if self.cursor == len(self.text):
                return

            self.cursor += 1
            self.update_advance()

        elif data.key == pygame.K_BACKSPACE:
            if self.select_started:
                self.delete_selected_subtext()
                self.select_started = False
                return
            if self.cursor == 0:
                return

            self.text.pop(self.cursor - 1)
            self.cursor -= 1
            self.update_advance()
            self.text_surface = self.make_text_surface()

    def toggle(self, data):
        if self.rect.collidepoint(data.pos):
            self.active = True
            self.background_color = [20, 20, 20]
        else:
            self.background_color = [30, 30, 30]
            self.active = False
            self.select_started = False
            self.cursor = self.select_cursor_begin
            self.update_advance()

    def __draw_text_box_debug(self, surface: pygame.Surface):
        pygame.draw.rect(
            surface,
            [255, 122, 0],
            self.text_rect,
            1,
            0,
        )

    def draw_box(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.background_color, self.rect, 0, self.roundness)

    def draw_cursor(self, surface: pygame.Surface):
        if self.select_started:
            pygame.draw.rect(
                surface,
                self.cursor_color,
                [
                    min(
                        self.text_rect.left + self.advance,
                        self.text_rect.left + self.select_advance_begin,
                    ),
                    self.text_rect.top,
                    abs(self.select_advance_begin - self.advance),
                    self.text_rect.height,
                ],
                0,
                8,
            )

        else:
            pygame.draw.rect(
                surface,
                self.cursor_color,
                [
                    self.text_rect.left + self.advance,
                    self.text_rect.top,
                    3,
                    self.text_rect.height,
                ],
                0,
                8,
            )

    def draw(self, surface: pygame.Surface):
        self.draw_box(surface)
        self.draw_cursor(surface)

        surface.blit(
            self.text_surface,
            self.text_surface.get_rect(
                centery=self.text_rect.centery, left=self.text_rect.left
            ),
        )


pygame.init()
pygame.key.set_repeat(500, 50)
display = pygame.display.set_mode([640, 360], pygame.RESIZABLE)
e = EventBroker()

textbox_rect = pygame.Rect(0, 0, 300, 50)
textbox_rect.center = [display.get_width() // 2, display.get_height() // 2]
textbox = TextBox(e, textbox_rect)
pygame.time.set_timer(cursor_blink, 500)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.VIDEORESIZE:
            textbox_rect.center = [display.get_width() // 2, display.get_height() // 2]
        e.emit(event.type, event)
    display.fill([0, 122, 255])
    textbox.draw(display)

    pygame.display.flip()
