# Import necessary modules for PDF generation
from flask import render_template, make_response
import pdfkit
from datetime import datetime

@admin_users_blueprint.route('/employee_history_pdf/<int:id>', methods=['GET'])
@admin_login_required
def employee_history_pdf(id):
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    report_type = request.args.get('report_type', 'overview')
    
    # Get employee data
    employee = Employee.query.get_or_404(id)
    
    # Get report data based on the report type
    report_data = []
    leave_balances = {}
    stats = {}
    
    if date_from and date_to:
        # Format dates for display
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        
        # Get report data
        if report_type == 'overview':
            # Get leave balances
            leave_balances = {
                'annual_leave': get_employee_leave_balance(employee.id, 'annual'),
                'sick_leave': get_employee_leave_balance(employee.id, 'sick'),
                'emergency_leave': get_employee_leave_balance(employee.id, 'emergency')
            }
            
            # Get attendance statistics
            stats = get_employee_attendance_stats(employee.id, date_from, date_to)
        else:
            # Get specific report data
            report_data = get_employee_report_data(employee.id, report_type, date_from, date_to)
    
    # Render the template to a string
    html = render_template(
        'emplooye_affairs_admin/employee_history_pdf.html',
        employee=employee,
        date_from=date_from,
        date_to=date_to,
        report_type=report_type,
        report_data=report_data,
        leave_balances=leave_balances,
        stats=stats,
        generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # Configure pdfkit options
    options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'margin-top': '1cm',
        'margin-right': '1cm',
        'margin-bottom': '1cm',
        'margin-left': '1cm',
        'orientation': 'portrait',
        'no-outline': None,
        'enable-local-file-access': None,
        'disable-smart-shrinking': None
    }
    
    # Create PDF from HTML
    pdf = pdfkit.from_string(html, False, options=options)
    
    # Create response
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=employee_history_{employee.id}_{date_from}_{date_to}.pdf'
    
    return response

# Helper function to get employee leave balance
def get_employee_leave_balance(employee_id, leave_type):
    # This function should get the current leave balance for the employee
    # Replace with actual implementation
    if leave_type == 'annual':
        return 21
    elif leave_type == 'sick':
        return 15
    elif leave_type == 'emergency':
        return 7
    return 0

# Helper function to get employee attendance statistics
def get_employee_attendance_stats(employee_id, date_from, date_to):
    # This function should calculate attendance statistics for the date range
    # Replace with actual implementation
    return {
        'period_days': 30,
        'working_days': 22,
        'attendance_days': 20,
        'absent_days': 2,
        'leave_days': 1,
        'mission_days': 1,
        'delays_count': 3,
        'permission_count': 2
    }

# Helper function to get employee report data
def get_employee_report_data(employee_id, report_type, date_from, date_to):
    # This function should get the specific report data based on the report type
    # Replace with actual implementation
    if report_type == 'check_in_delays':
        return [
            {'date': '2023-05-10', 'check_in_time': '08:15', 'delay_duration': '15 دقيقة', 'notes': 'ازدحام مروري'},
            {'date': '2023-05-15', 'check_in_time': '08:30', 'delay_duration': '30 دقيقة', 'notes': 'ظروف شخصية'}
        ]
    elif report_type == 'momrya':
        return [
            {'start_date': '2023-05-20', 'end_date': '2023-05-22', 'destination': 'القاهرة', 'notes': 'اجتماع إداري'}
        ]
    elif report_type == 'ezn':
        return [
            {'date': '2023-05-12', 'start_time': '11:00', 'end_time': '12:00', 'duration': '1 ساعة', 'reason': 'مراجعة طبية'}
        ]
    elif report_type == 'agaza':
        return [
            {'leave_type': 'سنوية', 'start_date': '2023-05-25', 'end_date': '2023-05-27', 'days': 3, 'reason': 'ظروف عائلية', 'status': 'مقبولة'}
        ]
    elif report_type == 'clinic':
        return [
            {'date': '2023-05-18', 'entry_time': '10:30', 'exit_time': '11:00', 'reason': 'صداع', 'notes': 'تم صرف الدواء'}
        ]
    elif report_type == 'altmas':
        return [
            {'date': '2023-05-05', 'request_type': 'طلب مساعدة مالية', 'details': 'تكاليف علاج', 'status': 'قيد المراجعة'}
        ]
    elif report_type == 'absent':
        return [
            {'date': '2023-05-08', 'day_name': 'الإثنين', 'status': 'غياب بدون إذن', 'notes': 'تم إرسال إنذار'}
        ]
    return [] 