import locale
from flask import  flash
import pandas as pd
from app.extensions import db
from app.models import  Agaza, Altmas, Approvals, Clinic, Deduction, Employee, Attendance, EmployeeRates, Ezn, JobScheduleOverride, Momrya, OfficialHoliday, User
from sqlalchemy import case, func , String, or_
from datetime import datetime ,timedelta
from sqlalchemy import and_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
from sqlalchemy import and_
from datetime import datetime, timedelta

def is_agaza_approved(employee_id, date):
    """
    Check if there is an approved agaza for the given employee ID within the date range.

    Args:
        employee_id (int): The ID of the employee.
        date (datetime.date): The date to check.

    Returns:
        bool: True if there is an approved agaza, False otherwise.
    """
    agaza = Agaza.query.filter(
        Agaza.employee_id == employee_id,
        Agaza.approval_status == "Approved",
        Agaza.from_date <= date,
        Agaza.to_date >= date
    ).first()

    return bool(agaza)


def parse_time_str(time_str):
    """Convert a time string (format 'HH:MM:SS' or 'HH:MM:SS.ssssss') to a datetime.time object."""
    if time_str:
        try:
            return datetime.strptime(time_str, '%H:%M:%S.%f').time()
        except ValueError:
            return datetime.strptime(time_str, '%H:%M:%S').time()
    return None

from datetime import datetime, timedelta
from sqlalchemy.orm import aliased
from sqlalchemy import func, and_, or_

def handle_attendance_reports(
    report_type, 
    report_date=None, 
    period=None, 
    id=None, 
    date_from=None, 
    date_to=None, 
    include_delay_minutes=False, 
    include_leave_early_time=False,
    employee_office_name=None
):
    status_translations = {
        'Pending': 'قيد الموافقة',
        'Approved': 'تمت الموافقة',
        'Rejected': 'تم رفض الطلب'
    }

    today_date = datetime.today().date()
    formatted_date = format_date_to_arabic(today_date)
    arabic_day_name = formatted_date.split(',')[0]

    query = build_base_query()
    query = apply_filters(query, id, employee_office_name, date_from, date_to, report_date, period)
    report_data = query.order_by(Employee.office_name).all()

    final_report_data = []
    total_delay_minutes = 0
    total_leave_early_minutes = 0

    if report_type == 'no_check_out':
        final_report_data = handle_no_check_out_report(id, employee_office_name, date_from, date_to, report_date, period)
    elif report_type == 'rest':
        final_report_data = handle_rest_report(date_from, date_to, report_date, id, employee_office_name, period)
    elif report_type == 'rased':
        final_report_data = handle_rased_report(id, employee_office_name)
    elif report_type in ['agaza', 'agaza_only', 'fr2a', 'entdab', 'no_salary']:
        final_report_data = handle_agaza_reports(report_type, id, employee_office_name, date_from, date_to, report_date, period, status_translations)
    elif report_type == 'altmas':
        final_report_data = handle_altmas_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
    elif report_type == 'ezn':
        final_report_data = handle_ezn_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
    elif report_type == 'clinic':
        final_report_data = handle_clinic_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
    elif report_type == 'momrya':
        final_report_data = handle_momrya_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
    else:
        final_report_data = handle_attendance_reports_default(report_data, report_type, include_delay_minutes, include_leave_early_time)

    if not final_report_data:
        return []

    if include_delay_minutes and report_type == 'check_in_delays':
        final_report_data.append(calculate_total_delay(total_delay_minutes))
    elif include_leave_early_time and report_type == 'check_out_ahead':
        final_report_data.append(calculate_total_leave_early(total_leave_early_minutes))

    return final_report_data

def build_base_query():
    return db.session.query(
        Employee.id,
        Employee.name, 
        Employee.office_name, 
        func.cast(Attendance.check_in_time, String).label('check_in_time'),
        func.cast(Attendance.check_out_time, String).label('check_out_time'),
        func.cast(Attendance.date, String).label('att_date'),
        func.cast(JobScheduleOverride.job_start_time, String).label('override_job_start_time'),
        func.cast(JobScheduleOverride.job_end_time, String).label('override_job_end_time'),
        func.cast(Employee.job_start_time, String).label('job_start_time'),
        func.cast(Employee.job_end_time, String).label('job_end_time'),
        func.date(JobScheduleOverride.date).label('override_date'),
        Employee.sat,
        Employee.sun,
        Employee.mon,
        Employee.tues,
        Employee.wed,
        Employee.thr,
        Employee.fri
    ).join(Attendance).outerjoin(
        JobScheduleOverride,
        (Employee.id == JobScheduleOverride.employee_id) &
        (func.date(Attendance.date) == func.date(JobScheduleOverride.date))
    ).filter(
        Employee.active == 'ظهور'
    ).distinct()

def apply_filters(query, id, employee_office_name, date_from, date_to, report_date, period):
    if id:
        query = query.filter(Employee.id == id)
    if employee_office_name:
        query = query.filter(Employee.office_name == employee_office_name)
    if date_from and date_to:
        query = query.filter(Attendance.date.between(date_from, date_to))
    elif report_date:
        query = query.filter(Attendance.date == report_date)
    if period:
        query = query.filter(Employee.period == period)
    return query

def handle_no_check_out_report(id, employee_office_name, date_from, date_to, report_date, period):
    no_check_out_query = db.session.query(
        Employee.name, 
        Employee.office_name,
        Attendance.date
    ).join(
        Attendance,
        Employee.id == Attendance.employee_id   
    ).filter(
        Attendance.check_out_time.is_(None),
        Attendance.check_in_time.isnot(None),
        Employee.active == 'ظهور'
    )

    if id:
        no_check_out_query = no_check_out_query.filter(Employee.id == id)
    if employee_office_name:
        no_check_out_query = no_check_out_query.filter(Employee.office_name == employee_office_name)
    if date_from and date_to:
        no_check_out_query = no_check_out_query.filter(Attendance.date.between(date_from, date_to))
    elif report_date:
        no_check_out_query = no_check_out_query.filter(Attendance.date == report_date)    
    if period:
        no_check_out_query = no_check_out_query.filter(Employee.period == period)

    no_check_out_data = no_check_out_query.distinct().all()
    final_report_data = []

    for employee in no_check_out_data:
        final_report_data.append({
            'arabic_day': format_date_to_arabic(employee.date).split(',')[0],
            'Employee Name': employee.name,
            'Office': employee.office_name,
            'Message': 'لم يقم بتسجيل انصرافه',
            'date': employee.date,
        })
    return final_report_data

def handle_rest_report(date_from, date_to, report_date, id, employee_office_name, period):
    final_report_data = []
    if date_from and date_to:
        start_date = date_from
        end_date = date_to
        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            days_map = {0: 'mon', 1: 'tues', 2: 'wed', 3: 'thr', 4: 'fri', 5: 'sat', 6: 'sun'}
            day_column = days_map.get(day_of_week)
            if day_column:
                rest_query = db.session.query(
                    Employee.name, 
                    Employee.office_name, 
                    Employee.period
                ).filter(
                    getattr(Employee, day_column) == False,
                    Employee.active == 'ظهور'
                )
                if employee_office_name:
                    rest_query = rest_query.filter(Employee.office_name == employee_office_name)
                if id:
                    rest_query = rest_query.filter(Employee.id == id)
                if period:
                    rest_query = rest_query.filter(Employee.period == period)
                rest_data = rest_query.distinct().all()
                for employee in rest_data:
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(current_date).split(',')[0],
                        'Employee Name': employee.name,
                        'Office': employee.office_name,
                        'Rest Day': f"  اليوم {format_date_to_arabic(current_date)} ، وهو يوم راحة لهذا الموظف. ",
                        'date': current_date.strftime('%Y-%m-%d'),
                    })
            current_date += timedelta(days=1)
    elif report_date:
        day_of_week = datetime.strptime(str(report_date), '%Y-%m-%d').weekday()
        days_map = {0: 'mon', 1: 'tues', 2: 'wed', 3: 'thr', 4: 'fri', 5: 'sat', 6: 'sun'}
        day_column = days_map.get(day_of_week)
        formatted_date = datetime.strptime(str(report_date), '%Y-%m-%d')
        if day_column:
            rest_query = db.session.query(
                Employee.name, 
                Employee.office_name, 
                Employee.period
            ).filter(
                getattr(Employee, day_column) == False,
                Employee.active == 'ظهور'
            )
            if employee_office_name:
                rest_query = rest_query.filter(Employee.office_name == employee_office_name)
            if id:
                rest_query = rest_query.filter(Employee.id == id)
            if period:
                rest_query = rest_query.filter(Employee.period == period)
            rest_data = rest_query.distinct().all()
            for employee in rest_data:
                final_report_data.append({
                    'arabic_day': format_date_to_arabic(formatted_date).split(',')[0],
                    'Employee Name': employee.name,
                    'Office': employee.office_name,
                    'Rest Day': f"  اليوم {format_date_to_arabic(formatted_date)} ، وهو يوم راحة لهذا الموظف. ",
                    'date': formatted_date.strftime('%Y-%m-%d'),
                })
    return final_report_data

def handle_rased_report(id, employee_office_name):
    final_report_data = []
    if id:
        rased_query = db.session.query(
            Employee.name, 
            Employee.office_name, 
            Employee.arda_points, 
            Employee.sanwya_points, 
            Employee.tar7eel_points
        ).filter(Employee.id == id)
        if employee_office_name:
            rased_query = rased_query.filter(Employee.office_name == employee_office_name)
        rased_data = rased_query.first()
        if rased_data:
            final_report_data.append({
                'Employee Name': rased_data.name,
                'Office': rased_data.office_name,
                'رصيد العارضة': rased_data.arda_points,
                'رصيد الاعتيادية': rased_data.sanwya_points,
                'الرصيد المرحل': rased_data.tar7eel_points
            })
    return final_report_data

def handle_agaza_reports(report_type, id, employee_office_name, date_from, date_to, report_date, period, status_translations):
    main_employee = aliased(Employee)
    alternative_employee = aliased(Employee)
    query = db.session.query(
        Agaza.id,
        Agaza.from_date,
        Agaza.to_date,
        Agaza.submit_date,
        Agaza.type,
        Agaza.approval_status,
        Agaza.notes_agaza,
        Agaza.notes_agaza_manager,
        Agaza.deducat,
        main_employee.name.label('employee_name'),
        main_employee.office_name.label('employee_office_name'),
        alternative_employee.name.label('alternative_employee_name'),
        main_employee.period.label('period'),
    ).join(
        main_employee, main_employee.id == Agaza.employee_id
    ).outerjoin(
        alternative_employee, alternative_employee.id == Agaza.alternative
    )
    if report_type == 'agaza':
        query = query.filter(
            Agaza.approval_status == 'Approved',
            main_employee.active == 'ظهور'
        )
    if report_type == 'agaza_only':
        query = query.filter(
            Agaza.approval_status == 'Approved',
            main_employee.active == 'ظهور',
            ~Agaza.type.in_(['انتداب', 'فرقة', 'بدون مرتب'])
        )
    if report_type == 'fr2a':
        query = query.filter(
            Agaza.approval_status == 'Approved',
            main_employee.active == 'ظهور',
            Agaza.type == 'فرقة',
        )
    if report_type == 'entdab':
        query = query.filter(
            Agaza.approval_status == 'Approved',
            main_employee.active == 'ظهور',
            Agaza.type == 'انتداب',
        )
    if report_type == 'no_salary':
        query = query.filter(
            Agaza.approval_status == 'Approved',
            main_employee.active == 'ظهور',
            Agaza.type == 'بدون مرتب',
        )
    if id:
        query = query.filter(Agaza.employee_id == id)
    if employee_office_name:
        query = query.filter(main_employee.office_name == employee_office_name)
    if date_from and date_to:
        query = query.filter(
            or_(
                and_(Agaza.from_date <= date_to, Agaza.to_date >= date_from),
                and_(Agaza.from_date.between(date_from, date_to), Agaza.to_date.between(date_from, date_to))
            )
        )
    elif report_date:
        query = query.filter(Agaza.from_date <= report_date, Agaza.to_date >= report_date)
    if period:
        query = query.filter(main_employee.period == period)
    agaza_data = query.all()
    final_report_data = []
    for request_item in agaza_data:
        approval_status = request_item.approval_status if request_item.approval_status else 'لم تسجل بعد'
        translated_status = status_translations.get(approval_status, 'لم تسجل بعد')
        final_report_data.append({
            'Employee Name': request_item.employee_name if request_item.employee_name else 'لم تسجل بعد',
            'Office': request_item.employee_office_name if request_item.employee_office_name else 'لم تسجل بعد',
            'From Date': request_item.from_date.strftime('%Y-%m-%d') if request_item.from_date else 'لم تسجل بعد',
            'To Date': request_item.to_date.strftime('%Y-%m-%d') if request_item.to_date else 'لم تسجل بعد',
            'Type': request_item.type if request_item.type else 'لم تسجل بعد',
            'Alternative': request_item.alternative_employee_name if request_item.alternative_employee_name else 'لايوجد بديل',
            'notes_agaza': request_item.notes_agaza if request_item.notes_agaza else 'لم تسجل بعد',
            'notes_agaza_manager': request_item.notes_agaza_manager if request_item.notes_agaza_manager else 'لم تسجل بعد',
            'Approval Status': translated_status,
            'deducat': request_item.deducat if request_item.deducat else 'لم تسجل بعد',
            'Submit Date': request_item.submit_date.strftime('%Y-%m-%d') if request_item.submit_date else 'لم تسجل بعد',
        })
    return final_report_data

def handle_altmas_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations):
    main_employee = aliased(Employee)
    query = db.session.query(
        Altmas.id,
        main_employee.name.label('employee_name'),
        main_employee.office_name.label('employee_office_name'),
        main_employee.period.label('period'),
        Altmas.petition,
        Altmas.approval_status,
        Altmas.submit_date
    ).join(
        main_employee, main_employee.id == Altmas.employee_id
    ).filter(
        main_employee.active == 'ظهور'
    )
    if id:
        query = query.filter(Altmas.employee_id == id)
    if employee_office_name:
        query = query.filter(main_employee.office_name == employee_office_name)
    if date_from and date_to:
        query = query.filter(Altmas.submit_date.between(date_from, date_to))
    elif report_date:
        query = query.filter(Altmas.submit_date == report_date)
    if period:
        query = query.filter(main_employee.period == period)
    altmas_data = query.all()
    final_report_data = []
    for request_item in altmas_data:
        approval_status = request_item.approval_status if request_item.approval_status else 'لم تسجل بعد'
        translated_status = status_translations.get(approval_status, 'لم تسجل بعد')
        final_report_data.append({
            'arabic_day': format_date_to_arabic(request_item.submit_date).split(',')[0],
            'Submit Date': request_item.submit_date.strftime('%Y-%m-%d') if request_item.submit_date else 'لم تسجل بعد',
            'Employee Name': request_item.employee_name if request_item.employee_name else 'لم تسجل بعد',
            'Office': request_item.employee_office_name if request_item.employee_office_name else 'لم تسجل بعد',
            'Petition': request_item.petition if request_item.petition else 'لم تسجل بعد',
            'Approval Status': translated_status,
        })
    return final_report_data

def handle_ezn_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations):
    main_employee = aliased(Employee)
    query = db.session.query(
        Ezn.id,
        main_employee.name.label('employee_name'),
        main_employee.office_name.label('employee_office_name'),
        main_employee.period.label('period'),
        Ezn.from_time,
        Ezn.to_time,
        Ezn.submit_date,
        Ezn.approval_status,
        Ezn.out_time,
        Ezn.back_time
    ).join(
        main_employee, main_employee.id == Ezn.employee_id
    ).filter(
        main_employee.active == 'ظهور'
    )
    if id:
        query = query.filter(Ezn.employee_id == id)
    if employee_office_name:
        query = query.filter(main_employee.office_name == employee_office_name)
    if date_from and date_to:
               query = query.filter(Ezn.submit_date.between(date_from, date_to))
    elif report_date:
        query = query.filter(Ezn.submit_date == report_date)
    if period:
        query = query.filter(main_employee.period == period)
    ezn_data = query.all()
    final_report_data = []
    for request_item in ezn_data:
        approval_status = request_item.approval_status if request_item.approval_status else 'لم تسجل بعد'
        translated_status = status_translations.get(approval_status, 'لم تسجل بعد')
        final_report_data.append({
            'arabic_day': format_date_to_arabic(request_item.submit_date).split(',')[0],
            'Submit Date': request_item.submit_date.strftime('%Y-%m-%d') if request_item.submit_date else 'لم تسجل بعد',
            'Employee Name': request_item.employee_name if request_item.employee_name else 'لم تسجل بعد',
            'Office': request_item.employee_office_name if request_item.employee_office_name else 'لم تسجل بعد',
            'From Time': f"سعت {format_time_to_arabic(request_item.from_time)}" if request_item.from_time else 'لم تسجل بعد',
            'To Time': f"سعت {format_time_to_arabic(request_item.to_time)}" if request_item.to_time else 'لم تسجل بعد',
            'Approval Status': translated_status,
            'Out Time': format_time_to_arabic(request_item.out_time) if request_item.out_time else 'لم تسجل بعد',
            'Back Time': format_time_to_arabic(request_item.back_time) if request_item.back_time else 'لم تسجل بعد',
        })
    return final_report_data

def handle_clinic_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations):
    main_employee = aliased(Employee)
    query = db.session.query(
        Clinic.id,
        main_employee.name.label('employee_name'),
        main_employee.office_name.label('employee_office_name'),
        main_employee.period.label('period'),
        Clinic.clinic_type,
        Clinic.date,
        Clinic.out_time,
        Clinic.back_time,
        Clinic.diagnosis,
        Clinic.submit_date,
        Clinic.approval_status
    ).join(
        main_employee, main_employee.id == Clinic.employee_id
    ).filter(
        main_employee.active == 'ظهور'
    )
    if id:
        query = query.filter(Clinic.employee_id == id)
    if employee_office_name:
        query = query.filter(main_employee.office_name == employee_office_name)
    if date_from and date_to:
        query = query.filter(Clinic.date.between(date_from, date_to))
    elif report_date:
        query = query.filter(Clinic.date == report_date)
    if period:
        query = query.filter(main_employee.period == period)
    clinic_data = query.all()
    final_report_data = []
    for request_item in clinic_data:
        approval_status = request_item.approval_status if request_item.approval_status else 'لم تسجل بعد'
        translated_status = status_translations.get(approval_status, 'لم تسجل بعد')
        final_report_data.append({
            'arabic_day': format_date_to_arabic(request_item.submit_date).split(',')[0],
            'Submit Date': request_item.submit_date.strftime('%Y-%m-%d') if request_item.submit_date else 'لم تسجل بعد',
            'Employee Name': request_item.employee_name if request_item.employee_name else 'لم تسجل بعد',
            'Office': request_item.employee_office_name if request_item.employee_office_name else 'لم تسجل بعد',
            'Clinic Type': f"عيادة {request_item.clinic_type}" if request_item.clinic_type else 'لم تسجل بعد',
            'تاريخ العيادة': request_item.date.strftime('%Y-%m-%d') if request_item.date else 'لم تسجل بعد',
            'Out Time': f"سعت {format_time_to_arabic(request_item.out_time)}" if request_item.out_time else 'لم تسجل بعد',
            'Back Time': f"سعت {format_time_to_arabic(request_item.back_time)}" if request_item.back_time else 'لم تسجل بعد',
            'Diagnosis': request_item.diagnosis if request_item.diagnosis else 'لم تسجل بعد',
            'Approval Status': translated_status,
        })
    return final_report_data

def handle_momrya_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations):
    main_employee = aliased(Employee)
    query = db.session.query(
        Momrya.id,
        main_employee.name.label('employee_name'),
        main_employee.office_name.label('employee_office_name'),
        main_employee.period.label('period'),
        Momrya.date,
        Momrya.to_date,
        Momrya.out_time,
        Momrya.back_time,
        Momrya.reason,
        Momrya.submit_date,
        Momrya.approval_status,
        Momrya.from_time
    ).join(
        main_employee, main_employee.id == Momrya.employee_id
    ).filter(
        main_employee.active == 'ظهور'
    )
    if id:
        query = query.filter(Momrya.employee_id == id)
    if employee_office_name:
        query = query.filter(main_employee.office_name == employee_office_name)
    if date_from and date_to:
        query = query.filter(Momrya.date.between(date_from, date_to))
    elif report_date:
        query = query.filter(Momrya.date == report_date)
    if period:
        query = query.filter(main_employee.period == period)
    momrya_data = query.all()
    final_report_data = []
    for request_item in momrya_data:
        approval_status = request_item.approval_status if request_item.approval_status else 'لم تسجل بعد'
        translated_status = status_translations.get(approval_status, 'لم تسجل بعد')
        final_report_data.append({
            'Arabic Day': format_date_to_arabic(request_item.submit_date).split(',')[0],
            'Submit Date': request_item.submit_date.strftime('%Y-%m-%d') if request_item.submit_date else 'لم تسجل بعد',
            'Employee Name': request_item.employee_name if request_item.employee_name else 'لم تسجل بعد',
            'Office': request_item.employee_office_name if request_item.employee_office_name else 'لم تسجل بعد',
            'from_date': request_item.date.strftime('%Y-%m-%d') if request_item.date else 'لم تسجل بعد',
            'to_date': request_item.date.strftime('%Y-%m-%d') if request_item.date else 'لم تسجل بعد',
            'Out Time': f"سعت {format_time_to_arabic(request_item.out_time)}" if request_item.out_time else 'لم تسجل بعد',
            'Back Time': f"سعت {format_time_to_arabic(request_item.back_time)}" if request_item.back_time else 'لم تسجل بعد',
            'From Time': f"سعت {format_time_to_arabic(request_item.from_time)}" if request_item.from_time else 'لم تسجل بعد',
            'Reason': request_item.reason if request_item.reason else 'لم تسجل بعد',
            'Approval Status': translated_status,
        })
    return final_report_data

def handle_attendance_reports_default(report_data, report_type, include_delay_minutes, include_leave_early_time):
    final_report_data = []
    seen_employees = set()
    total_delay_minutes = 0
    total_leave_early_minutes = 0

    for row in report_data:
        employee_key = (row.id, row.check_in_time, row.check_out_time, row.att_date)
        if employee_key in seen_employees:
            continue
        if is_agaza_approved(row.id, row.att_date):
            continue
        seen_employees.add(employee_key)

        job_start_time = parse_time_str(row.override_job_start_time) if row.override_job_start_time else parse_time_str(row.job_start_time)
        job_end_time = parse_time_str(row.override_job_end_time) if row.override_job_end_time else parse_time_str(row.job_end_time)

        if report_type == 'check_in_attendance':
            if row.check_in_time:
                check_in_time = parse_time_str(row.check_in_time)
                if check_in_time:
                    today_date = datetime.today().date()
                    check_in_datetime = datetime.combine(today_date, check_in_time)
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                        'date': row.att_date,
                        'Employee Name': row.name,
                        'Office': row.office_name,
                        'check_in_time': parse_time_str(row.job_start_time).strftime('%H:%M:%S'),
                        'Time': check_in_datetime.strftime('%H:%M:%S'),
                    })
                else:
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                        'date': row.att_date,
                        'Employee Name': row.name,
                        'Office': row.office_name,
                        'check_in_time': parse_time_str(row.job_start_time).strftime('%H:%M:%S'),
                        'Time': row.check_in_time,
                    })
            final_report_data = sorted(final_report_data, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))       
        elif report_type == 'check_all':
            if row.check_in_time or row.check_out_time:
                check_in_time = parse_time_str(row.check_in_time)
                check_out_time = parse_time_str(row.check_out_time)
                if check_in_time or check_out_time:
                    today_date = datetime.today().date()
                    check_in_datetime = datetime.combine(today_date, check_in_time) if check_in_time else None
                    check_out_datetime = datetime.combine(today_date, check_out_time) if check_out_time else None
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                        'date': row.att_date,
                        'Employee Name': row.name,
                        'Office': row.office_name,
                        'in': check_in_datetime.strftime('%H:%M:%S') if check_in_datetime else 'لايوجد',
                        'out': check_out_datetime.strftime('%H:%M:%S') if check_out_datetime else 'لايوجد',
                    })
                else:
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                        'date': row.att_date,
                        'Employee Name': row.name,
                        'Office': row.office_name,
                        'in': row.check_in_time if row.check_in_time else 'لايوجد',
                        'out': row.check_out_time if row.check_out_time else 'لايوجد',
                    })
        elif report_type == 'check_in_delays' and include_delay_minutes:
            if row.check_in_time and job_start_time:
                check_in_time = parse_time_str(row.check_in_time)
                if check_in_time and job_start_time:
                    today_date = datetime.today().date()
                    check_in_datetime = datetime.combine(today_date, check_in_time)
                    job_start_datetime = datetime.combine(today_date, job_start_time)
                    delay_seconds = (check_in_datetime - job_start_datetime).total_seconds()
                    hours, remainder = divmod(delay_seconds, 3600)
                    minutes = remainder // 60
                    if delay_seconds > 1:
                        total_delay_minutes += delay_seconds / 60
                        final_report_data.append({
                            'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                            'date': row.att_date,
                            'Employee Name': row.name,
                            'Office': row.office_name,
                            'check_in_time': parse_time_str(row.job_start_time).strftime('%H:%M:%S'),
                            'Time': check_in_datetime.strftime('%H:%M:%S'),
                            'Delay Time': f"{int(hours):02}:{int(minutes):02}:00",
                        })
        elif report_type == 'check_out_attendance':
            if row.check_out_time:
                check_out_time = parse_time_str(row.check_out_time)
                if check_out_time:
                    today_date = datetime.today().date()
                    check_out_datetime = datetime.combine(today_date, check_out_time)
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                        'date': row.att_date,
                        'Employee Name': row.name,
                        'Office': row.office_name,
                        'Time': check_out_datetime.strftime('%H:%M:%S'),
                    })
                else:
                    final_report_data.append({
                        'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                        'date': row.att_date,
                        'Employee Name': row.name,
                        'Office': row.office_name,
                        'Time': row.check_out_time,
                    })
        elif report_type == 'check_out_ahead' and include_leave_early_time:
            if row.check_out_time and job_end_time:
                check_out_time = parse_time_str(row.check_out_time)
                if check_out_time and job_end_time:
                    today_date = datetime.today().date()
                    check_out_datetime = datetime.combine(today_date, check_out_time)
                    job_end_datetime = datetime.combine(today_date, job_end_time)
                    ahead_seconds = (job_end_datetime - check_out_datetime).total_seconds()
                    hours, remainder = divmod(ahead_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if ahead_seconds > 0:
                        total_leave_early_minutes += ahead_seconds / 60
                        final_report_data.append({
                            'arabic_day': format_date_to_arabic(row.att_date).split(',')[0],
                            'date': row.att_date,
                            'Employee Name': row.name,
                            'Office': row.office_name,
                            'check_out_time': parse_time_str(row.job_end_time).strftime('%H:%M:%S'),
                            'Time': check_out_datetime.strftime('%H:%M:%S'),
                            'Leave Early Time': f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}",
                        })
    return final_report_data

def calculate_total_delay(total_delay_minutes):
    total_delay_seconds = total_delay_minutes * 60
    hours, remainder = divmod(total_delay_seconds, 3600)
    minutes = remainder // 60
    return {
        'arabic_day': '',
        'date': '',
        'Employee Name': '',
        'Office': '',
        'Time': '',
        'check_in_time': 'مجموع التاخيرات',
        'Delay Time': f"{int(hours):02}:{int(minutes):02}:00",
    }

def calculate_total_leave_early(total_leave_early_minutes):
    total_leave_early_seconds = total_leave_early_minutes * 60
    hours, remainder = divmod(total_leave_early_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {
        'arabic_day': '',
        'date': '',
        'Employee Name': '',
        'Office': '',
        'Time': '',
        'check_in_time': 'مجموع التاخيرات',
        'Delay Time': f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}:00",
    }

def handle_ezn_delay(
    report_date=None, 
    id=None, 
    date_from=None, 
    date_to=None, 
    period=None, 
    employee_office_name=None
):
    # Initialize the detailed report and total delay variables
    detailed_report = []
    total_delay_seconds = 0

    # Query the "ezn" table based on provided parameters
    query = db.session.query(Ezn).filter(Ezn.approval_status == 'Approved')

    if id:
        query = query.filter(Ezn.employee_id == id)
    if report_date:
        query = query.filter(Ezn.submit_date == report_date)
    elif date_from:
        query = query.filter(Ezn.submit_date >= date_from)
    if date_to:
        query = query.filter(Ezn.submit_date <= date_to)
    if period:
        query = query.filter(Ezn.period == period)
    if employee_office_name:
        # Filter employees by office name
        employees_with_office = Employee.query.filter_by(office_name=employee_office_name).all()
        employee_ids = [emp.id for emp in employees_with_office]
        query = query.filter(Ezn.employee_id.in_(employee_ids))

    # Fetch the results from the database
    ezn_records = query.all()

    for ezn in ezn_records:
        employee = Employee.query.get(ezn.employee_id)  # Get employee details
        if not employee:
            continue

        # Directly compare back_time and to_time since they are datetime.time objects
        if ezn.back_time and ezn.to_time:
            print(f"\nProcessing Employee: {employee.name}")
            print(f"Back Time: {ezn.back_time}, To Time: {ezn.to_time}")

            if ezn.back_time > ezn.to_time:
                print(f"Delay detected! Back Time > To Time")

                # Calculate delay
                delay_time = datetime.combine(datetime.min, ezn.back_time) - datetime.combine(datetime.min, ezn.to_time)
                total_delay_seconds += int(delay_time.total_seconds())

                print(f"Delay Time (HH:MM:SS): {str(delay_time)}")

                # Include in the detailed report only if there is a delay
                detailed_report.append({
                    'arabic_day':format_date_to_arabic(ezn.submit_date).split(',')[0],
                    'Submit Date': ezn.submit_date,# Format delay time as 'HH:MM:SS'
                    'Employee Name': employee.name,
                    'Office': employee.office_name,
                    'Out Time': ezn.out_time,
                    'Back Time': ezn.back_time,
                    'Delay Time': str(delay_time), 

                })
            else:
                print("No delay. Back Time is less than or equal to To Time.")

    # Add the total delay time as the last row if there are any delays
    if total_delay_seconds > 0:
        total_delay_minutes, remainder = divmod(total_delay_seconds, 60)
        total_delay_hours, total_delay_minutes = divmod(total_delay_minutes, 60)

        print(f"Total Delay Time (HH:MM:SS): {total_delay_hours:02}:{total_delay_minutes:02}:{remainder:02}")

        detailed_report.append({
            'Employee Name': 'مجموع التأخيرات',
            'Office': '',
            'Submit Date': '',
            'Out Time': '',
            'Back Time': '',
            'Delay Time': f"{int(total_delay_hours):02}:{int(total_delay_minutes):02}:{int(remainder):02}"
        })

    return detailed_report
def handle_deduction_report(
    report_date=None, 
    id=None, 
    date_from=None, 
    date_to=None, 
    period=None, 
    employee_office_name=None
):
    # Initialize the detailed report and total deduction variables
    detailed_report = []

    # Query the "deduction" table based on provided parameters
    query = db.session.query(Deduction).join(Employee).filter(Deduction.employee_id == Employee.id)

    if id:
        query = query.filter(Deduction.employee_id == id)
    if report_date:
        query = query.filter(Deduction.submit_date == report_date)
    elif date_from:
        query = query.filter(Deduction.submit_date >= date_from)
    if date_to:
        query = query.filter(Deduction.submit_date <= date_to)
    if period:
        query = query.join(Employee).filter(Employee.period == period)
    if employee_office_name:
        query = query.join(Employee).filter(Employee.office_name == employee_office_name)

    # Fetch the results from the database
    deductions = query.all()

    if id:
        # Calculate total deductions for the specific employee
        total_deductions = db.session.query(
            db.func.sum(Deduction.deduction_points).label('total_deductions')
        ).filter(Deduction.employee_id == id).scalar()
        
        # Add individual deductions to the report
        for deduction in deductions:
            employee = Employee.query.get(deduction.employee_id)  # Get employee details
            if not employee:
                continue
            
            detailed_report.append({
                'Employee Name': employee.name,
                'Office Name': employee.office_name,
                'Reason': deduction.reason,
                'Deduction Points': deduction.deduction_points
            })

        # Add total deductions to the report if it's a single employee report
        if total_deductions is not None:
            detailed_report.append({
                'Employee Name': "",
                'Office Name': "",
                'Reason': 'مجموع ايام الجزائات',
                'Deduction Points': total_deductions
            })

    else:
        # Regular report without total deductions
        for deduction in deductions:
            employee = Employee.query.get(deduction.employee_id)  # Get employee details
            if not employee:
                continue
            
            detailed_report.append({
                'Employee Name': employee.name,
                'Office Name': employee.office_name,
                'Reason': deduction.reason,
                'Deduction Points': deduction.deduction_points
            })


    return detailed_report

def get_absent_employees(specific_day=None, period=None, employee_id=None, date_from=None, date_to=None, office_name=None):
    """
    Function to retrieve absent employees based on the provided filters.

    Parameters:
        specific_day (date): A specific day to check for absence.
        period (str): The period to filter the absences (e.g., 'morning', 'evening').
        employee_id (int): The ID of a specific employee to check for absence.
        date_from (date): The start date of a range to check for absence.
        date_to (date): The end date of a range to check for absence.
        office_name (str): The name of the office to filter absences.

    Returns:
        List[dict]: A list of dictionaries containing details of absent employees.
    """

    # Convert strings to date objects if necessary
    if isinstance(specific_day, str):
        specific_day = datetime.strptime(specific_day, '%Y-%m-%d').date()
    if isinstance(date_from, str):
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
    if isinstance(date_to, str):
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    if specific_day:
        date_range = [specific_day]
    elif date_from and date_to:
        date_range = [date_from + timedelta(days=i) for i in range((date_to - date_from).days + 1)]
    else:
        date_range = [datetime.now().date()]

    absent_employees = []

    for day in date_range:
        #print(f"Checking day: {day}")  # Debugging #print

        # Check if the day is an official holiday
        holiday = OfficialHoliday.query.filter(and_(OfficialHoliday.from_date <= day, OfficialHoliday.to_date >= day)).first()
        #print('OfficialHoliday' ,holiday)
        if holiday:
            #print(f"Skipping {day} as it is a holiday.")  # Debugging #print
            continue

        # Filter employees based on the provided parameters
        query = Employee.query

        # Add filters for employee_id, office_name, and period if provided
        if employee_id:
            query = query.filter_by(id=employee_id)
        if office_name:
            query = query.filter_by(office_name=office_name)
        if period:
            query = query.filter_by(period=period)

        # Add filter for active employees with 'ظهور' status
        query = query.filter_by(active='ظهور')

        # Fetch and order the results
        employees = query.order_by(Employee.office_name).all()

        for employee in employees:
            # Skip the check if the day is a rest day for the employee
            rest_days = {
                'mon': employee.mon,
                'tues': employee.tues,
                'wed': employee.wed,
                'thr': employee.thr,
                'fri': employee.fri,
                'sat': employee.sat,
                'sun': employee.sun
            }
            day_of_week = day.strftime('%a').lower()  # Get the day of the week in abbreviated form
            day_column = {
                'mon': 'mon',
                'tue': 'tues',
                'wed': 'wed',
                'thu': 'thr',
                'fri': 'fri',
                'sat': 'sat',
                'sun': 'sun'
            }.get(day_of_week[:3], '')

            if not rest_days.get(day_column):
                #print(f"Skipping {employee.name} as it is their rest day.")  # Debugging #print
                continue

            # Check if the employee has approved leave (Agaza) on the day
            agaza = Agaza.query.filter(
                and_(
                    Agaza.employee_id == employee.id,
                    Agaza.from_date <= day,
                    Agaza.to_date >= day,
                    Agaza.approval_status == "Approved"
                )
            ).first()
            if agaza:
                #print(f"Skipping {employee.name} as they have approved leave.")  # Debugging #print
                continue

            # Check the attendance record
            attendance = Attendance.query.filter(
                and_(
                    Attendance.employee_id == employee.id,
                    Attendance.date == day,
                )
            ).first()

            if not attendance or attendance.check_in_time is None:
                absent_employees.append({
                    'arabic_day':format_date_to_arabic(day).split(',')[0],
                    'date': day.strftime('%Y-%m-%d'),
                    'اسم الموظف': employee.name,
                    'Office': employee.office_name,
                    'الحالة': 'غياب',
                })

    return absent_employees


def get_employee_info(employee_id):
    employee = Employee.query.get(employee_id)
    if employee:
        return employee.name, employee.office_name
    return None, None

def days_between_dates(date1_str, date2_str):
    # Define the format of the date strings
    date_format = "%Y-%m-%d"  # Example format: "2024-08-10"

    # Convert the date strings to datetime objects
    date1 = datetime.strptime(date1_str, date_format)
    date2 = datetime.strptime(date2_str, date_format)

    # Calculate the difference between the two dates
    delta = date2 - date1

    # Return the number of days between the two dates
    return abs(delta.days)
def generate_employee_query(employee_id):
    # Create a query string with the provided employee_id
    query = f"SELECT * FROM employees WHERE employee_id = '{employee_id}';"
    
    # Return the query string
    return query
def calculate_agaza_duration_this_year(employee_id, current_year, agaza_type=None, submit_date=None, after=None):
    # Get today's date
    today = datetime.today().date()

    # Determine if today's date is before or after July 1st
    july_first_current_year = datetime(current_year, 7, 1).date()

    if today >= july_first_current_year:
        # If today is on or after July 1st, use the current fiscal year (July 1st - June 30th of the next year)
        fiscal_year_start = july_first_current_year
        fiscal_year_end = datetime(current_year + 1, 6, 30).date()
    else:
        # If today is before July 1st, use the previous fiscal year (July 1st of the previous year - June 30th of this year)
        fiscal_year_start = datetime(current_year - 1, 7, 1).date()
        fiscal_year_end = datetime(current_year, 6, 30).date()

    # Build the query to get approved agaza records within the fiscal year
    query = Agaza.query.filter(
        Agaza.employee_id == employee_id,
        Agaza.approval_status == 'Approved',
        Agaza.submit_date.between(fiscal_year_start, fiscal_year_end)
    )

    # Handle 'عارضة' and 'عارضة طارئة' together
    if agaza_type in ['عارضة', 'عارضة طارئة']:
        query = query.filter(Agaza.type.in_(['عارضة', 'عارضة طارئة']))
    
    # Handle 'أعتيادية' independently
    elif agaza_type in ['أعتيادية' , 'اجازة بدل انصراف']:
        query = query.filter(Agaza.type.in_(['أعتيادية' , 'اجازة بدل انصراف']))
    
    # Filter by submit_date if provided
    if submit_date:
        query = query.filter(Agaza.submit_date < submit_date)
    
    # Filter by after date if provided
    if after:
        query = query.filter(Agaza.submit_date > after)

    # Execute the query to get the agaza records
    agaza_records = query.all()
    print('agaza_records' , agaza_records)
    # Initialize total duration
    total_duration = 0

    # Calculate the duration for each record
    for agaza in agaza_records:
        # Ensure the agaza dates are within the fiscal year
        print('agaza' , agaza)
        from_date = max(agaza.from_date, fiscal_year_start)
        to_date = min(agaza.to_date, fiscal_year_end)
        
        # Calculate the duration
        if from_date == to_date:
            duration = 1
        else:
            duration = days_between_dates(from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')) + 1
        
        # Add the duration to the total
        total_duration += duration

    return total_duration
def format_date_to_arabic(date_obj):
    # Dictionary to convert English month names to Arabic
    months_ar = {
        1: "يناير",
        2: "فبراير",
        3: "مارس",
        4: "أبريل",
        5: "مايو",
        6: "يونيو",
        7: "يوليو",
        8: "أغسطس",
        9: "سبتمبر",
        10: "أكتوبر",
        11: "نوفمبر",
        12: "ديسمبر"
    }

    # Dictionary to convert English weekday names to Arabic
    days_ar = {
        0: "الاثنين",
        1: "الثلاثاء",
        2: "الأربعاء",
        3: "الخميس",
        4: "الجمعة",
        5: "السبت",
        6: "الأحد"
    }

    # Dictionary to convert English numerals to Arabic numerals
    arabic_numerals = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣',
        '4': '٤', '5': '٥', '6': '٦', '7': '٧',
        '8': '٨', '9': '٩'
    }

    # Function to convert a number to Arabic numerals
    def convert_to_arabic_numerals(number):
        return ''.join(arabic_numerals[digit] for digit in str(number))

    # If the input is a string, convert it to a datetime object
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()  # Assuming format is 'YYYY-MM-DD'
        except ValueError:
            raise ValueError("Date string must be in 'YYYY-MM-DD' format")

    # Get the day, month, and year from the date object
    day = convert_to_arabic_numerals(date_obj.day)
    month = date_obj.month
    year = convert_to_arabic_numerals(date_obj.year)
    weekday = date_obj.weekday()

    # Convert to Arabic date format
    arabic_date = f"{days_ar[weekday]}, {day} {months_ar[month]} {year}"

    return arabic_date
def get_user_name_by_office(employee_office_name):
    try:
        # Query the User table for a user with the matching office
        user = User.query.filter_by(office=employee_office_name , user_type = "manager").first()
        
        # Check if a user was found and return their name
        if user:
            return user.name
        else:
            return "No user found for the specified office"

    except NoResultFound:
        return "No user found for the specified office" 
def format_time_to_arabic(time_obj):
    # Define Arabic numerals mapping
    arabic_numerals = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣',
        '4': '٤', '5': '٥', '6': '٦', '7': '٧',
        '8': '٨', '9': '٩'
    }
    
    # Convert time object to string in HH:MM format
    time_str = time_obj.strftime('%H:%M')
    
    # Extract hours and minutes from the time string
    hours, minutes = time_str.split(':')
    
    # Convert hours and minutes to Arabic numerals
    arabic_hours = ''.join(arabic_numerals[digit] for digit in hours)
    arabic_minutes = ''.join(arabic_numerals[digit] for digit in minutes)
    
    # Format the result
    result = f" {arabic_hours}{arabic_minutes}"
    
    return result
def convert_to_arabic_numerals(number):
    print('number' , number)
    arabic_numerals = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣',
        '4': '٤', '5': '٥', '6': '٦', '7': '٧',
        '8': '٨', '9': '٩'
    }

    # Convert the number to a string, then replace each digit with its Arabic counterpart
    arabic_number = ''.join(arabic_numerals[digit] for digit in str(number))
    
    return arabic_number
def get_user_office_and_type(user_id):
    try:
        # Query to get the office and user_type of the user by ID
        user_data = db.session.query(User.office, User.user_type).filter_by(id=user_id).first()
        
        # Check if the user data was found
        if user_data:
            # Return a dictionary with office and user_type
            return {
                "office": user_data.office,
                "user_type": user_data.user_type
            }
        else:
            return {
                "error": "No office or user type found for the given user ID."
            }
    
    except NoResultFound:
        return {
            "error": "User not found."
        }      
def generate_attendance_report(report_date, period=None , type_field=None):
    # Initialize an empty list to store the attendance report for all employees
    attendance_report = []

    # Initialize counters for the summary report
    total_employees = 0
    no_agaza_or_rest_count = 0
    rest_count = 0
    agaza_type_counts = {
        'أعتيادية': 0,
        'عارضة': 0,
        'عارضة طارئة': 0,
        'منحة': 0,
        'مرضي': 0,
        'بدون مرتب': 0,
        'بالخصم': 0,
        'وضع': 0,
        'فرقة': 0,
        'مأمورية': 0,
        'انتداب': 0,
        'حجز في المستشفي': 0
    }

    # Base query for employees with active status 'ظهور'
    query = Employee.query.filter_by(active='ظهور')

    # Apply filters based on the provided period and type_field
    if period:
        query = query.filter_by(period=period)

    if type_field:
        query = query.filter_by(emp_type=type_field)

    # Sort by office_name with custom ordering logic
    employees = query.order_by(
        case(
            (Employee.office_name == 'اجازة بدون مرتب', 1),  # First condition
            (Employee.office_name == 'انتداب خارج وزارة الدفاع', 2),  # Second condition
            else_=3  # All other offices
        ),
        Employee.office_name.asc()  # Sort all other offices alphabetically
    ).all()
    # Loop through each employee and check their status for the given date
    

    for employee in employees:
        total_employees += 1  # Count all employees

        employee_data = {
            'Employee Name': employee.name,
            'Office': employee.office_name,
            'Period': employee.period,
            'Leave Type': None,  # Will be filled if 'agaza' is found and approved
            'From Date': None,
            'To Date': None,
            'Has Rest': False,   # Will be True if 'rest' is found
        }

        # Check for leave (agaza)
        agaza_data = handle_attendance_reports(report_type='agaza', report_date=report_date, id=employee.id)
        has_agaza = False  # Flag to check if the employee has an approved leave

        if agaza_data and isinstance(agaza_data, list):
            # Iterate over the list to find the first approved leave
            for agaza_record in agaza_data:
                if agaza_record.get('Approval Status') == 'تمت الموافقة':
                    leave_type = agaza_record.get('Type', 'N/A')
                    employee_data['Leave Type'] = leave_type
                    employee_data['From Date'] = agaza_record.get('From Date', 'N/A')
                    employee_data['To Date'] = agaza_record.get('To Date', 'N/A')
                    has_agaza = True

                    # Update the leave type count
                    if leave_type in agaza_type_counts:
                        agaza_type_counts[leave_type] += 1

                    # Exit the loop after finding the first approved agaza
                    break

        # Check for rest
        rest_data = handle_attendance_reports(report_type='rest', report_date=report_date, id=employee.id)
        if rest_data:
            employee_data['Has Rest'] = True
            rest_count += 1  # Increment rest count

        # If the employee has neither an approved leave nor rest, increment the no_agaza_or_rest_count
        if not has_agaza and not employee_data['Has Rest']:
            no_agaza_or_rest_count += 1

        # Add the employee's data to the attendance report
        attendance_report.append(employee_data)

    # Prepare the summary report
    summary_report = {
        'Total Employees': total_employees,
        'Employees without Agaza or Rest': no_agaza_or_rest_count,
        'Rest Count': rest_count,
        'Agaza Type Counts': agaza_type_counts,
         'Percentage with Agaza or Rest': round(((total_employees - no_agaza_or_rest_count) / total_employees) * 100)
    }
    attendance_report = sort_attendance_report(attendance_report)
    # Return both the detailed attendance report and the summary report
    return attendance_report, summary_report
def sort_attendance_report(attendance_report):
    # Define the custom office order
    office_priority = {
        'اجازة بدون مرتب': 1,
        'انتداب خارج وزارة الدفاع': 2
    }

    # Sort the attendance report based on the office priority, and then alphabetically for other offices
    sorted_report = sorted(
        attendance_report, 
        key=lambda x: (office_priority.get(x['Office'], 3), x['Office'])
    )
    
    return sorted_report
def generate_mo2srat_report(from_date, to_date, office=None, employee_id=None , type =None):
    # Initialize empty lists for detailed and summary reports
    detailed_report = []
    summary_report = []

    # Query all employees with active status 'ظهور'
    employees = Employee.query.filter_by(active='ظهور').all()

    # Loop through each employee and check their status for the given date range
    for employee in employees:
        # Skip employees if specific employee_id or office filter is provided
        if employee_id and employee.id != employee_id:
            continue
        if office and employee.office_name != office:
            continue
        if type and employee.emp_type != type:
            continue
        # Initialize employee data for the detailed report
        employee_data = {
            'Employee Name': employee.name,
            'Office': employee.office_name,
            'Ezn': [],
            'Clinic': [],
            'Check-in Delays': [],
            'Agaza': [],
            'agaza_ded':[],
            'Deductions': [],
            'Ezn Delays': [],
            'absent': [],
        }
        
        
                # Fetch 'deduction' reports
        absent_data = get_absent_employees(
            specific_day=None,
            employee_id=employee.id,
            date_from=from_date,
            date_to=to_date,
        )
        if absent_data:
            employee_data['absent'] = absent_data  # Include deduction data
        print(employee_data['absent'] , "absent_data")
        # Fetch 'ezn' reports for the employee, only approved ones
        ezn_data = handle_attendance_reports(
            report_type='ezn',
            date_from=from_date,
            date_to=to_date,
            id=employee.id,
        )
        if ezn_data:
            approved_ezn_data = [record for record in ezn_data if record.get('Approval Status') == 'تمت الموافقة']
            employee_data['Ezn'] = approved_ezn_data  # Only include approved ezn data

        # Fetch 'clinic' reports for the employee, only approved ones
        clinic_data = handle_attendance_reports(
            report_type='clinic',
            date_from=from_date,
            date_to=to_date,
            id=employee.id,
        )
        if clinic_data:
            approved_clinic_data = [record for record in clinic_data if record.get('Approval Status') == 'تمت الموافقة']
            employee_data['Clinic'] = approved_clinic_data  # Only include approved clinic data

        # Fetch 'check_in_delays' reports, including delay minutes
        delay_data = handle_attendance_reports(
            report_type='check_in_delays',
            date_from=from_date,
            date_to=to_date,
            id=employee.id,
            include_delay_minutes=True
        )
        if delay_data:
            employee_data['Check-in Delays'] = delay_data  # Store the check-in delays data

        # Fetch 'agaza' reports, but only for 'عارضة طارئة' and 'مرضي', and only approved ones
        agaza_data = handle_attendance_reports(
            report_type='agaza',
            date_from=from_date,
            date_to=to_date,
            id=employee.id,
        )
        if agaza_data:
            # Filter by approved status and agaza types 'عارضة طارئة' and 'مرضي'
            approved_agaza_data = [
                record for record in agaza_data
                if record.get('Approval Status') == 'تمت الموافقة' and record.get('Type') in ['مرضي' , 'بالخصم']
            ]
            employee_data['Agaza'] = approved_agaza_data  # Only include approved and filtered agaza data
        # Fetch 'agaza' reports, but only for 'عارضة طارئة' and 'مرضي', and only approved ones
        agaza_ded = handle_attendance_reports(
            report_type='agaza',
            date_from=from_date,
            date_to=to_date,
            id=employee.id,
            
        )
        if agaza_ded:
            # Filter by approved status and agaza types 'عارضة طارئة' and 'مرضي'
            approved_agaza_data = [
                record for record in agaza_data
                if record.get('Approval Status') == 'تمت الموافقة' and record.get('deducat') == "مؤثر"
            ]
            employee_data['agaza_ded'] = approved_agaza_data  

        # Fetch 'deduction' reports
        deduction_data = handle_deduction_report(
            report_date=None,
            id=employee.id,
            date_from=from_date,
            date_to=to_date,
        )
        if deduction_data:
            employee_data['Deductions'] = deduction_data  # Include deduction data

        # Fetch 'ezn delay' reports
        ezn_delay_data = handle_ezn_delay(
            report_date=None,
            id=employee.id,
            date_from=from_date,
            date_to=to_date,
            employee_office_name=employee.office_name
        )
        print('ezn_delay_data',ezn_delay_data)
        if ezn_delay_data:
            # Extract the 'Delay Time' from the total delay row
            total_delay_time = next((row['Delay Time'] for row in ezn_delay_data if row['Employee Name'] == 'مجموع التأخيرات'), None)
            
            if total_delay_time:
                employee_data['Ezn Delays'] = total_delay_time  # Store only the 'Delay Time' value
            else:
                employee_data['Ezn Delays'] = '00:00:00'  # Default value if no total delay is found


        # Add the employee's detailed data to the detailed report
        detailed_report.append(employee_data)

        # Initialize delay time, deduction points, and agaza counts in summary report (if applicable)
        delay_time = "00:00:00"  # Default to zero if there's no delay data
        total_deductions = 0.0  # Default to zero if there's no deduction data
        agaza_count_emergency = 0
        agaza_count_sick = 0
        agaza_count_ded = 0
        if delay_data and len(delay_data) > 0:
            # Get the last row which contains total delay time
            last_row = delay_data[-1]
            delay_time = last_row.get('Delay Time', "00:00:00")  # Extract 'Delay Time' if available

        if deduction_data and len(deduction_data) > 0:
            # Get the last row which contains total deduction points
            last_row = deduction_data[-1]
            total_deductions = last_row.get('Deduction Points', 0.0)  # Extract total deductions if available

        if agaza_data:
            # Count each type of approved agaza
            agaza_types = [record.get('Type') for record in agaza_data if record.get('Approval Status') == 'تمت الموافقة']
            agaza_count_sick = agaza_types.count('مرضي')
            agaza_count_ded = agaza_types.count('بالخصم')
            
                    # Count the number of rates for the officer
        rates_count = EmployeeRates.query.filter_by(employee_id=employee.employment_id).count()
        last_rate= None
        if rates_count > 1:
            # If there is only one rate, fetch the last rate directly without offset
            last_rate = EmployeeRates.query.filter_by(employee_id=employee.employment_id) \
                                        .order_by(EmployeeRates.id.desc()) \
                                        .first() 
        else:
            # If there is only one rate, fetch the last rate directly without offset
            last_rate = EmployeeRates.query.filter_by(employee_id=employee.employment_id) \
                                        .order_by(EmployeeRates.id.desc()) \
                                        .first()    
        # Add the counts and total delay time to the summary report
        print(len(employee_data['absent']) if absent_data else 0 ,'Absent Count' )
        summary_report.append({
            'Employee Name': employee.name,
            'Office': employee.office_name,
            'Ezn Count': len(employee_data['Ezn']),
            'Clinic Count': len(employee_data['Clinic']),
            'Check-in Delays Count': len(employee_data['Check-in Delays'])- 1  if delay_data else 0,  # Exclude the last row as it’s the summary
            'Agaza Emergency Count': len(employee_data['agaza_ded']) if agaza_ded else 0,
            'Agaza Sick Count': agaza_count_sick,
            'Agaza Sick ded': agaza_count_ded,
            'Deductions Count': len(employee_data['Deductions']) - 1 if deduction_data else 0,
            'Absent Count': len(employee_data['absent']) if absent_data else 0,
            'Ezn Delays Count': employee_data['Ezn Delays'] if ezn_delay_data else "00:00:00",
            'Delay Time': delay_time,  # Include total delay time from last row
            'Total Deduction Points': total_deductions,  # Include total deduction points from last row
            'rate':last_rate.rate if last_rate else 'لا يوجد'
        })

    # Return both the detailed attendance report and the summary report
    return detailed_report, summary_report
def manage_agaza():
    try:
        print("Starting manage_agaza process...")

        # Step 1: Find all approved "أعتيادية" agazas
        regular_agazas = Agaza.query.filter(
            Agaza.type == 'أعتيادية',
            Agaza.approval_status == 'Approved'
        ).all()
        print(f"Found {len(regular_agazas)} regular 'أعتيادية' agazas.")
            
        for agaza in regular_agazas:
            print(f"Processing agaza ID: {agaza.id}, Employee ID: {agaza.employee_id}")
            from_date = agaza.from_date
            to_date = agaza.to_date
            print(f"From date: {from_date}, To date: {to_date}")

            # Step 2: Check for overlapping agazas of other types and official holidays
            overlapping_agazas = Agaza.query.filter(
                Agaza.employee_id == agaza.employee_id,
                Agaza.type != 'أعتيادية',
                (Agaza.from_date <= to_date) & (Agaza.to_date >= from_date)
            ).all()
            print(f"Found {len(overlapping_agazas)} overlapping agazas.")

            overlapping_holidays = OfficialHoliday.query.filter(
                (OfficialHoliday.from_date <= to_date) & (OfficialHoliday.to_date >= from_date)
            ).all()
            print(f"Found {len(overlapping_holidays)} overlapping holidays.")

            if overlapping_agazas or overlapping_holidays:
                print("Overlapping agazas or holidays found, removing approval...")
                # Step 3: Remove the original "أعتيادية" agaza approval
                approval = Approvals.query.filter(
                    Approvals.request_type == 'agaza',
                    Approvals.request_id == agaza.id
                ).first()
                if approval:
                    print(f"Deleting approval ID: {approval.approval_id}")
                    db.session.delete(approval)

                # Step 4: Create new "أعتيادية" agazas for non-overlapping periods
                current_date = from_date
                all_overlaps = sorted(overlapping_agazas + overlapping_holidays, key=lambda x: x.from_date)

                for overlap in all_overlaps:
                    overlap_from = overlap.from_date
                    overlap_to = overlap.to_date
                    print(f"Processing overlap from {overlap_from} to {overlap_to}")

                    if current_date < overlap_from:
                        new_agaza = Agaza(
                            employee_id=agaza.employee_id,
                            submit_date=agaza.submit_date,  # Copy submit_date from original agaza
                            alternative=agaza.alternative,  # Copy alternative from original agaza
                            from_date=current_date,
                            to_date=overlap_from - timedelta(days=1),
                            type='أعتيادية',
                            approval_status='Approved'
                        )
                        db.session.add(new_agaza)
                        db.session.flush()  # To get the new agaza ID
                        print(f"Created new agaza ID: {new_agaza.id} from {current_date} to {overlap_from - timedelta(days=1)}")

                        new_approval = Approvals(
                            request_type='agaza',
                            request_id=new_agaza.id,
                            office_manager_approval_status='Approved',
                            employee_affairs_approval_status='Approved',
                            secretary_approval_status='Approved',
                            vice_president_approval_status='Approved',
                            president_follower_approval_status='Approved',
                            president_approval_status='Approved'
                        )
                        db.session.add(new_approval)
                        print(f"Created new approval for agaza ID: {new_agaza.id}")

                    # Step 5: Calculate day count for the overlapping period
                    if isinstance(overlap, (Agaza, OfficialHoliday)):
                        day_count = (overlap_to - overlap_from).days + 1

                        print(f"Day count for overlap: {day_count} days")

                        # Step 6: Update employee's sanwya_points
                        employee = Employee.query.get(agaza.employee_id)
                        if employee:
                            employee.sanwya_points += day_count
                            print(f"Updated employee ID {employee.id} sanwya_points by {day_count} points.")

                    current_date = overlap_to + timedelta(days=1)

                if current_date <= to_date:
                    new_agaza = Agaza(
                        employee_id=agaza.employee_id,
                        submit_date=agaza.submit_date,
                        from_date=current_date,
                        alternative=agaza.alternative,
                        to_date=to_date,
                        type='أعتيادية',
                        approval_status='Approved'
                    )
                    db.session.add(new_agaza)
                    db.session.flush()  # To get the new agaza ID
                    print(f"Created final agaza ID: {new_agaza.id} from {current_date} to {to_date}")

                    new_approval = Approvals(
                        request_type='agaza',
                        request_id=new_agaza.id,
                        office_manager_approval_status='Approved',
                        employee_affairs_approval_status='Approved',
                        secretary_approval_status='Approved',
                        vice_president_approval_status='Approved',
                        president_follower_approval_status='Approved',
                        president_approval_status='Approved'
                    )
                    db.session.add(new_approval)
                    print(f"Created final approval for agaza ID: {new_agaza.id}")

        db.session.commit()
        print("Agaza management completed successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")

    finally:
        db.session.close()
        print("Database session closed.")
