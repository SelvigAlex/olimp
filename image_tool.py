#!/usr/bin/env python3
"""
Программа для обработки изображений BMP и PNG
Специализированное программное средство для тактических карт
"""

import argparse
import sys
import os
import sqlite3
import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import struct

# Коды ошибок
ERR_GENERAL = 40
ERR_FILE_FORMAT = 41
ERR_CMD_ARGS = 42
ERR_COLOR = 43
ERR_COORDS = 44
ERR_MEMORY = 45
ERR_IO = 46
ERR_DRAW = 47
ERR_TRIM = 48
ERR_INV = 49


class ImageProcessor:
    def __init__(self):
        self.db_conn = None
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        try:
            self.db_conn = sqlite3.connect('image_processing.db', check_same_thread=False)
            cursor = self.db_conn.cursor()

            # Таблица обработанных файлов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    file_size_kb REAL NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица операций обработки
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    output_filename TEXT NOT NULL,
                    operation_command TEXT NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES processed_files (id)
                )
            ''')

            self.db_conn.commit()
        except Exception as e:
            print(f"Database initialization error: {e}", file=sys.stderr)

    def log_file_processing(self, filename, file_type, width, height, file_size_kb):
        """Логирование обработки файла"""
        if not self.db_conn:
            return None

        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO processed_files 
                (filename, file_type, width, height, file_size_kb, processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filename, file_type, width, height, file_size_kb, datetime.datetime.now()))

            file_id = cursor.lastrowid
            self.db_conn.commit()
            return file_id
        except Exception as e:
            print(f"Error logging file: {e}", file=sys.stderr)
            return None

    def log_operation(self, file_id, output_filename, operation_command):
        """Логирование операции"""
        if not self.db_conn or file_id is None:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO processing_operations 
                (file_id, output_filename, operation_command, processed_at)
                VALUES (?, ?, ?, ?)
            ''', (file_id, output_filename, operation_command, datetime.datetime.now()))

            self.db_conn.commit()
        except Exception as e:
            print(f"Error logging operation: {e}", file=sys.stderr)

    def parse_coordinates(self, coord_str):
        """Парсинг координат формата X.Y"""
        try:
            x, y = map(int, coord_str.split('.'))
            return x, y
        except:
            raise ValueError(f"Invalid coordinates format: {coord_str}")

    def parse_color(self, color_str):
        """Парсинг цвета формата R.G.B"""
        try:
            r, g, b = map(int, color_str.split('.'))
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                raise ValueError("Color values must be between 0 and 255")
            return (r, g, b)
        except:
            raise ValueError(f"Invalid color format: {color_str}")

    def validate_coordinates(self, x, y, width, height):
        """Проверка координат на валидность"""
        if x < 0 or y < 0 or x >= width or y >= height:
            raise ValueError(f"Coordinates ({x}, {y}) out of image bounds ({width}x{height})")

    def validate_rectangle(self, left_up, right_down, width, height):
        """Проверка прямоугольника на валидность"""
        x1, y1 = left_up
        x2, y2 = right_down

        if x1 >= x2 or y1 >= y2:
            raise ValueError("Invalid rectangle: left_up must be above and to the left of right_down")

        # Корректировка координат до границ изображения
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))

        return (x1, y1), (x2, y2)

    def load_image(self, filename):
        """Загрузка изображения с проверкой формата"""
        try:
            image = Image.open(filename)

            # Проверка формата
            if image.format not in ['BMP', 'PNG']:
                raise ValueError(f"Unsupported format: {image.format}")

            # Конвертация в RGB если необходимо
            if image.mode != 'RGB':
                image = image.convert('RGB')

            return image
        except Exception as e:
            raise ValueError(f"Error loading image: {e}")

    def save_image(self, image, filename, original_format):
        """Сохранение изображения с сохранением формата"""
        try:
            if original_format == 'BMP':
                image.save(filename, 'BMP')
            else:  # PNG
                image.save(filename, 'PNG', optimize=True)
        except Exception as e:
            raise ValueError(f"Error saving image: {e}")

    def get_file_info(self, filename):
        """Получение информации о файле"""
        try:
            image = self.load_image(filename)
            file_size = os.path.getsize(filename)

            return {
                'width': image.width,
                'height': image.height,
                'file_size': file_size,
                'format': image.format
            }
        except Exception as e:
            raise ValueError(f"Error getting file info: {e}")

    def draw_rectangle(self, image, left_up, right_down, thickness, color, fill=False, fill_color=None):
        """Рисование прямоугольника"""
        draw = ImageDraw.Draw(image)
        left_up, right_down = self.validate_rectangle(left_up, right_down, image.width, image.height)

        if fill:
            if fill_color is None:
                fill_color = color
            draw.rectangle([left_up, right_down], outline=color, fill=fill_color, width=thickness)
        else:
            draw.rectangle([left_up, right_down], outline=color, width=thickness)

        return image

    def draw_circle(self, image, center, radius, thickness, color, fill=False, fill_color=None):
        """Рисование окружности"""
        if radius <= 0:
            raise ValueError("Radius must be positive")

        draw = ImageDraw.Draw(image)
        x, y = center

        # Проверка центра
        self.validate_coordinates(x, y, image.width, image.height)

        # Корректировка радиуса если необходимо
        max_radius = min(x, y, image.width - x - 1, image.height - y - 1)
        radius = min(radius, max_radius)

        bbox = [(x - radius, y - radius), (x + radius, y + radius)]

        if fill:
            if fill_color is None:
                fill_color = color
            draw.ellipse(bbox, outline=color, fill=fill_color, width=thickness)
        else:
            draw.ellipse(bbox, outline=color, width=thickness)

        return image

    def rotate_region(self, image, left_up, right_down, angle):
        """Поворот области"""
        if angle not in [90, 180, 270]:
            raise ValueError("Angle must be 90, 180 or 270")

        left_up, right_down = self.validate_rectangle(left_up, right_down, image.width, image.height)

        # Выделение области
        region = image.crop((left_up[0], left_up[1], right_down[0] + 1, right_down[1] + 1))

        # Поворот
        rotated_region = region.rotate(angle, expand=False)

        # Вставка обратно
        image.paste(rotated_region, (left_up[0], left_up[1]))

        return image

    def replace_color(self, image, old_color, new_color):
        """Замена цвета"""
        pixels = image.load()

        for y in range(image.height):
            for x in range(image.width):
                if pixels[x, y] == old_color:
                    pixels[x, y] = new_color

        return image

    def mirror_region(self, image, axis, left_up, right_down):
        """Отражение области"""
        if axis not in ['x', 'y']:
            raise ValueError("Axis must be 'x' or 'y'")

        left_up, right_down = self.validate_rectangle(left_up, right_down, image.width, image.height)

        # Выделение области
        region = image.crop((left_up[0], left_up[1], right_down[0] + 1, right_down[1] + 1))

        # Отражение
        if axis == 'x':
            mirrored_region = ImageOps.mirror(region)
        else:  # 'y'
            mirrored_region = ImageOps.flip(region)

        # Вставка обратно
        image.paste(mirrored_region, (left_up[0], left_up[1]))

        return image

    def trim_image(self, image, left_up, right_down):
        """Обрезка изображения"""
        left_up, right_down = self.validate_rectangle(left_up, right_down, image.width, image.height)

        # Обрезка
        trimmed = image.crop((left_up[0], left_up[1], right_down[0] + 1, right_down[1] + 1))

        return trimmed

    def copy_region(self, image, left_up, right_down, dest_left_up):
        """Копирование области"""
        left_up, right_down = self.validate_rectangle(left_up, right_down, image.width, image.height)
        dest_x, dest_y = dest_left_up

        # Проверка целевых координат
        if dest_x < 0 or dest_y < 0 or dest_x >= image.width or dest_y >= image.height:
            raise ValueError("Destination coordinates out of bounds")

        # Выделение области
        region = image.crop((left_up[0], left_up[1], right_down[0] + 1, right_down[1] + 1))

        # Вставка в новое место
        image.paste(region, (dest_x, dest_y))

        return image

    def apply_rgb_filter(self, image, component_name, component_value):
        """Применение RGB-фильтра"""
        if component_name not in ['red', 'green', 'blue']:
            raise ValueError("Component name must be 'red', 'green' or 'blue'")

        if not (0 <= component_value <= 255):
            raise ValueError("Component value must be between 0 and 255")

        pixels = image.load()
        component_index = {'red': 0, 'green': 1, 'blue': 2}[component_name]

        for y in range(image.height):
            for x in range(image.width):
                pixel = list(pixels[x, y])
                pixel[component_index] = component_value
                pixels[x, y] = tuple(pixel)

        return image

    def create_collage(self, image, number_x, number_y):
        """Создание коллажа"""
        if number_x <= 0 or number_y <= 0:
            raise ValueError("Number of tiles must be positive")

        # Создание холста для коллажа
        collage_width = image.width * number_x
        collage_height = image.height * number_y
        collage = Image.new('RGB', (collage_width, collage_height))

        # Заполнение коллажа копиями изображения
        for y in range(number_y):
            for x in range(number_x):
                collage.paste(image, (x * image.width, y * image.height))

        return collage


def main():
    parser = argparse.ArgumentParser(description='Image processing tool for BMP and PNG files')
    parser.add_argument('-i', '--input', help='Input image file')
    parser.add_argument('-o', '--output', help='Output image file')

    # Операции
    parser.add_argument('--info', action='store_true', help='Show image information')
    parser.add_argument('--rect', action='store_true', help='Draw rectangle')
    parser.add_argument('--circle', action='store_true', help='Draw circle')
    parser.add_argument('--rotate', action='store_true', help='Rotate region')
    parser.add_argument('--color_replace', action='store_true', help='Replace color')
    parser.add_argument('--mirror', action='store_true', help='Mirror region')
    parser.add_argument('--trim', action='store_true', help='Trim image')
    parser.add_argument('--copy', action='store_true', help='Copy region')
    parser.add_argument('--rgbfilter', action='store_true', help='Apply RGB filter')
    parser.add_argument('--collage', action='store_true', help='Create collage')

    # Параметры
    parser.add_argument('--left_up', help='Left upper coordinates (X.Y)')
    parser.add_argument('--right_down', help='Right down coordinates (X.Y)')
    parser.add_argument('--center', help='Center coordinates (X.Y)')
    parser.add_argument('--dest_left_up', help='Destination left upper coordinates (X.Y)')
    parser.add_argument('--thickness', type=int, help='Line thickness')
    parser.add_argument('--color', help='Color (R.G.B)')
    parser.add_argument('--fill', action='store_true', help='Fill shape')
    parser.add_argument('--fill_color', help='Fill color (R.G.B)')
    parser.add_argument('--radius', type=int, help='Circle radius')
    parser.add_argument('--angle', type=int, help='Rotation angle (90, 180, 270)')
    parser.add_argument('--old_color', help='Old color (R.G.B)')
    parser.add_argument('--new_color', help='New color (R.G.B)')
    parser.add_argument('--axis', help='Mirror axis (x or y)')
    parser.add_argument('--component_name', help='RGB component name (red, green, blue)')
    parser.add_argument('--component_value', type=int, help='RGB component value (0-255)')
    parser.add_argument('--number_x', type=int, help='Number of horizontal tiles for collage')
    parser.add_argument('--number_y', type=int, help='Number of vertical tiles for collage')

    # Последний аргумент - входной файл
    parser.add_argument('input_file', nargs='?', help='Input image file')

    args = parser.parse_args()

    # Определение входного файла
    input_file = args.input or args.input_file
    if not input_file:
        print("Error: Input file not specified", file=sys.stderr)
        sys.exit(ERR_CMD_ARGS)

    # Проверка существования файла
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found", file=sys.stderr)
        sys.exit(ERR_IO)

    # Определение выходного файла
    output_file = args.output
    if not output_file:
        # Определение расширения по входному файлу
        ext = os.path.splitext(input_file)[1].lower()
        if ext in ['.bmp', '.png']:
            output_file = f'out{ext}'
        else:
            output_file = 'out.bmp'

    # Проверка совпадения входного и выходного файлов
    if input_file == output_file:
        print("Error: Input and output files cannot be the same", file=sys.stderr)
        sys.exit(ERR_CMD_ARGS)

    processor = ImageProcessor()

    try:
        # Операция --info
        if args.info:
            info = processor.get_file_info(input_file)
            print("File information:")
            print(f"File size: {info['file_size']}")
            print(f"Width: {info['width']}")
            print(f"Height: {info['height']}")
            print(f"Format: {info['format']}")
            sys.exit(0)

        # Загрузка изображения
        image = processor.load_image(input_file)
        original_format = image.format

        # Логирование файла
        file_size_kb = os.path.getsize(input_file) / 1024
        file_id = processor.log_file_processing(
            input_file, original_format, image.width, image.height, file_size_kb
        )

        # Определение команды для логирования
        operation_command = ' '.join(sys.argv[1:])

        # Выполнение операций
        if args.rect:
            if not all([args.left_up, args.right_down, args.thickness, args.color]):
                print("Error: Missing required flags for rectangle", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            left_up = processor.parse_coordinates(args.left_up)
            right_down = processor.parse_coordinates(args.right_down)
            color = processor.parse_color(args.color)
            fill_color = processor.parse_color(args.fill_color) if args.fill_color else None

            image = processor.draw_rectangle(
                image, left_up, right_down, args.thickness, color,
                args.fill, fill_color
            )

        elif args.circle:
            if not all([args.center, args.radius, args.thickness, args.color]):
                print("Error: Missing required flags for circle", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            center = processor.parse_coordinates(args.center)
            color = processor.parse_color(args.color)
            fill_color = processor.parse_color(args.fill_color) if args.fill_color else None

            image = processor.draw_circle(
                image, center, args.radius, args.thickness, color,
                args.fill, fill_color
            )

        elif args.rotate:
            if not all([args.left_up, args.right_down, args.angle]):
                print("Error: Missing required flags for rotation", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            left_up = processor.parse_coordinates(args.left_up)
            right_down = processor.parse_coordinates(args.right_down)

            image = processor.rotate_region(image, left_up, right_down, args.angle)

        elif args.color_replace:
            if not all([args.old_color, args.new_color]):
                print("Error: Missing required flags for color replacement", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            old_color = processor.parse_color(args.old_color)
            new_color = processor.parse_color(args.new_color)

            image = processor.replace_color(image, old_color, new_color)

        elif args.mirror:
            if not all([args.axis, args.left_up, args.right_down]):
                print("Error: Missing required flags for mirror", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            left_up = processor.parse_coordinates(args.left_up)
            right_down = processor.parse_coordinates(args.right_down)

            image = processor.mirror_region(image, args.axis, left_up, right_down)

        elif args.trim:
            if not all([args.left_up, args.right_down]):
                print("Error: Missing required flags for trim", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            left_up = processor.parse_coordinates(args.left_up)
            right_down = processor.parse_coordinates(args.right_down)

            image = processor.trim_image(image, left_up, right_down)

        elif args.copy:
            if not all([args.left_up, args.right_down, args.dest_left_up]):
                print("Error: Missing required flags for copy", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            left_up = processor.parse_coordinates(args.left_up)
            right_down = processor.parse_coordinates(args.right_down)
            dest_left_up = processor.parse_coordinates(args.dest_left_up)

            image = processor.copy_region(image, left_up, right_down, dest_left_up)

        elif args.rgbfilter:
            if not all([args.component_name, args.component_value]):
                print("Error: Missing required flags for RGB filter", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            image = processor.apply_rgb_filter(image, args.component_name, args.component_value)

        elif args.collage:
            if not all([args.number_x, args.number_y]):
                print("Error: Missing required flags for collage", file=sys.stderr)
                sys.exit(ERR_CMD_ARGS)

            image = processor.create_collage(image, args.number_x, args.number_y)

        else:
            # Если не указана операция, просто копируем файл
            pass

        # Сохранение изображения
        processor.save_image(image, output_file, original_format)

        # Логирование операции
        processor.log_operation(file_id, output_file, operation_command)

        print(f"Operation completed successfully. Output: {output_file}")

    except ValueError as e:
        error_msg = str(e)
        if "color" in error_msg.lower():
            print(f"Error: Incorrect color", file=sys.stderr)
            sys.exit(ERR_COLOR)
        elif "coordinate" in error_msg.lower() or "bounds" in error_msg.lower():
            print(f"Error: Incorrect coordinates", file=sys.stderr)
            sys.exit(ERR_COORDS)
        elif "angle" in error_msg.lower():
            print(f"Error: Invalid angle", file=sys.stderr)
            sys.exit(ERR_CMD_ARGS)
        elif "component" in error_msg.lower():
            print(f"Error: --component_name [red|green|blue] required", file=sys.stderr)
            sys.exit(ERR_CMD_ARGS)
        else:
            print(f"Error: {error_msg}", file=sys.stderr)
            sys.exit(ERR_CMD_ARGS)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(ERR_GENERAL)


if __name__ == '__main__':
    main()