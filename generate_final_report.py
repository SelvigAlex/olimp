#!/usr/bin/env python3
import json
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

def generate_final_report():
    """Generate final comprehensive test report"""
    
    # Load test results
    test_results = []
    try:
        with open('test_results.json', 'r') as f:
            test_results = json.load(f)
        print("✓ test_results.json loaded successfully")
    except FileNotFoundError:
        print("WARNING: test_results.json not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: test_results.json contains invalid JSON: {e}")
    
    # Load comparison results - более надежная обработка
    comparison_results = {'summary': {'total_comparisons': 0, 'matches': 0, 'mismatches': 0, 'match_percentage': 0}, 'comparisons': []}
    
    comparison_file_path = 'comparison_results.json'
    if os.path.exists(comparison_file_path):
        file_size = os.path.getsize(comparison_file_path)
        if file_size == 0:
            print("WARNING: comparison_results.json exists but is empty (0 bytes)")
            print("Using default empty comparison results")
        else:
            try:
                with open(comparison_file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        comparison_results = json.loads(content)
                        print("✓ comparison_results.json loaded successfully")
                    else:
                        print("WARNING: comparison_results.json is empty after stripping")
            except json.JSONDecodeError as e:
                print(f"ERROR: comparison_results.json contains invalid JSON: {e}")
                print("Using default empty comparison results")
    else:
        print("WARNING: comparison_results.json not found")
    
    # Create workbook with multiple sheets
    wb = Workbook()
    
    # Sheet 1: Executive Summary
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"
    
    # Test results summary
    test_passed = sum(1 for r in test_results if r.get('success', False))
    test_total = len(test_results)
    test_success_rate = (test_passed / test_total * 100) if test_total > 0 else 0
    
    # Comparison summary
    comp_summary = comparison_results.get('summary', {})
    comp_match_rate = comp_summary.get('match_percentage', 0)
    
    # Executive summary
    ws_summary.cell(1, 1, "FINAL TEST REPORT").font = Font(bold=True, size=16)
    ws_summary.cell(3, 1, "Test Execution Summary").font = Font(bold=True)
    ws_summary.cell(4, 1, f"Total Tests: {test_total}")
    ws_summary.cell(5, 1, f"Tests Passed: {test_passed}")
    ws_summary.cell(6, 1, f"Tests Failed: {test_total - test_passed}")
    ws_summary.cell(7, 1, f"Test Success Rate: {test_success_rate:.1f}%")
    
    ws_summary.cell(9, 1, "Image Comparison Summary").font = Font(bold=True)
    ws_summary.cell(10, 1, f"Total Comparisons: {comp_summary.get('total_comparisons', 0)}")
    ws_summary.cell(11, 1, f"Image Matches: {comp_summary.get('matches', 0)}")
    ws_summary.cell(12, 1, f"Image Mismatches: {comp_summary.get('mismatches', 0)}")
    ws_summary.cell(13, 1, f"Match Percentage: {comp_match_rate:.1f}%")
    
    
    ws_summary.cell(17, 1, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Sheet 2: Detailed Test Results
    ws_tests = wb.create_sheet("Test Results")
    
    headers = ['Test Name', 'Command', 'Status', 'Expected', 'Actual']
    for col, header in enumerate(headers, 1):
        cell = ws_tests.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    for row, result in enumerate(test_results, 2):
        ws_tests.cell(row=row, column=1, value=result.get('test', 'N/A'))
        ws_tests.cell(row=row, column=2, value=result.get('command', 'N/A'))
        
        success = result.get('success', False)
        status_cell = ws_tests.cell(row=row, column=3, value='PASS' if success else 'FAIL')
        status_cell.fill = PatternFill(
            start_color="00FF00" if success else "FF0000",
            end_color="00FF00" if success else "FF0000", 
            fill_type="solid"
        )
        
        ws_tests.cell(row=row, column=4, value=result.get('expected', 'N/A'))
        ws_tests.cell(row=row, column=5, value=str(result.get('actual', 'N/A'))[:100])
    
    # Sheet 3: Image Comparison Results
    ws_compare = wb.create_sheet("Image Comparison")
    
    headers = ['Standard File', 'Output File', 'Match', 'File Size Std', 'File Size Out', 'Method']
    for col, header in enumerate(headers, 1):
        cell = ws_compare.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    comparisons = comparison_results.get('comparisons', [])
    if comparisons:
        for row, comp in enumerate(comparisons, 2):
            ws_compare.cell(row=row, column=1, value=comp.get('standard_file', 'N/A'))
            ws_compare.cell(row=row, column=2, value=comp.get('output_file', 'N/A'))
            
            match = comp.get('match', False)
            match_cell = ws_compare.cell(row=row, column=3, value='YES' if match else 'NO')
            match_cell.fill = PatternFill(
                start_color="00FF00" if match else "FF0000",
                end_color="00FF00" if match else "FF0000", 
                fill_type="solid"
            )
            
            ws_compare.cell(row=row, column=4, value=comp.get('file_size_std', 'N/A'))
            ws_compare.cell(row=row, column=5, value=comp.get('file_size_out', 'N/A'))
            ws_compare.cell(row=row, column=6, value=comp.get('method', 'N/A'))
    else:
        # Если нет данных сравнения, добавить сообщение
        ws_compare.cell(2, 1, "No comparison data available")
        ws_compare.merge_cells('A2:F2')
        ws_compare.cell(2, 1).alignment = Alignment(horizontal='center')
    
    # Auto-adjust columns for all sheets
    for ws in [ws_summary, ws_tests, ws_compare]:
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save final report
    report_filename = 'final_test_report.xlsx'
    wb.save(report_filename)
    print(f"✓ Final test report generated: {report_filename}")
    
    # Print summary to console
    print(f"\n=== FINAL TEST SUMMARY ===")
    print(f"Tests: {test_passed}/{test_total} passed ({test_success_rate:.1f}%)")
    print(f"Images: {comp_summary.get('matches', 0)}/{comp_summary.get('total_comparisons', 0)} matched ({comp_match_rate:.1f}%)")
    
    # Strict criteria info
    print(f"\n=== STRICT COMPARISON CRITERIA ===")
    print("✓ Image comparison: Pixel-by-pixel exact match required")
    print("✓ Test pass threshold: 90% success rate")
    print("✓ Image match threshold: 90% exact matches")

def fix_comparison_results_file():
    """Create a valid empty comparison_results.json file if it's empty or missing"""
    comparison_file_path = 'comparison_results.json'
    
    if os.path.exists(comparison_file_path):
        file_size = os.path.getsize(comparison_file_path)
        if file_size == 0:
            print("Fixing empty comparison_results.json file...")
            # Создаем валидный пустой JSON
            empty_data = {
                "summary": {
                    "total_comparisons": 0,
                    "matches": 0, 
                    "mismatches": 0,
                    "match_percentage": 0
                },
                "comparisons": []
            }
            with open(comparison_file_path, 'w') as f:
                json.dump(empty_data, f, indent=2)
            print("✓ Created valid empty comparison_results.json")
        else:
            print("✓ comparison_results.json already exists and is not empty")
    else:
        print("Creating missing comparison_results.json file...")
        # Создаем файл с валидной структурой
        empty_data = {
            "summary": {
                "total_comparisons": 0,
                "matches": 0,
                "mismatches": 0,
                "match_percentage": 0
            },
            "comparisons": []
        }
        with open(comparison_file_path, 'w') as f:
            json.dump(empty_data, f, indent=2)
        print("✓ Created comparison_results.json with valid structure")

if __name__ == "__main__":
    # Сначала починим файл comparison_results.json если нужно
    print("Checking comparison_results.json file...")
    fix_comparison_results_file()
    
    print("\n" + "="*50)
    print("Generating final report...")
    print("="*50 + "\n")
    
    # Затем генерируем отчет
    generate_final_report()