import subprocess
import sys
import os
import glob

def cleanup():
    """Очистка предыдущих тестовых файлов"""
    files_to_remove = [
        'out.bmp', 'out.png', 'test_results.json', 'test_report.xlsx', 
        'comparison_results.json', 'final_test_report.xlsx'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Удален {file}")
    
    # Очищаем output_photos, но сохраняем директорию
    if os.path.exists("output_photos"):
        for file in os.listdir("output_photos"):
            file_path = os.path.join("output_photos", file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("Очищена директория output_photos")

def run_full_test():
    print("=== РАСШИРЕННЫЙ КОМПЛЕКСНЫЙ ТЕСТ ОБРАБОТКИ ИЗОБРАЖЕНИЙ ===")
    print("Тестирование всех возможных случаев использования image_tool.py")
    
    print("\n0. Очистка предыдущих тестовых файлов...")
    cleanup()
    
    if not os.path.exists("input_photos"):
        print("ОШИБКА: Директория input_photos не найдена!")
        print("Создайте директорию input_photos с тестовыми изображениями")
        return False
    
    # Проверяем наличие изображений
    bmp_files = [f for f in os.listdir('input_photos') if f.endswith('.bmp')]
    png_files = [f for f in os.listdir('input_photos') if f.endswith('.png')]
    
    print(f"Найдено {len(bmp_files)} BMP изображений в input_photos/")
    print(f"Найдено {len(png_files)} PNG изображений в input_photos/")
    
    if len(bmp_files) + len(png_files) == 0:
        print("ОШИБКА: Тестовые изображения не найдены в input_photos/!")
        return False
    
    # Создаем необходимые директории
    os.makedirs("output_photos", exist_ok=True)
    
    print("\n1. Запуск расширенного набора тестов...")
    result = subprocess.run([sys.executable, "test_suite.py"])
    if result.returncode != 0:
        print("ПРЕДУПРЕЖДЕНИЕ: Некоторые тесты не пройдены")
    
    print("\n2. Генерация Excel отчетов...")
    result = subprocess.run([sys.executable, "generate_excel_report.py"])
    if result.returncode != 0:
        print("ОШИБКА: Не удалось сгенерировать базовый отчет")
    
    result = subprocess.run([sys.executable, "generate_final_report.py"])
    if result.returncode != 0:
        print("ОШИБКА: Не удалось сгенерировать итоговый отчет")
    
    print("\n3. Завершение тестирования!")
    
    # Показываем итоговую статистику
    if os.path.exists("test_results.json"):
        import json
        with open('test_results.json', 'r') as f:
            test_results = json.load(f)
        passed = sum(1 for r in test_results if r['success'])
        total = len(test_results)
        print(f"\n=== ИТОГОВАЯ СТАТИСТИКА ===")
        print(f"Всего тестов: {total}")
        print(f"Пройдено: {passed}")
        print(f"Не пройдено: {total - passed}")
        print(f"Процент успеха: {passed/total*100:.1f}%")
    
    print(f"\nРезультаты сохранены в:")
    print(f"- output_photos/ - обработанные изображения")
    print(f"- test_results.json - детальные результаты тестов") 
    print(f"- test_report.xlsx - Excel отчет по тестам")
    print(f"- final_test_report.xlsx - итоговый отчет")
    
    print(f"\nДля сравнения с эталонными изображениями выполните:")
    print(f"python compare_with_standards.py")
    
    return True

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)