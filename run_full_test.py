#!/usr/bin/env python3
import subprocess
import sys
import os
import glob

def cleanup():
    files_to_remove = [
        'out.bmp', 'out.png', 'test_results.json', 'test_report.xlsx'
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed {file}")

def run_full_test():
    print("=== Image Processor Comprehensive Test Suite ===")
    print("Using real BMP and PNG images from input_photos/")
    
    print("0. Cleaning up previous test files (keeping output_photos)...")
    cleanup()
    
    if not os.path.exists("input_photos"):
        print("ERROR: input_photos directory not found!")
        return False
    
    bmp_count = len([f for f in os.listdir('input_photos') if f.endswith('.bmp') and f[:-4].isdigit()])
    png_count = len([f for f in os.listdir('input_photos') if f.endswith('.png') and f[:-4].isdigit()])
    
    print(f"Found {bmp_count} BMP images and {png_count} PNG images in input_photos/")
    
    if bmp_count + png_count == 0:
        print("ERROR: No test images found in input_photos/!")
        return False
    
    os.makedirs("output_photos", exist_ok=True)
    
    print("1. Running test suite with real images...")
    result = subprocess.run([sys.executable, "test_suite.py"])
    if result.returncode != 0:
        print("WARNING: Some tests failed")
    
    print("2. Generating Excel report...")
    result = subprocess.run([sys.executable, "generate_excel_report.py"])
    if result.returncode != 0:
        print("ERROR: Failed to generate report")
        return False
    
    print("3. Test completion!")
    print(f"Results saved in output_photos/ and test_report.xlsx")
    return True

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)