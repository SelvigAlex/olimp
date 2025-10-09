#!/usr/bin/env python3
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

def create_excel_report():
    """Create Excel report from test results"""
    
    # Load test results
    try:
        with open('test_results.json', 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("No test results found")
        return
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Results"
    
    # Headers
    headers = ['Test Name', 'Command', 'Status', 'Expected', 'Actual', 'Timestamp']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    
    # Data
    for row, result in enumerate(results, 2):
        ws.cell(row=row, column=1, value=result['test'])
        ws.cell(row=row, column=2, value=result['command'])
        
        status_cell = ws.cell(row=row, column=3, value='PASS' if result['success'] else 'FAIL')
        status_cell.fill = PatternFill(
            start_color="00FF00" if result['success'] else "FF0000",
            end_color="00FF00" if result['success'] else "FF0000", 
            fill_type="solid"
        )
        
        ws.cell(row=row, column=4, value=result['expected'])
        ws.cell(row=row, column=5, value=str(result['actual'])[:100])  # Truncate long output
        ws.cell(row=row, column=6, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Summary
    summary_row = len(results) + 3
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    ws.cell(row=summary_row, column=1, value="SUMMARY").font = Font(bold=True)
    ws.cell(row=summary_row+1, column=1, value=f"Total Tests: {len(results)}")
    ws.cell(row=summary_row+2, column=1, value=f"Passed: {passed}")
    ws.cell(row=summary_row+3, column=1, value=f"Failed: {failed}")
    ws.cell(row=summary_row+4, column=1, value=f"Success Rate: {passed/len(results)*100:.1f}%")
    
    # Auto-adjust columns
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
    
    # Save
    wb.save('test_report.xlsx')
    print(f"Excel report generated: test_report.xlsx")
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} tests")

if __name__ == "__main__":
    create_excel_report()