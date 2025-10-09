import os
import subprocess
import sys
from typing import List, Dict, Any
import json

class ImageProcessorTester:
    def __init__(self):
        self.script_path = "./image_tool.py"
        self.input_dir = "input_photos"
        self.output_dir = "output_photos"
        self.results = []
        
        # Определяем размеры тестового изображения
        self.width = 852
        self.height = 480
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.bmp_images = []
        self.png_images = []
        
        if os.path.exists(self.input_dir):
            # Ищем все BMP и PNG файлы
            for file in os.listdir(self.input_dir):
                if file.endswith('.bmp'):
                    self.bmp_images.append(os.path.join(self.input_dir, file))
                elif file.endswith('.png'):
                    self.png_images.append(os.path.join(self.input_dir, file))
        else:
            print(f"ОШИБКА: Входная директория '{self.input_dir}' не найдена!")
        
        print(f"Найдено {len(self.bmp_images)} BMP изображений")
        print(f"Найдено {len(self.png_images)} PNG изображений")
        
    def run_command(self, args: List[str]) -> Dict[str, Any]:
        """Выполняет команду и возвращает результат"""
        try:
            cmd = [sys.executable, self.script_path] + args
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Таймаут выполнения',
                'command': ' '.join(cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(cmd)
            }
    
    def get_output_path(self, input_path: str, operation: str) -> str:
        """Генерирует путь для выходного файла результата теста"""
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        ext = os.path.splitext(input_path)[1]
        return os.path.join(self.output_dir, f"{base_name}_{operation}{ext}")
    
    def get_test_image(self):
        """Возвращает первое доступное тестовое изображение"""
        if self.bmp_images:
            return self.bmp_images[0]
        elif self.png_images:
            return self.png_images[0]
        else:
            return None
    
    def test_no_arguments(self):
        """Тест запуска без аргументов"""
        print("Тестирование запуска без аргументов...")
        result = self.run_command([])
        self.results.append({
            'test': 'Запуск без аргументов',
            'command': '',
            'success': result['returncode'] == 0,
            'expected': 'Показать справку',
            'actual': result['stdout'][:100] + '...' if result['stdout'] else result['stderr']
        })
    
    def test_help_commands(self):
        """Тестирование различных вариантов справки"""
        print("Тестирование команд справки...")
        
        help_variants = [
            ("--help", "Основная справка"),
            ("-h", "Короткая справка"),
            ("--help=rect", "Справка по прямоугольнику"),
            ("--help=circle", "Справка по окружности"),
            ("--help=rotate", "Справка по повороту"),
            ("--help=mirror", "Справка по отражению"),
            ("--help=color_replace", "Справка по замене цвета"),
            ("-h rect", "Справка по прямоугольнику (короткий формат)"),
            ("-h circle", "Справка по окружности (короткий формат)")
        ]
        
        for cmd, description in help_variants:
            result = self.run_command(cmd.split())
            self.results.append({
                'test': f'Справка: {description}',
                'command': cmd,
                'success': result['success'],
                'expected': 'Показать справку',
                'actual': 'Справка показана' if result['success'] else result['stderr']
            })
    
    def test_info_command(self):
        """Тестирование команды --info"""
        print("Тестирование команды info...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        result = self.run_command(["--info", test_image])
        # Для команды --info успехом считается любой вывод информации о файле
        success = result['success'] and any(keyword in result['stdout'].lower() for keyword in ['size', 'width', 'height', 'размер', 'ширина', 'высота'])
        self.results.append({
            'test': 'Информация о файле',
            'command': f'--info {os.path.basename(test_image)}',
            'success': success,
            'expected': 'Информация о файле',
            'actual': result['stdout'][:100] if result['stdout'] else result['stderr']
        })
    
    def test_rect_cases(self):
        """Тестирование различных случаев рисования прямоугольников"""
        print("Тестирование прямоугольников...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        rect_cases = [
            # Внутри изображения
            ("10.10", "100.100", "Внутри изображения"),
            # На границах
            ("0.0", "100.100", "Верхний левый угол"),
            (f"{self.width-100}.0", f"{self.width}.100", "Верхний правый угол"),
            (f"0.{self.height-100}", f"100.{self.height}", "Нижний левый угол"),
            (f"{self.width-100}.{self.height-100}", f"{self.width}.{self.height}", "Нижний правый угол"),
            # На границе
            ("0.10", "100.110", "Левая граница"),
            (f"{self.width-100}.10", f"{self.width}.110", "Правая граница"),
            ("10.0", "110.100", "Верхняя граница"),
            (f"10.{self.height-100}", f"110.{self.height}", "Нижняя граница"),
        ]
        
        for i, (lu, rd, description) in enumerate(rect_cases):
            output_path = self.get_output_path(test_image, f"rect_case_{i}")
            result = self.run_command([
                "--rect", 
                "--left_up", lu, 
                "--right_down", rd, 
                "--thickness", "2", 
                "--color", "255.0.0",
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Прямоугольник: {description}',
                'command': f'rect {lu} {rd}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_filled_rect_cases(self):
        """Тестирование залитых прямоугольников"""
        print("Тестирование залитых прямоугольников...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        filled_cases = [
            ("50.50", "200.200", "Залитый прямоугольник"),
            ("0.0", "150.150", "Залитый в углу"),
        ]
        
        for i, (lu, rd, description) in enumerate(filled_cases):
            output_path = self.get_output_path(test_image, f"filled_rect_{i}")
            result = self.run_command([
                "--rect",
                "--left_up", lu,
                "--right_down", rd, 
                "--thickness", "2",
                "--color", "0.255.0",
                "--fill",
                "--fill_color", "0.0.255",
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Залитый прямоугольник: {description}',
                'command': f'filled rect {lu} {rd}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_circle_cases(self):
        """Тестирование различных случаев рисования окружностей"""
        print("Тестирование окружностей...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        circle_cases = [
            # Внутри изображения
            ("400.300", "100", "В центре"),
            # На границах
            ("100.100", "100", "Близко к углу"),
            (f"{self.width-100}.100", "100", "У правой границы"),
            (f"100.{self.height-100}", "100", "У нижней границы"),
            (f"{self.width-100}.{self.height-100}", "100", "В правом нижнем углу"),
        ]
        
        for i, (center, radius, description) in enumerate(circle_cases):
            output_path = self.get_output_path(test_image, f"circle_case_{i}")
            result = self.run_command([
                "--circle",
                "--center", center, 
                "--radius", radius,
                "--thickness", "3",
                "--color", "255.255.0",
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Окружность: {description}',
                'command': f'circle {center} r{radius}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_filled_circle_cases(self):
        """Тестирование залитых окружностей"""
        print("Тестирование залитых окружностей...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        filled_circle_cases = [
            ("200.200", "80", "Залитая окружность"),
            ("600.400", "50", "Залитая маленькая"),
        ]
        
        for i, (center, radius, description) in enumerate(filled_circle_cases):
            output_path = self.get_output_path(test_image, f"filled_circle_{i}")
            result = self.run_command([
                "--circle",
                "--center", center,
                "--radius", radius,
                "--thickness", "1", 
                "--color", "0.255.255",
                "--fill",
                "--fill_color", "255.0.255",
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Залитая окружность: {description}',
                'command': f'filled circle {center} r{radius}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_rotate_cases(self):
        """Тестирование поворотов"""
        print("Тестирование поворотов...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        rotate_cases = [
            ("100.100", "300.300", "90", "Поворот 90°"),
            ("50.50", "200.200", "180", "Поворот 180°"),
            ("150.150", "400.400", "270", "Поворот 270°"),
            ("0.0", "100.100", "90", "Поворот в углу"),
            (f"{self.width-200}.{self.height-200}", f"{self.width}.{self.height}", "180", "Поворот в правом нижнем углу")
        ]
        
        for i, (lu, rd, angle, description) in enumerate(rotate_cases):
            output_path = self.get_output_path(test_image, f"rotate_{angle}_{i}")
            result = self.run_command([
                "--rotate",
                "--left_up", lu,
                "--right_down", rd, 
                "--angle", angle,
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Поворот: {description}',
                'command': f'rotate {lu}-{rd} {angle}°',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_mirror_cases(self):
        """Тестирование отражений"""
        print("Тестирование отражений...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        mirror_cases = [
            ("x", "100.100", "300.300", "Отражение по X"),
            ("y", "100.100", "300.300", "Отражение по Y"),
            ("x", "0.0", "200.200", "Отражение в углу по X"),
            ("y", f"{self.width-200}.{self.height-200}", f"{self.width}.{self.height}", "Отражение в углу по Y")
        ]
        
        for i, (axis, lu, rd, description) in enumerate(mirror_cases):
            output_path = self.get_output_path(test_image, f"mirror_{axis}_{i}")
            result = self.run_command([
                "--mirror", 
                "--axis", axis,
                "--left_up", lu,
                "--right_down", rd,
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Отражение: {description}',
                'command': f'mirror {axis} {lu}-{rd}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_copy_cases(self):
        """Тестирование копирования"""
        print("Тестирование копирования...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        copy_cases = [
            ("50.50", "150.150", "200.200", "Копирование области"),
            ("0.0", "100.100", "300.300", "Копирование из угла"),
            (f"{self.width-150}.{self.height-150}", f"{self.width}.{self.height}", "50.50", "Копирование из правого нижнего угла")
        ]
        
        for i, (src_lu, src_rd, dest_lu, description) in enumerate(copy_cases):
            output_path = self.get_output_path(test_image, f"copy_{i}")
            result = self.run_command([
                "--copy",
                "--left_up", src_lu,
                "--right_down", src_rd, 
                "--dest_left_up", dest_lu,
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Копирование: {description}',
                'command': f'copy {src_lu}-{src_rd} -> {dest_lu}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_trim_cases(self):
        """Тестирование обрезки"""
        print("Тестирование обрезки...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        trim_cases = [
            ("100.100", "400.400", "Обрезка центра"),
            ("0.0", "200.200", "Обрезка левого верхнего угла"),
            (f"{self.width-200}.{self.height-200}", f"{self.width}.{self.height}", "Обрезка правого нижнего угла"),
            ("50.50", "300.500", "Обрезка прямоугольной области")
        ]
        
        for i, (lu, rd, description) in enumerate(trim_cases):
            output_path = self.get_output_path(test_image, f"trim_{i}")
            result = self.run_command([
                "--trim",
                "--left_up", lu, 
                "--right_down", rd,
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Обрезка: {description}',
                'command': f'trim {lu}-{rd}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_rgbfilter_cases(self):
        """Тестирование RGB фильтров"""
        print("Тестирование RGB фильтров...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        filter_cases = [
            ("red", "128", "Красный фильтр"),
            ("green", "200", "Зеленый фильтр"),
            ("blue", "100", "Синий фильтр"),
            ("red", "0", "Красный фильтр (мин)"),
            ("green", "255", "Зеленый фильтр (макс)"),
            ("blue", "50", "Синий фильтр (половинный)")
        ]
        
        for component, value, description in filter_cases:
            output_path = self.get_output_path(test_image, f"filter_{component}_{value}")
            result = self.run_command([
                "--rgbfilter",
                "--component_name", component,
                "--component_value", value,
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'RGB фильтр: {description}',
                'command': f'filter {component} {value}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_collage_cases(self):
        """Тестирование коллажей"""
        print("Тестирование коллажей...")
        test_image = self.get_test_image()
        if not test_image:
            return
            
        collage_cases = [
            ("2", "2", "Коллаж 2x2"),
            ("3", "2", "Коллаж 3x2"),
            ("1", "4", "Коллаж 1x4"),
            ("4", "1", "Коллаж 4x1")
        ]
        
        for nx, ny, description in collage_cases:
            output_path = self.get_output_path(test_image, f"collage_{nx}x{ny}")
            result = self.run_command([
                "--collage",
                "--number_x", nx,
                "--number_y", ny, 
                "-o", output_path,
                test_image
            ])
            self.results.append({
                'test': f'Коллаж: {description}',
                'command': f'collage {nx}x{ny}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Выходной файл создан',
                'actual': f'Файл создан' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_error_cases(self):
        """Тестирование обработки ошибок"""
        print("Тестирование обработки ошибок...")
        test_image = self.get_test_image()
        if not test_image:
            return
        
        error_cases = [
            # Неизвестная опция
            (["--unknown_option", test_image], "Неизвестная опция", ERR_CMD_ARGS),
            # Неверный цвет
            (["--rect", "--left_up", "100.100", "--right_down", "200.200", "--thickness", "2", "--color", "300.0.0", test_image], 
             "Неверный цвет", ERR_COLOR),
            # Отсутствующие параметры
            (["--rect", test_image], "Отсутствующие параметры", ERR_CMD_ARGS),
            # Множественные операции
            (["--rect", "--circle", test_image], "Множественные операции", ERR_CMD_ARGS),
            # Несуществующий файл
            (["--info", "nonexistent.bmp"], "Несуществующий файл", ERR_FILE_FORMAT),
            # Неверный угол поворота
            (["--rotate", "--left_up", "100.100", "--right_down", "200.200", "--angle", "45", test_image], 
             "Неверный угол", ERR_DRAW),
            # Неверная ось отражения
            (["--mirror", "--axis", "z", "--left_up", "100.100", "--right_down", "200.200", test_image], 
             "Неверная ось", ERR_CMD_ARGS),
            # Неверный компонент RGB
            (["--rgbfilter", "--component_name", "alpha", "--component_value", "100", test_image], 
             "Неверный компонент", ERR_CMD_ARGS),
            # Неверное значение компонента
            (["--rgbfilter", "--component_name", "red", "--component_value", "300", test_image], 
             "Неверное значение компонента", ERR_CMD_ARGS),
            (["--rect", "--left_up", "-50.-50", "--right_down", "50.50", "--thickness", "2", "--color", "255.0.0", test_image], 
             "Координаты за пределами", ERR_CMD_ARGS),
        ]
        
        for cmd_args, description, expected_code in error_cases:
            result = self.run_command(cmd_args)
            # Для тестов ошибок успехом считается получение ожидаемого кода ошибки
            success = result['returncode'] == expected_code
            self.results.append({
                'test': f'Ошибка: {description}',
                'command': ' '.join(cmd_args),
                'success': success,
                'expected': f'Код ошибки {expected_code}' if expected_code != 0 else 'Успешное выполнение',
                'actual': f"Код {result['returncode']}"
            })
    
    def run_non_image_tests(self):
        """Запускает тесты, которые не создают изображения"""
        print("=== ТЕСТЫ БЕЗ ВЫХОДНЫХ ИЗОБРАЖЕНИЙ ===")
        self.test_no_arguments()
        self.test_help_commands()
        self.test_info_command()
        self.test_error_cases()
    
    def run_image_tests(self):
        """Запускает тесты, которые создают изображения"""
        print("\n=== ТЕСТЫ С ВЫХОДНЫМИ ИЗОБРАЖЕНИЯМИ ===")
        self.test_rect_cases()
        self.test_filled_rect_cases()
        self.test_circle_cases()
        self.test_filled_circle_cases()
        self.test_rotate_cases()
        self.test_mirror_cases()
        self.test_copy_cases()
        self.test_trim_cases()
        self.test_rgbfilter_cases()
        self.test_collage_cases()
    
    def run_all_tests(self):
        """Запускает все наборы тестов"""
        print("Начало комплексного тестирования...")
        
        if not self.get_test_image():
            print("ОШИБКА: Тестовые изображения не найдены!")
            return []
        
        # Запускаем все тесты
        self.run_non_image_tests()
        self.run_image_tests()
        
        print(f"\nЗавершено {len(self.results)} тестов")
        
        # Расчет статистики
        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed
        
        print(f"Пройдено: {passed}/{len(self.results)}")
        print(f"Не пройдено: {failed}/{len(self.results)}")
        
        # Показать созданные выходные файлы
        output_files = [f for f in os.listdir(self.output_dir) if os.path.isfile(os.path.join(self.output_dir, f))]
        print(f"Выходные файлы созданы в {self.output_dir}: {len(output_files)}")
        
        return self.results

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

if __name__ == "__main__":
    tester = ImageProcessorTester()
    results = tester.run_all_tests()
    
    # Сохраняем результаты в JSON
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Выход с кодом ошибки если какие-либо тесты не пройдены
    if any(not r['success'] for r in results):
        sys.exit(1)
    else:
        sys.exit(0)