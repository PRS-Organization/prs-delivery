import pygame
import sys


class WebDemo(object):
    def __init__(self, server=None):
        # Initialize Pygame
        pygame.init()

        self.server = server
        # Set window size
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("PRS Env Demo")

        # Set Color
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.text = 'This is a long text example that needs to be wrapped in multiple lines to fit the given area. Hopefully, this function will handle line wrapping properly.'
        self.running = False
        # Set Font
        self.font = pygame.font.SysFont(None, 24)
        self.button_state = 0
        # Add game start prompt text
        self.start_text = self.font.render("Game is beginning", True, self.BLACK)
        self.start_text_rect = self.start_text.get_rect()
        self.start_text_rect.center = (400, 50)

        # Define button coordinates and size
        self.button_width = 100
        self.button_height = 50
        self.button_margin = 20
        self.buttons = []
        for i in range(25):
            if i < 5:
                button = pygame.Rect(100 + i * (self.button_width + self.button_margin), 50, self.button_width, self.button_height)
            elif i < 10:
                button = pygame.Rect(100 + (i-5) * (self.button_width + self.button_margin), 110, self.button_width, self.button_height)
            elif i < 15:
                button = pygame.Rect(100 + (i-10) * (self.button_width + self.button_margin), 170, self.button_width, self.button_height)
            elif i < 20:
                button = pygame.Rect(100 + (i-15) * (self.button_width + self.button_margin), 230, self.button_width, self.button_height)
            elif i < 25:
                button = pygame.Rect(100 + (i-20) * (self.button_width + self.button_margin), 290, self.button_width, self.button_height)

            self.buttons.append(button)


    def button_clicked(self, index):
        result = f"Button {index + 1} clicked"
        # print(result)
        return result

    # Rendering text onto buttons

    def render_text_on_button(self, text, button):
        text_surface = self.font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect()
        text_rect.center = button.center
        self.screen.blit(text_surface, text_rect)

    # Rendered Text
    def render_text(self, screen, text):
        if len(text) > 100:
            text = text[-100:]
        text_surface = self.font.render(text, True, self.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = (400, 500)
        screen.blit(text_surface, text_rect)
        return text_rect

    def render_text_with_wrap(self, rect, max_lines):
        words = [word.split(' ') for word in self.text.splitlines()]  # 分割单词
        space = self.font.size(' ')[0]  # 单词间距
        max_width, max_height = rect.width, rect.height
        x, y = rect.topleft
        line_spacing = 2

        final_text = ''
        line_count = 0

        for line in words:
            for word in line:
                word_surface = self.font.render(word, True, self.BLACK)
                word_width, word_height = word_surface.get_size()

                if x + word_width < rect.right:
                    final_text += word + ' '
                    x += word_width + space
                else:
                    x = rect.left
                    y += word_height + line_spacing
                    if y > max_height or line_count >= max_lines:
                        return final_text
                    final_text += '\n'
                    line_count += 1

        return final_text

    def render_multiline_text(self, width=600):
        words = [word.split(' ') for word in self.text.splitlines()]
        space = self.font.size(' ')[0]  # 获取字体空格的宽度
        max_width, max_height = width, self.font.get_height()
        lines = []
        for line in words:
            for word in line:
                if self.font.size(' '.join(line))[0] >= max_width:
                    line.insert(-1, '\n')  # 换行
                    lines.extend(line[:-1])
                    line = line[-1:]
                    words.insert(words.index(line), line)
                    break
            else:
                lines.extend(line)
        lines_surface = pygame.Surface((max_width, max_height * len(lines)))
        lines_surface.fill((0, 0, 0, 0))
        text_pos = pygame.Rect(0, 0, max_width, max_height)
        for line in lines:
            for word in line:
                word_surface = self.font.render(word, True, self.BLACK)
                if text_pos.x + word_surface.get_width() >= max_width:
                    text_pos.x = 0
                    text_pos.y += max_height
                lines_surface.blit(word_surface, text_pos)
                text_pos.x += word_surface.get_width() + space
            text_pos.y += max_height
            text_pos.x = 0
        return lines_surface


    def run(self, env, time_manager):
        self.running = True
        text = "Press"
        while self.running:
            self.screen.fill(self.WHITE)

            # Display game start prompt text
            text_rect = self.render_text(self.screen, self.text)
            # text_rect = pygame.Rect(300, 300, 400, 200)  # 设置文本显示区域
            # final_text = self.render_text_with_wrap(text_rect, 8)
            # print(final_text)
            # text_surface = self.font.render(final_text, True, self.BLACK)
            self.screen.blit(self.start_text, self.start_text_rect, text_rect)
            # self.screen.blit(text_surface, text_rect)

            text = self.font.render(str(time_manager.current_date), True, self.BLACK)
            self.screen.blit(text, (10, 10))
            text = self.font.render('Day: '+str(time_manager.time_difference())+' Week: ' + str(time_manager.weekday_now()), True,self.BLACK)
            self.screen.blit(text, (10, 25))
            # print(self.buttons)
            for i, button in enumerate(self.buttons):
                pygame.draw.rect(self.screen, self.BLACK, button)
                self.render_text_on_button(f'Button {i + 1}', button)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        x, y = event.pos
                        for i, button in enumerate(self.buttons):
                            if button.collidepoint(x, y):
                                result = self.button_clicked(i)
                                self.button_state = i + 1
                                # render_text(screen, result)
                                env.chioce(i+1)
                                # text = result
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        print('game over')
                        self.running = False
                        self.server.state = 0
                        pygame.quit()
                    elif event.key == pygame.K_ESCAPE:
                        print('game over')
                        # print(self.button_state)
                        self.running = False
                        self.server.state = 0
                        pygame.quit()

            try:
                pygame.display.flip()
            except:
                pygame.quit()

# Close the Pygame window and terminate the program
# pygame.quit()
# sys.exit()
if __name__ == '__main__':
    game = WebDemo()
    game.run()