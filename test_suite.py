#!/usr/bin/env python3
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
        
        self.width = 800
        self.height = 500
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.bmp_images = []
        self.png_images = []
        
        if os.path.exists(self.input_dir):
            for i in range(1, 35):
                bmp_path = os.path.join(self.input_dir, f"{i}.bmp")
                png_path = os.path.join(self.input_dir, f"{i}.png")
                
                if os.path.exists(bmp_path):
                    self.bmp_images.append(bmp_path)
                if os.path.exists(png_path):
                    self.png_images.append(png_path)
        else:
            print(f"ERROR: Input directory '{self.input_dir}' not found!")
        
        print(f"Found {len(self.bmp_images)} BMP images: {[os.path.basename(p) for p in self.bmp_images]}")
        print(f"Found {len(self.png_images)} PNG images: {[os.path.basename(p) for p in self.png_images]}")
        print(f"Using coordinates for image size: {self.width}x{self.height}")
        
    def run_command(self, args: List[str]) -> Dict[str, Any]:
        """Run command and return result"""
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
                'stderr': 'Timeout expired',
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
        """Generate output path for test result"""
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        ext = os.path.splitext(input_path)[1]
        return os.path.join(self.output_dir, f"{base_name}_{operation}{ext}")
    
    def test_basic_commands(self):
        """Test basic commands and help"""
        print("Testing basic commands...")
        
        # Test 1: No arguments (should show help)
        result = self.run_command([])
        self.results.append({
            'test': 'No arguments',
            'command': ' '.join([]),
            'success': result['returncode'] == 0,
            'expected': 'Show help',
            'actual': result['stdout'][:100] + '...' if result['stdout'] else result['stderr']
        })
        
        # Test 2: Help command
        result = self.run_command(["--help"])
        self.results.append({
            'test': 'Help command',
            'command': '--help',
            'success': result['success'],
            'expected': 'Show help',
            'actual': 'Help displayed' if result['success'] else result['stderr']
        })
        
        # Test 3: Specific command help
        result = self.run_command(["--help=rect"])
        self.results.append({
            'test': 'Rect command help',
            'command': '--help=rect',
            'success': 'rectangle' in result['stdout'].lower(),
            'expected': 'Rectangle help',
            'actual': 'Help displayed' if result['success'] else result['stderr']
        })
    
    def test_info_command(self):
        """Test --info command with all images"""
        print("Testing info command...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images[:3]:  # Test first 3 images
            result = self.run_command(["--info", img_path])
            self.results.append({
                'test': f'Info {os.path.basename(img_path)}',
                'command': f'--info {img_path}',
                'success': result['success'] and 'File information' in result['stdout'],
                'expected': 'File information',
                'actual': result['stdout'][:100] if result['success'] else result['stderr']
            })
    
    def test_rect_operations_all_images(self):
        """Test rectangle drawing on all images"""
        print("Testing rectangle operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "rect")
            
            # Rectangle in center of image
            result = self.run_command([
                "--rect", 
                "--left_up", "200.150", 
                "--right_down", "800.500", 
                "--thickness", "3", 
                "--color", "255.0.0",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Rect on {os.path.basename(img_path)}',
                'command': f'rect on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_filled_rect_operations_all_images(self):
        """Test filled rectangle drawing on all images"""
        print("Testing filled rectangle operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "filled_rect")
            
            # Filled rectangle in different position
            result = self.run_command([
                "--rect",
                "--left_up", "100.100",
                "--right_down", "800.600", 
                "--thickness", "3",
                "--color", "0.255.0",
                "--fill",
                "--fill_color", "0.0.255",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Filled rect on {os.path.basename(img_path)}',
                'command': f'filled rect on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_circle_operations_all_images(self):
        """Test circle drawing on all images"""
        print("Testing circle operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "circle")
            
            # Circle in center
            result = self.run_command([
                "--circle",
                "--center", "400.225", 
                "--radius", "200",
                "--thickness", "3",
                "--color", "255.255.0",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Circle on {os.path.basename(img_path)}',
                'command': f'circle on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_filled_circle_operations_all_images(self):
        """Test filled circle drawing on all images"""
        print("Testing filled circle operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "filled_circle")
            
            # Filled circle in corner
            result = self.run_command([
                "--circle",
                "--center", "150.100",
                "--radius", "150",
                "--thickness", "1", 
                "--color", "0.255.255",
                "--fill",
                "--fill_color", "255.0.255",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Filled circle on {os.path.basename(img_path)}',
                'command': f'filled circle on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_rotate_operations_all_images(self):
        """Test rotate operations on all images"""
        print("Testing rotate operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            for angle in [90, 180, 270]:
                output_path = self.get_output_path(img_path, f"rotate{angle}")
                
                # Rotate central area
                result = self.run_command([
                    "--rotate",
                    "--left_up", "300.125",
                    "--right_down", "700.525", 
                    "--angle", str(angle),
                    "-o", output_path,
                    img_path
                ])
                self.results.append({
                    'test': f'Rotate {angle} on {os.path.basename(img_path)}',
                    'command': f'rotate {angle} on {os.path.basename(img_path)}',
                    'success': result['success'] and os.path.exists(output_path),
                    'expected': 'Output file created',
                    'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
                })
    
    def test_color_replace_all_images(self):
        """Test color replace on all images"""
        print("Testing color replace on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "color_replace")
            
            # Replace black with blue (common color)
            result = self.run_command([
                "--color_replace",
                "--old_color", "0.0.0", 
                "--new_color", "0.0.255",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Color replace on {os.path.basename(img_path)}',
                'command': f'color replace on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_mirror_operations_all_images(self):
        """Test mirror operations on all images"""
        print("Testing mirror operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            for axis in ['x', 'y']:
                output_path = self.get_output_path(img_path, f"mirror{axis}")
                
                # Mirror left side of image
                result = self.run_command([
                    "--mirror", 
                    "--axis", axis,
                    "--left_up", "50.50",
                    "--right_down", "600.600",
                    "-o", output_path,
                    img_path
                ])
                self.results.append({
                    'test': f'Mirror {axis} on {os.path.basename(img_path)}',
                    'command': f'mirror {axis} on {os.path.basename(img_path)}',
                    'success': result['success'] and os.path.exists(output_path),
                    'expected': 'Output file created',
                    'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
                })
    
    def test_trim_operations_all_images(self):
        """Test trim operations on all images"""
        print("Testing trim operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "trim")
            
            # Trim to central area
            result = self.run_command([
                "--trim",
                "--left_up", "200.100", 
                "--right_down", "800.550",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Trim on {os.path.basename(img_path)}',
                'command': f'trim on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_copy_operations_all_images(self):
        """Test copy operations on all images"""
        print("Testing copy operations on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            output_path = self.get_output_path(img_path, "copy")
            
            # Copy from top-left to bottom-right
            result = self.run_command([
                "--copy",
                "--left_up", "50.50",
                "--right_down", "200.150", 
                "--dest_left_up", "800.600",
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Copy on {os.path.basename(img_path)}',
                'command': f'copy on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_rgbfilter_operations_all_images(self):
        """Test RGB filter operations on all images"""
        print("Testing RGB filter on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images:
            for component in ['red', 'green', 'blue']:
                output_path = self.get_output_path(img_path, f"filter{component}")
                
                result = self.run_command([
                    "--rgbfilter",
                    "--component_name", component,
                    "--component_value", "150",
                    "-o", output_path,
                    img_path
                ])
                self.results.append({
                    'test': f'RGB filter {component} on {os.path.basename(img_path)}',
                    'command': f'filter {component} on {os.path.basename(img_path)}',
                    'success': result['success'] and os.path.exists(output_path),
                    'expected': 'Output file created',
                    'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
                })
    
    def test_collage_operations_all_images(self):
        """Test collage operations on all images"""
        print("Testing collage on all images...")
        
        all_images = self.bmp_images + self.png_images
        for img_path in all_images[:2]:  # Only test 2 images (creates large files)
            output_path = self.get_output_path(img_path, "collage")
            
            result = self.run_command([
                "--collage",
                "--number_x", "2",
                "--number_y", "2", 
                "-o", output_path,
                img_path
            ])
            self.results.append({
                'test': f'Collage on {os.path.basename(img_path)}',
                'command': f'collage on {os.path.basename(img_path)}',
                'success': result['success'] and os.path.exists(output_path),
                'expected': 'Output file created',
                'actual': f'File created: {os.path.basename(output_path)}' if os.path.exists(output_path) else result['stderr']
            })
    
    def test_error_cases(self):
        """Test error handling"""
        print("Testing error cases...")
        
        # Use first existing image for error tests
        if self.bmp_images:
            test_image = self.bmp_images[0]
        elif self.png_images:
            test_image = self.png_images[0]
        else:
            print("No images found for error testing")
            return
        
        # Test 1: Unknown option
        result = self.run_command(["--unknown_option", test_image])
        self.results.append({
            'test': 'Unknown option',
            'command': '--unknown_option',
            'success': result['returncode'] == ERR_CMD_ARGS,
            'expected': 'Error code 42',
            'actual': f"Code {result['returncode']}"
        })
        
        # Test 2: Invalid color format
        result = self.run_command([
            "--rect", "--left_up", "100.100", "--right_down", "200.200",
            "--thickness", "2", "--color", "300.0.0", test_image
        ])
        self.results.append({
            'test': 'Invalid color',
            'command': 'color 300.0.0',
            'success': result['returncode'] == ERR_COLOR,
            'expected': 'Error code 43', 
            'actual': f"Code {result['returncode']}"
        })
        
        # Test 3: Missing required parameters
        result = self.run_command(["--rect", test_image])
        self.results.append({
            'test': 'Missing parameters',
            'command': 'rect without params',
            'success': result['returncode'] == ERR_CMD_ARGS,
            'expected': 'Error code 42',
            'actual': f"Code {result['returncode']}"
        })
        
        # Test 4: Multiple operations
        result = self.run_command(["--rect", "--circle", test_image])
        self.results.append({
            'test': 'Multiple operations',
            'command': 'rect and circle',
            'success': result['returncode'] == ERR_CMD_ARGS,
            'expected': 'Error code 42',
            'actual': f"Code {result['returncode']}"
        })
        
        # Test 5: Non-existent file
        result = self.run_command(["--info", "nonexistent.bmp"])
        self.results.append({
            'test': 'Non-existent file',
            'command': 'info nonexistent.bmp',
            'success': result['returncode'] == ERR_FILE_FORMAT,
            'expected': 'Error code 41',
            'actual': f"Code {result['returncode']}"
        })
    
    def run_all_tests(self):
        """Run all test suites"""
        print("Starting comprehensive testing with real images...")
        print(f"Testing with {len(self.bmp_images)} BMP and {len(self.png_images)} PNG images")
        print(f"All operations optimized for {self.width}x{self.height} images")
        
        if not self.bmp_images and not self.png_images:
            print("ERROR: No test images found!")
            return []
        
        self.test_basic_commands()
        self.test_info_command() 
        self.test_rect_operations_all_images()
        self.test_filled_rect_operations_all_images()
        self.test_circle_operations_all_images()
        self.test_filled_circle_operations_all_images()
        self.test_rotate_operations_all_images()
        self.test_color_replace_all_images()
        self.test_mirror_operations_all_images()
        self.test_trim_operations_all_images()
        self.test_copy_operations_all_images()
        self.test_rgbfilter_operations_all_images()
        self.test_collage_operations_all_images()
        self.test_error_cases()
        
        print(f"\nCompleted {len(self.results)} tests")
        
        # Calculate statistics
        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed
        
        print(f"Passed: {passed}/{len(self.results)}")
        print(f"Failed: {failed}/{len(self.results)}")
        
        # Show output files created
        output_files = [f for f in os.listdir(self.output_dir) if os.path.isfile(os.path.join(self.output_dir, f))]
        print(f"Output files created in {self.output_dir}: {len(output_files)}")
        
        return self.results

# Error codes (copy from main script)
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
    
    # Save results to JSON for GitLab CI
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with error code if any tests failed
    if any(not r['success'] for r in results):
        sys.exit(1)
    else:
        sys.exit(0)