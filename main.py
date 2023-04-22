from itertools import islice
from PIL import Image
import requests

from math import sqrt
from io import BytesIO
import math
import concurrent.futures

new_colors = []
past_color = 1


def mix_colors(*color_codes, ratios=None):
    """
    Функция для смешивания нескольких цветов в заданных пропорциях.

    Аргументы:
    *color_codes - кортеж или список 24-битных цветовых кодов
    ratios - список пропорций для каждого цвета. Если None, то используются равные пропорции для каждого цвета.

    Возвращает:
    Кортеж RGB значений итогового смешанного цвета.

    """
    num_colors = len(color_codes)
    if num_colors == 0:
        return None
    if ratios is None:
        ratios = [1] * num_colors
    total_ratio = sum(ratios)
    if total_ratio == 0:
        return None

    # Получаем отдельные значения красного, зеленого и синего для каждого цвета
    colors = [(color >> 16 & 0xff, color >> 8 & 0xff, color & 0xff) for color in color_codes]
    reds, greens, blues = zip(*colors)

    # Смешиваем цвета в заданных пропорциях
    mixed_red = sum(r * ratio for r, ratio in zip(reds, ratios)) // total_ratio
    mixed_green = sum(g * ratio for g, ratio in zip(greens, ratios)) // total_ratio
    mixed_blue = sum(b * ratio for b, ratio in zip(blues, ratios)) // total_ratio

    # Возвращаем итоговый цвет в виде кортежа RGB значений
    return mixed_red, mixed_green, mixed_blue


def get_colors() -> dict[str, int]:
    r = requests.post("http://api.datsart.dats.team/art/colors/list", headers={"Authorization": "Bearer 6437d6464d6da6437d6464d6dc"})
    return r.json()['response']


def color_distance(color1, color2):
    """Функция для расчета расстояния между двумя цветами"""
    r1, g1, b1 = (color1 >> 16) & 0xFF, (color1 >> 8) & 0xFF, color1 & 0xFF
    r2, g2, b2 = (color2 >> 16) & 0xFF, (color2 >> 8) & 0xFF, color2 & 0xFF
    return sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def find_color(colors, color_amount, desired_color):
    """Функция для поиска оптимальных коэффициентов цветов"""
    result = {}
    color_coefficients = {}

    # Находим максимальный коэффициент для каждого цвета
    for i in range(len(colors)):
        color_coefficients[colors[i]] = color_distance(colors[i], desired_color)

    # Сортируем цвета по возрастанию расстояния до искомого цвета
    sorted_colors = sorted(colors, key=lambda color: color_coefficients[color])

    # Находим оптимальный коэффициент для каждого цвета
    for i in range(len(sorted_colors)):
        color = sorted_colors[i]
        if color_amount[colors.index(color)] < 30:
            continue
        result[color] = color_amount[colors.index(color)]
    return result


def circle_image(url, circle_size, amount):
    # Загружаем изображение по ссылке
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert('RGB')

    # Получаем размер изображения
    width, height = img.size

    # Создаем список для хранения окружностей
    circles = []

    # Разбиваем изображение на круги
    for y in range(0, height, circle_size):
        for x in range(0, width, circle_size):
            # Вычисляем координаты центра круга
            center_x = x + circle_size // 2
            center_y = y + circle_size // 2

            # Если круг не выходит за границы изображения, то добавляем его в список
            if center_x < width and center_y < height:
                # Получаем цвет круга
                circle = img.crop((x, y, x + circle_size, y + circle_size))
                mean_color = tuple(map(int, circle.resize((1, 1)).getpixel((0, 0))))

                # Если цвет не белый, то добавляем круг в список
                if sum(mean_color[:3]) <= 700 and sum(mean_color[:3]) != 531:
                    mean_color = mean_color[0] << 16 | mean_color[1] << 8 | mean_color[2]
                    circles.append((center_x, center_y, amount, mean_color))

    return circles


def shoot_pixels(x, y):
    m = mass # масса
    k = 0.001
    g = 9.80665
    p = power # сила, для массы 10 лучше ставить 30, для массы 20 ставить 60, для массы 30 ставить 100, т.к. если синус получится отрицательным, все сломается
    # print("power = {}".format(p))

    catapultaX = 250
    catapultaY = 0

    y = 300 + y #координата точки
    A = y
    B = x - catapultaX
    C = sqrt(A ** 2 + B ** 2)

    sinusVert = (C * m * k * g) / (2 * p)
    angularVertical = math.asin(sinusVert) * (180.0 / math.pi)
    angularVertical = angularVertical / 2
    # print("angularVertical = {:.6f}".format(angularVertical)) # поменять запятую на точку в выводе

    angularHorizontal = math.atan(B / A) * (180.0 / math.pi)
    # print("angularHorizontal = {:.6f}".format(angularHorizontal)) # поменять запятую на точку в выводе
    return angularHorizontal, angularVertical


def main_shooter(shoot, past_color):
    global new_colors

    # if past_color != shoot[3]:
    #     colors = color_list.keys()
    #     amounts = list(color_list.values())
    #     colors = list(map(int, colors))
    #     new_colors = find_color(colors, amounts, shoot[3])
    #     new_colors = list(islice(new_colors.items(), 11))

    angleHorizontal, angleVertical = shoot_pixels(shoot[0], shoot[1])
    # print(angleHorizontal)
    print(shoot)

    data = {"angleHorizontal": (None, str(angleHorizontal)),
            "angleVertical": (None, str(angleVertical)),
            "power": (None, str(power))}
    for key, value in new_colors:
        data[f"colors[{key}]"] = (None, str(20))

    print(data)
    r = requests.post("http://api.datsart.dats.team/art/ballista/shoot", files=data,
                      headers={"Authorization": "Bearer 6437d6464d6da6437d6464d6dc"}, )
    print(r.json())


if __name__ == '__main__':
    power = 1000
    mass = 220
    image_url = "http://s.datsart.dats.team/game/image/shared/30.png"
    circle_radius = 10
    pixel_amount = 32
    num_threads = 5
    color_number = 267067

    circles_bitmap = circle_image(image_url, circle_radius, pixel_amount)
    color_list = get_colors()
    colors = color_list.keys()
    amounts = list(color_list.values())
    colors = list(map(int, colors))
    new_colors = find_color(colors, amounts, color_number)
    new_colors = list(islice(new_colors.items(), 11))
    new_bitmap = []
    # for shots in circles_bitmap:
    #     if shots[3] == color_number:
    #         new_bitmap.append(shots)
    #         print(shots)

    for shots in circles_bitmap:
        try:
            main_shooter(shots, past_color)
            past_color = shots[3]
        except:
            pass

    # with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    #     results = [executor.submit(target=main_shooter, args=shoot) for shoot in circles_bitmap]
    #
    #     for result in concurrent.futures.as_completed(results):
    #         print("я сделал")
    #         pass

