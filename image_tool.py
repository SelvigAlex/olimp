#!/usr/bin/env python3
import argparse
import sys
import sqlite3
import os
from typing import Tuple, Optional
from datetime import datetime

from PIL import Image, ImageDraw

# Error codes
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

DB_FILE = 'files.db'

# ----------------- Database Helpers -----------------
def init_database():
    """Initialize database with required tables"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS processed_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_type TEXT,
            width INTEGER,
            height INTEGER, 
            file_size_kb REAL
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS processing_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            output_filename TEXT NOT NULL,
            operation_command TEXT NOT NULL,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES processed_files (id)
        )''')
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Warning: Could not initialize database: {e}", file=sys.stderr)


def log_processing(in_name: str, out_name: str, command: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Сначала проверяем существование файла в базе
        c.execute('SELECT id FROM processed_files WHERE filename = ?', (in_name,))
        result = c.fetchone()
        
        if result:
            # Файл уже существует, используем существующий ID
            file_id = result[0]
            
            # Обновляем информацию о файле (на случай если он изменился)
            try:
                img = Image.open(in_name)
                width, height = img.size
                file_size_bytes = os.path.getsize(in_name)
                file_size_kb = file_size_bytes / 1024.0
                file_type = img.format or 'Unknown'
                
                c.execute('''UPDATE processed_files 
                           SET file_type = ?, width = ?, height = ?, file_size_kb = ?
                           WHERE id = ?''',
                         (file_type, width, height, file_size_kb, file_id))
            except Exception as e:
                print(f"Warning: Could not update file info for logging: {e}", file=sys.stderr)
                
        else:
            # Файл не существует, создаем новую запись
            try:
                img = Image.open(in_name)
                width, height = img.size
                file_size_bytes = os.path.getsize(in_name)
                file_size_kb = file_size_bytes / 1024.0
                file_type = img.format or 'Unknown'
            except Exception as e:
                print(f"Warning: Could not get file info for logging: {e}", file=sys.stderr)
                width = height = 0
                file_size_kb = 0
                file_type = 'Unknown'
            
            c.execute('''INSERT INTO processed_files 
                        (filename, file_type, width, height, file_size_kb)
                        VALUES (?, ?, ?, ?, ?)''',
                     (in_name, file_type, width, height, file_size_kb))
            file_id = c.lastrowid
        
        # Добавляем запись об операции
        c.execute('''INSERT INTO processing_operations 
                    (file_id, output_filename, operation_command)
                    VALUES (?, ?, ?)''',
                 (file_id, out_name, command))
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Warning: Database error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not log processing: {e}", file=sys.stderr)


def exit_err(msg: str, code: int):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)

def parse_rgb(s: str) -> Tuple[int,int,int]:
    parts = s.split('.')
    if len(parts) != 3:
        raise ValueError('invalid color format')
    try:
        vals = [int(p) for p in parts]
    except Exception:
        raise ValueError('invalid color components')
    for v in vals:
        if not (0 <= v <= 255):
            raise ValueError('color components must be between 0 and 255')
    return tuple(vals)

def parse_point(s: str) -> Tuple[int,int]:
    parts = s.split('.')
    if len(parts) != 2:
        raise ValueError('invalid point format')
    try:
        x = int(parts[0])
        y = int(parts[1])
    except Exception:
        raise ValueError('invalid coordinates')
    return x, y

def ensure_image_openable(path: str) -> Image.Image:
    if not os.path.isfile(path):
        exit_err('Incorrect input file', ERR_FILE_FORMAT)
    try:
        img = Image.open(path)
        img.verify()
        img = Image.open(path).convert('RGB')
        return img
    except Exception as e:
        if "cannot identify image file" in str(e).lower():
            exit_err('Not a BMP file', ERR_FILE_FORMAT)
        exit_err('Incorrect input file', ERR_FILE_FORMAT)

def save_image(img: Image.Image, out_path: str, src_path: str):
    if os.path.abspath(out_path) == os.path.abspath(src_path):
        exit_err('Input and output files cannot be the same', ERR_CMD_ARGS)
    try:
        img.save(out_path)
    except Exception:
        exit_err('Error saving image', ERR_IO)

def op_info(img: Image.Image, path: str):
    size = os.path.getsize(path)
    w,h = img.size
    print("File information:")
    print(f"File size: {size}")
    print(f"Width: {w}")
    print(f"Height: {h}")

def validate_rectangle(left_up, right_down, width, height):
    """Проверка прямоугольника на валидность (из нижнего кода)"""
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

def op_rect(img: Image.Image, left_up:Tuple[int,int], right_down:Tuple[int,int], thickness:int, color:Tuple[int,int,int], fill:bool=False, fill_color:Optional[Tuple[int,int,int]]=None):
    """Рисование прямоугольника (упрощенная версия из нижнего кода)"""
    draw = ImageDraw.Draw(img)
    
    if thickness <= 0:
        exit_err('Thickness must be positive', ERR_DRAW)
    if fill and fill_color is None:
        exit_err('Fill specified but no fill_color', ERR_CMD_ARGS)
    
    # Корректируем координаты как в нижнем коде
    left_up, right_down = validate_rectangle(left_up, right_down, img.width, img.height)

    if fill:
        if fill_color is None:
            fill_color = color
        draw.rectangle([left_up, right_down], outline=color, fill=fill_color, width=thickness)
    else:
        draw.rectangle([left_up, right_down], outline=color, width=thickness)

def op_circle(img: Image.Image, center:Tuple[int,int], radius:int, thickness:int, color:Tuple[int,int,int], fill:bool=False, fill_color:Optional[Tuple[int,int,int]]=None):
    """Рисование окружности (упрощенная версия из нижнего кода)"""
    draw = ImageDraw.Draw(img)
    cx, cy = center
    
    if radius <= 0 or thickness <= 0:
        exit_err('Radius and thickness must be positive', ERR_DRAW)
    if fill and fill_color is None:
        exit_err('Fill specified but no fill_color', ERR_CMD_ARGS)
    
    if cx < 0 or cy < 0 or cx >= img.width or cy >= img.height:
        raise ValueError("Center coordinates out of bounds")

    bbox = [(cx - radius, cy - radius), (cx + radius, cy + radius)]

    if fill:
        if fill_color is None:
            fill_color = color
        draw.ellipse(bbox, outline=color, fill=fill_color, width=thickness)
    else:
        draw.ellipse(bbox, outline=color, width=thickness)

def clamp_area(left:int, up:int, right:int, down:int, w:int, h:int):
    l = max(0, min(left, w))
    u = max(0, min(up, h))
    r = max(0, min(right, w))
    d = max(0, min(down, h))
    return l,u,r,d

def op_rotate(img: Image.Image, left_up:Tuple[int,int], right_down:Tuple[int,int], angle:int):
    if angle not in (90,180,270):
        exit_err('Invalid angle', ERR_DRAW)
    x1,y1 = left_up; x2,y2 = right_down
    w,h = img.size
    l,u,r,d = clamp_area(x1,y1,x2,y2,w,h)
    if l>=r or u>=d:
        exit_err('Rotate area empty', ERR_TRIM)
    box = (l,u,r,d)
    region = img.crop(box)
    region = region.rotate(angle, expand=True)
    rw,rh = region.size
    target_w = r-l; target_h = d-u
    if rw != target_w or rh != target_h:
        region = region.crop((0,0,min(rw,target_w), min(rh,target_h)))
    img.paste(region, (l,u))

def op_color_replace(img: Image.Image, old_color:Tuple[int,int,int], new_color:Tuple[int,int,int]):
    """Замена цвета (упрощенная версия)"""
    px = img.load()
    w,h = img.size
    replaced = 0
    for y in range(h):
        for x in range(w):
            if px[x,y] == old_color:
                px[x,y] = new_color
                replaced += 1
    return replaced

def op_mirror(img: Image.Image, axis:str, left_up:Tuple[int,int], right_down:Tuple[int,int]):
    """Отражение области (упрощенная версия)"""
    if axis not in ('x','y'):
        exit_err('Invalid axis', ERR_CMD_ARGS)
    
    left_up, right_down = validate_rectangle(left_up, right_down, img.width, img.height)
    
    region = img.crop((left_up[0], left_up[1], right_down[0] + 1, right_down[1] + 1))

    if axis == 'x':
        mirrored_region = region.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        mirrored_region = region.transpose(Image.FLIP_TOP_BOTTOM)

    img.paste(mirrored_region, (left_up[0], left_up[1]))

def op_trim(img: Image.Image, left_up:Tuple[int,int], right_down:Tuple[int,int]) -> Image.Image:
    """Обрезка изображения (упрощенная версия)"""
    left_up, right_down = validate_rectangle(left_up, right_down, img.width, img.height)
    
    return img.crop((left_up[0], left_up[1], right_down[0] + 1, right_down[1] + 1))

def op_copy(img: Image.Image, src_left_up:Tuple[int,int], src_right_down:Tuple[int,int], dest_left_up:Tuple[int,int]):
    """Копирование области (упрощенная версия)"""
    src_left_up, src_right_down = validate_rectangle(src_left_up, src_right_down, img.width, img.height)
    
    dest_x, dest_y = dest_left_up

    if dest_x < 0 or dest_y < 0 or dest_x >= img.width or dest_y >= img.height:
        return

    region = img.crop((src_left_up[0], src_left_up[1], src_right_down[0] + 1, src_right_down[1] + 1))

    img.paste(region, (dest_x, dest_y))

def op_rgbfilter(img: Image.Image, component_name:str, component_value:int):
    """RGB фильтр (упрощенная версия)"""
    if component_name not in ('red','green','blue'):
        exit_err('--component_name [red|green|blue] required', ERR_CMD_ARGS)
    if not (0 <= component_value <= 255):
        exit_err('--component_value 0-255', ERR_CMD_ARGS)
    px = img.load()
    w,h = img.size
    for y in range(h):
        for x in range(w):
            r,g,b = px[x,y]
            if component_name == 'red':
                px[x,y] = (component_value, g, b)
            elif component_name == 'green':
                px[x,y] = (r, component_value, b)
            else:
                px[x,y] = (r, g, component_value)

def print_help(command=None):
    if command is None:
        print("Basic options:")
        print("\t-h, --help[=COMMAND]\tShow help (general or for specific command)")
        print("\t-i, --input=FILE\tInput BMP/PNG image file (required)")
        print("\t-o, --output=FILE\tOutput BMP/PNG image file (default: out.bmp/out.png)")
        print("\t--info\t\t\tShow image information\n")
        print("Operations (only one at a time):")
        print("\t--rect\t\t\tDraw rectangle")
        print("\t--circle\t\tDraw circle")
        print("\t--rotate\t\tRotate area")
        print("\t--color_replace\t\tReplace color")
        print("\t--mirror\t\tMirror area")
        print("\t--trim\t\t\tTrim image")
        print("\t--copy\t\t\tCopy area")
        print("\t--rgbfilter\t\tApply RGB filter")
        print("\t--collage\t\tCreate collage\n")
        print("For detailed help on specific operations, use:")
        print("\t--help=rect")
        print("\t--help=circle")
        print("\t--help=rotate")
        print("\t--help=color_replace")
    
    elif command == 'rect':
        print("Draw rectangle operation:\n")
        print("Required parameters:")
        print("\t--left_up=X.Y\t\tCoordinates of first point")
        print("\t--right_down=X.Y\tCoordinates of second point")
        print("\t--thickness=N\t\tBorder thickness (positive integer)")
        print("\t--color=R.G.B\t\tBorder color (RGB values, 0-255)\n")
        print("Optional parameters:")
        print("\t--fill\t\t\tEnable fill")
        print("\t--fill_color=R.G.B\tFill color (RGB values, 0-255)")
    
    elif command == 'circle':
        print("Draw circle operation:\n")
        print("Required parameters:")
        print("\t--center=X.Y\t\tCenter coordinates")
        print("\t--radius=N\t\tCircle radius (positive integer)")
        print("\t--thickness=N\t\tBorder thickness (positive integer)")
        print("\t--color=R.G.B\t\tBorder color (RGB values, 0-255)\n")
        print("Optional parameters:")
        print("\t--fill\t\t\tEnable fill")
        print("\t--fill_color=R.G.B\tFill color (RGB values, 0-255)")
    
    elif command == 'rotate':
        print("Rotate area operation:\n")
        print("Required parameters:")
        print("\t--left_up=X.Y\t\tCoordinates of first point")
        print("\t--right_down=X.Y\tCoordinates of second point")
        print("\t--angle=N\t\tRotation angle (Angles multiple of 90 from 0 to 270)")
    
    elif command == 'color_replace':
        print("Color replace operation:\n")
        print("Required parameters:")
        print("\t--old_color=R.G.B\tColor to replace (RGB values, 0-255)")
        print("\t--new_color=R.G.B\tNew color (RGB values, 0-255)")
    
    else:
        print(f"No detailed help available for: {command}")

def build_parser():
    p = argparse.ArgumentParser(prog='cw', add_help=False, allow_abbrev=False)
    
    p.add_argument('-h', '--help', nargs='?', const='__general__', metavar='COMMAND')
    p.add_argument('-i', '--input', help='Input image file')
    p.add_argument('-o', '--output', help='Output image file')
    p.add_argument('--info', action='store_true', help='Show image information')

    p.add_argument('--rect', action='store_true', help='Draw rectangle')
    p.add_argument('--circle', action='store_true', help='Draw circle')
    p.add_argument('--rotate', action='store_true', help='Rotate area')
    p.add_argument('--color_replace', action='store_true', help='Replace color')
    p.add_argument('--mirror', action='store_true', help='Mirror area')
    p.add_argument('--trim', action='store_true', help='Trim image')
    p.add_argument('--copy', action='store_true', help='Copy area')
    p.add_argument('--rgbfilter', action='store_true', help='Apply RGB filter')
    p.add_argument('--collage', action='store_true', help='Create collage')

    p.add_argument('--left_up', help='Coordinates of left upper point (X.Y)')
    p.add_argument('--right_down', help='Coordinates of right lower point (X.Y)')
    p.add_argument('--thickness', type=int, help='Border thickness')
    p.add_argument('--color', help='Color in R.G.B format')
    p.add_argument('--fill', action='store_true', help='Enable fill')
    p.add_argument('--fill_color', help='Fill color in R.G.B format')
    p.add_argument('--center', help='Center coordinates (X.Y)')
    p.add_argument('--radius', type=int, help='Circle radius')
    p.add_argument('--angle', type=int, help='Rotation angle')
    p.add_argument('--old_color', help='Old color to replace')
    p.add_argument('--new_color', help='New color')
    p.add_argument('--axis', help='Mirror axis (x or y)')
    p.add_argument('--dest_left_up', help='Destination coordinates for copy')
    p.add_argument('--component_name', help='RGB component name')
    p.add_argument('--component_value', type=int, help='RGB component value')
    p.add_argument('--number_x', type=int, help='Number of horizontal parts')
    p.add_argument('--number_y', type=int, help='Number of vertical parts')

    p.add_argument('input_file', nargs='?', help='Input image file')

    return p


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        if "unrecognized arguments" in message:
            import re
            match = re.search(r"unrecognized arguments: (.*)", message)
            if match:
                option = match.group(1).split()[0]
                exit_err("Incorrect argument", ERR_CMD_ARGS)
        elif "expected one argument" in message:
            option = message.split()[-1]
            exit_err("Incorrect argument", ERR_CMD_ARGS)
        else:
            exit_err(message, ERR_CMD_ARGS)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    
    init_database()
    
    if len(argv) == 0:
        print_help()
        sys.exit(0)
    
    known_flags = {'-h', '--help', '-i', '--input', '-o', '--output', '--info', 
                   '--rect', '--circle', '--rotate', '--color_replace', '--mirror',
                   '--trim', '--copy', '--rgbfilter', '--collage', '--left_up',
                   '--right_down', '--thickness', '--color', '--fill', '--fill_color',
                   '--center', '--radius', '--angle', '--old_color', '--new_color',
                   '--axis', '--dest_left_up', '--component_name', '--component_value',
                   '--number_x', '--number_y'}
    
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('-'):
            if '=' in arg:
                arg = arg.split('=')[0]
            if arg not in known_flags and not arg.replace('-', '').isdigit():
                # print(f"{os.path.basename(sys.argv[0])}: unrecognized option '{arg}'", file=sys.stderr)
                exit_err("Incorrect argument", ERR_CMD_ARGS)
        i += 1

    parser = CustomArgumentParser(prog=os.path.basename(sys.argv[0]), add_help=False, allow_abbrev=False)
    
    parser.add_argument('-h', '--help', nargs='?', const='__general__', metavar='COMMAND')
    parser.add_argument('-i', '--input', help='Input image file')
    parser.add_argument('-o', '--output', help='Output image file')
    parser.add_argument('--info', action='store_true', help='Show image information')

    parser.add_argument('--rect', action='store_true', help='Draw rectangle')
    parser.add_argument('--circle', action='store_true', help='Draw circle')
    parser.add_argument('--rotate', action='store_true', help='Rotate area')
    parser.add_argument('--color_replace', action='store_true', help='Replace color')
    parser.add_argument('--mirror', action='store_true', help='Mirror area')
    parser.add_argument('--trim', action='store_true', help='Trim image')
    parser.add_argument('--copy', action='store_true', help='Copy area')
    parser.add_argument('--rgbfilter', action='store_true', help='Apply RGB filter')
    parser.add_argument('--collage', action='store_true', help='Create collage')

    parser.add_argument('--left_up', help='Coordinates of left upper point (X.Y)')
    parser.add_argument('--right_down', help='Coordinates of right lower point (X.Y)')
    parser.add_argument('--thickness', type=int, help='Border thickness')
    parser.add_argument('--color', help='Color in R.G.B format')
    parser.add_argument('--fill', action='store_true', help='Enable fill')
    parser.add_argument('--fill_color', help='Fill color in R.G.B format')
    parser.add_argument('--center', help='Center coordinates (X.Y)')
    parser.add_argument('--radius', type=int, help='Circle radius')
    parser.add_argument('--angle', type=int, help='Rotation angle')
    parser.add_argument('--old_color', help='Old color to replace')
    parser.add_argument('--new_color', help='New color')
    parser.add_argument('--axis', help='Mirror axis (x or y)')
    parser.add_argument('--dest_left_up', help='Destination coordinates for copy')
    parser.add_argument('--component_name', help='RGB component name')
    parser.add_argument('--component_value', type=int, help='RGB component value')
    parser.add_argument('--number_x', type=int, help='Number of horizontal parts')
    parser.add_argument('--number_y', type=int, help='Number of vertical parts')

    parser.add_argument('input_file', nargs='?', help='Input image file')

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        sys.exit(ERR_CMD_ARGS)

    if args.help:
        if args.help == '__general__':
            print_help()
        else:
            print_help(args.help)
        sys.exit(0)

    in_name = args.input or args.input_file
    if in_name is None:
        exit_err('--input is required', ERR_CMD_ARGS)

    if args.output:
        out_name = args.output
    else:
        if '.' in in_name:
            ext = os.path.splitext(in_name)[1]
            out_name = f'out{ext}'
        else:
            out_name = 'out.bmp'

    img = ensure_image_openable(in_name)

    if args.info:
        for arg in ['left_up', 'right_down', 'thickness', 'color', 'fill', 'fill_color',
                   'center', 'radius', 'angle', 'old_color', 'new_color', 'axis',
                   'dest_left_up', 'component_name', 'component_value', 'number_x', 'number_y']:
            if getattr(args, arg):
                print("This option does not take arguments", file=sys.stderr)
                exit_err("Incorrect argument", ERR_CMD_ARGS)
        op_info(img, in_name)
        log_processing(in_name, out_name, '--info')
        sys.exit(0)

    ops = [args.rect, args.circle, args.rotate, args.color_replace, 
           args.mirror, args.trim, args.copy, args.rgbfilter, args.collage]
    op_count = sum(bool(x) for x in ops)
    
    if op_count == 0:
        exit_err('No operation specified', ERR_CMD_ARGS)
    elif op_count > 1:
        exit_err('Only one operation can be performed at a time', ERR_CMD_ARGS)

    try:
        if args.rect:
            if not all([args.left_up, args.right_down, args.thickness, args.color]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            lu = parse_point(args.left_up)
            rd = parse_point(args.right_down)
            color = parse_rgb(args.color)
            fill_color = parse_rgb(args.fill_color) if args.fill_color else None
            
            if args.thickness <= 0:
                exit_err('Thickness must be positive', ERR_DRAW)
                
            op_rect(img, lu, rd, args.thickness, color, args.fill, fill_color)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--rect')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.circle:
            if not all([args.center, args.radius, args.thickness, args.color]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            center = parse_point(args.center)
            color = parse_rgb(args.color)
            fill_color = parse_rgb(args.fill_color) if args.fill_color else None
            
            if args.radius <= 0 or args.thickness <= 0:
                exit_err('Radius and thickness must be positive', ERR_DRAW)
                
            op_circle(img, center, args.radius, args.thickness, color, args.fill, fill_color)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--circle')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.rotate:
            if not all([args.left_up, args.right_down, args.angle is not None]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            lu = parse_point(args.left_up)
            rd = parse_point(args.right_down)
            
            if args.angle not in (90, 180, 270):
                exit_err('Invalid angle', ERR_DRAW)
                
            op_rotate(img, lu, rd, args.angle)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--rotate')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.color_replace:
            if not all([args.old_color, args.new_color]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            oldc = parse_rgb(args.old_color)
            newc = parse_rgb(args.new_color)
            
            replaced = op_color_replace(img, oldc, newc)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--color_replace')
            print(f"Replaced {replaced} pixels. Output saved to {out_name}")

        elif args.mirror:
            if not all([args.axis, args.left_up, args.right_down]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            lu = parse_point(args.left_up)
            rd = parse_point(args.right_down)
            
            if args.axis not in ('x', 'y'):
                exit_err('Invalid axis', ERR_CMD_ARGS)
                
            op_mirror(img, args.axis, lu, rd)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--mirror')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.trim:
            if not all([args.left_up, args.right_down]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            lu = parse_point(args.left_up)
            rd = parse_point(args.right_down)
            
            new_img = op_trim(img, lu, rd)
            save_image(new_img, out_name, in_name)
            log_processing(in_name, out_name, '--trim')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.copy:
            if not all([args.left_up, args.right_down, args.dest_left_up]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            src_lu = parse_point(args.left_up)
            src_rd = parse_point(args.right_down)
            dest_lu = parse_point(args.dest_left_up)
            
            op_copy(img, src_lu, src_rd, dest_lu)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--copy')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.rgbfilter:
            if not all([args.component_name, args.component_value is not None]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
                
            if args.component_name not in ('red', 'green', 'blue'):
                exit_err('--component_name [red|green|blue] required', ERR_CMD_ARGS)
            if not (0 <= args.component_value <= 255):
                exit_err('--component_value 0-255', ERR_CMD_ARGS)
                
            op_rgbfilter(img, args.component_name, args.component_value)
            save_image(img, out_name, in_name)
            log_processing(in_name, out_name, '--rgbfilter')
            print(f"Operation completed successfully. Output saved to {out_name}")

        elif args.collage:
            if not all([args.number_x, args.number_y]):
                exit_err('Missing required flags', ERR_CMD_ARGS)
            nx = args.number_x
            ny = args.number_y
            
            if nx <= 0 or ny <= 0:
                exit_err('Number of tiles must be positive', ERR_CMD_ARGS)
                
            w,h = img.size
            new = Image.new('RGB', (w*nx, h*ny))
            for i in range(ny):
                for j in range(nx):
                    new.paste(img, (j*w, i*h))
            save_image(new, out_name, in_name)
            log_processing(in_name, out_name, '--collage')
            print(f"Operation completed successfully. Output saved to {out_name}")

    except ValueError as e:
        error_msg = str(e)
        if 'color' in error_msg:
            if 'invalid color format' in error_msg:
                exit_err('invalid color format', ERR_COLOR)
            else:
                exit_err('Incorrect color', ERR_COLOR)
        elif 'point' in error_msg or 'coordinates' in error_msg:
            exit_err('invalid coordinates format', ERR_COORDS)
        else:
            exit_err(error_msg, ERR_CMD_ARGS)
    except MemoryError:
        exit_err('Memory error', ERR_MEMORY)
    except Exception as e:
        exit_err(f'General error: {str(e)}', ERR_GENERAL)

if __name__ == '__main__':
    main()