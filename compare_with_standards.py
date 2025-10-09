import json
import os
import hashlib

def compare_images_pixel_by_pixel(image1_path, image2_path):
    """
    Сравнивает два изображения побайтово.
    Возвращает True только если ВСЕ байты идентичны.
    """
    try:
        # Читаем оба файла как бинарные
        with open(image1_path, 'rb') as f1:
            image1_bytes = f1.read()
        
        with open(image2_path, 'rb') as f2:
            image2_bytes = f2.read()
        
        # Сравниваем размеры файлов
        if len(image1_bytes) != len(image2_bytes):
            print(f"❌ Размеры файлов разные: {len(image1_bytes)} vs {len(image2_bytes)} байт")
            return False
        
        # Побайтовое сравнение
        if image1_bytes == image2_bytes:
            print(f"✅ Изображения идентичны побайтово")
            return True
        else:
            # Найдем первую позицию, где байты отличаются
            diff_count = 0
            for i, (b1, b2) in enumerate(zip(image1_bytes, image2_bytes)):
                if b1 != b2:
                    if diff_count == 0:  # Показываем только первую разницу
                        print(f"❌ Байты отличаются на позиции {i}: {b1:02X} vs {b2:02X}")
                    diff_count += 1
            
            if diff_count > 0:
                print(f"❌ Всего различных байтов: {diff_count} из {len(image1_bytes)}")
            return False
        
    except FileNotFoundError as e:
        print(f"❌ Файл не найден: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка при сравнении: {e}")
        return False

def compare_images_using_hash(image1_path, image2_path):
    """
    Альтернативный метод: сравнение по хешу
    """
    try:
        with open(image1_path, 'rb') as f1:
            hash1 = hashlib.md5(f1.read()).hexdigest()
        
        with open(image2_path, 'rb') as f2:
            hash2 = hashlib.md5(f2.read()).hexdigest()
        
        if hash1 == hash2:
            print(f"✅ Хеши идентичны: {hash1}")
            return True
        else:
            print(f"❌ Хеши разные: {hash1} vs {hash2}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при сравнении хешей: {e}")
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
                
                # Метод 2: Сравнение по хешу (для проверки)
                match_hash = compare_images_using_hash(std_path, out_path)
                
                # Оба метода должны дать одинаковый результат
                if match_pixel != match_hash:
                    print("⚠️  Внимание: методы сравнения дали разные результаты!")
                
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