import json
import os
import hashlib
from PIL import Image


def compare_images_pixel_by_pixel(image1_path, image2_path):
    """
    Сравнивает два изображения по пикселям.
    Возвращает True только если ВСЕ пиксели идентичны.
    """
    try:
        
        # Открываем оба изображения
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)
        
        # Преобразуем в RGB для единообразия
        # img1 = img1.convert('RGB')
        # img2 = img2.convert('RGB')
        
        # Сравниваем размеры изображений
        if img1.size != img2.size:
            print(f"❌ Размеры изображений разные: {img1.size} vs {img2.size}")
            return False
        
        width, height = img1.size
        
        # Сравниваем пиксели
        diff_count = 0
        different_pixels = []
        
        for y in range(height):
            for x in range(width):
                pixel1 = img1.getpixel((x, y))
                pixel2 = img2.getpixel((x, y))
                
                if pixel1 != pixel2:
                    diff_count += 1
                    if len(different_pixels) < 5:  # Сохраняем первые 5 отличающихся пикселей
                        different_pixels.append((x, y, pixel1, pixel2))
        
        if diff_count == 0:
            print(f"✅ Изображения идентичны по пикселям")
            return True
        else:
            print(f"❌ Количество отличающихся пикселей: {diff_count} из {width * height}")
            
            # Показываем информацию о первых отличающихся пикселях
            if different_pixels:
                print("Первые отличающиеся пиксели (x, y, pixel1, pixel2):")
                for i, (x, y, p1, p2) in enumerate(different_pixels):
                    print(f"  {i+1}. ({x}, {y}): {p1} vs {p2}")
            
            # Дополнительная статистика
            diff_percentage = (diff_count / (width * height)) * 100
            print(f"❌ Процент отличающихся пикселей: {diff_percentage:.2f}%")
            
            return False
        
    except FileNotFoundError as e:
        print(f"❌ Файл не найден: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при сравнении: {e}")
        return False

def strict_image_comparison():
    """Строгое сравнение изображений побайтово"""
    standard_dir = "standard_photos"
    output_dir = "output_photos"
    
    results = {
        'summary': {
            'total_comparisons': 0,
            'matches': 0,
            'mismatches': 0,
            'match_percentage': 0
        },
        'comparisons': []
    }
    
    # Ищем соответствующие файлы для сравнения
    if os.path.exists(standard_dir) and os.path.exists(output_dir):
        # Получаем все файлы из output_photos для сравнения
        output_files = [f for f in os.listdir(output_dir) if f.endswith(('.bmp', '.png'))]
        
        for output_file in output_files:
            # Ищем соответствующий файл в standard_photos
            # Предполагаем, что имена файлов совпадают
            std_file = output_file
            std_path = os.path.join(standard_dir, std_file)
            out_path = os.path.join(output_dir, output_file)
            
            if os.path.exists(std_path):
                print(f"\n=== Сравнение {std_file} ===")
                
                # Метод 1: Побайтовое сравнение
                match_pixel = compare_images_pixel_by_pixel(std_path, out_path)
                
                # Используем побайтовое сравнение как основной критерий
                match = match_pixel
                
                results['comparisons'].append({
                    'standard_file': std_file,
                    'output_file': output_file,
                    'match': match,
                    'method': 'pixel_by_pixel',
                    'file_size_std': os.path.getsize(std_path),
                    'file_size_out': os.path.getsize(out_path)
                })
                
                results['summary']['total_comparisons'] += 1
                if match:
                    results['summary']['matches'] += 1
                    print(f"✅ ТЕСТ ПРОЙДЕН: {std_file}")
                else:
                    results['summary']['mismatches'] += 1
                    print(f"❌ ТЕСТ НЕ ПРОЙДЕН: {std_file}")
            else:
                print(f"⚠️  Эталонный файл {std_file} не найден в {standard_dir}")
    
    # Расчет процента совпадения
    total = results['summary']['total_comparisons']
    if total > 0:
        results['summary']['match_percentage'] = (results['summary']['matches'] / total) * 100
    
    # Сохраняем результаты
    with open('comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== ИТОГИ СТРОГОГО СРАВНЕНИЯ ===")
    print(f"Всего сравнений: {results['summary']['total_comparisons']}")
    print(f"Совпадений: {results['summary']['matches']}")
    print(f"Несовпадений: {results['summary']['mismatches']}")
    print(f"Процент совпадения: {results['summary']['match_percentage']:.1f}%")
    
    return results

def validate_directories():
    """Проверяем существование необходимых директорий"""
    if not os.path.exists("output_photos"):
        print("❌ Директория output_photos не найдена!")
        return False
    return True

if __name__ == "__main__":
    print("=== СТРОГОЕ СРАВНЕНИЕ ИЗОБРАЖЕНИЙ (ПОБАЙТОВО) ===")
    
    if validate_directories():
        results = strict_image_comparison()
        
        if results['summary']['total_comparisons'] == 0:
            print("\n⚠️  Нет файлов для сравнения")
            print("Убедитесь, что:")
            print("1. В output_photos есть обработанные изображения")
            print("2. В standard_photos есть соответствующие эталонные изображения")
    else:
        print("Необходимые директории не найдены.")
        print("Создайте output_photos с результатами обработки")