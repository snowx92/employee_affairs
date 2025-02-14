from collections import defaultdict
import os
from queue import Empty, Queue
from threading import Lock, Thread
import traceback
from flask import Blueprint, json, logging, render_template, session, url_for, flash, redirect, request , jsonify ,current_app ,Response
import pandas as pd
from flask_login import login_user, current_user, logout_user, login_required
from app import  bcrypt, create_app
from app.forms import MomryaForm, RegistrationForm, LoginForm, EmployeeForm , HolidayForm, UserForm , UserSettingsForm , JobScheduleOverrideForm , AgazaForm ,AltmasForm ,ClinicForm ,EznForm
from app.models import Appear, EmployeeRates, Momrya, User, Employee, Attendance , OfficialHoliday  ,JobScheduleOverride , Ezn , Clinic , Agaza , Altmas , Approvals , Deduction as DED
from sqlalchemy.exc import IntegrityError
from sqlalchemy import case, func , String , and_, or_
from datetime import datetime, timedelta, timezone , time
from werkzeug.security import generate_password_hash 
from app.helpers import calculate_agaza_duration_this_year, convert_to_arabic_numerals, days_between_dates, format_date_to_arabic, format_time_to_arabic, generate_mo2srat_report, get_absent_employees, get_user_name_by_office, handle_attendance_reports , get_user_office_and_type , generate_attendance_report , manage_agaza
from app.extensions import db
from werkzeug.utils import secure_filename
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Session
from app.Face_Recognition.scripts.frame_generator import generate_frames
from sqlalchemy.exc import NoResultFound
import time as time_module
from sqlalchemy import case, func , String , and_, or_ , exc

main = Blueprint('main', __name__)



event_queue = Queue()

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    #print("Form Loaded")  # Debug #print

    if form.validate_on_submit():
        #print("Form Validated")  # Debug #print

        # Check if the username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('اسم المستخدم موجود بالفعل. الرجاء اختيار اسم مستخدم مختلف.', 'danger')
            #print("Username already exists")  # Debug #print
            return render_template('register.html', title='Register', form=form)

        # Check if the email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('البريد الإلكتروني موجود بالفعل. الرجاء اختيار بريد إلكتروني مختلف.', 'danger')
            #print("Email already exists")  # Debug #print
            return render_template('register.html', title='Register', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, user_type='user')
        
        try:
            #print("Attempting to add user to DB")  # Debug #print
            db.session.add(user)
            db.session.commit()
            #print("User added to DB successfully")  # Debug #print

            flash('تم إنشاء حسابك! أنت الآن قادر على تسجيل الدخول', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            #print("Error while adding user to DB")  # Debug #print
            db.session.rollback()
            flash('حدث خطأ أثناء إنشاء حسابك. يرجى المحاولة مرة أخرى في وقت لاحق.', 'danger')
            #print(str(e))  # Debug #print to show the exception

    else:
        #print("Form not validated")  # Debug #print
        for field, errors in form.errors.items():
            for error in errors:
                print(f"Error in the {field} field - {error}")  # Print form errors

    return render_template('register.html', title='Register', form=form)

@main.route('/', methods=['GET', 'POST'])
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.user_type == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')

            return redirect(next_page) if next_page else redirect(url_for('main.admin_dashboard'))

        else:
            flash('تسجيل الدخول غير ناجح. يرجى التحقق من البريد الإلكتروني وكلمة المرور', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/admin_dashboard')
@login_required
def admin_dashboard():
    print("current_user current_user" , current_user)
    today = datetime.today().date()

    # Calculate the first day of the current month
    date_from = today.replace(day=1)

    # Calculate date_to as today or the end of the month
    date_to = today  
    #print('date_from' , date_from)
    #print('date_to' , date_to)
    # Fetch the user's office and user_type
    user_info = get_user_office_and_type(current_user.id)
    user_office = user_info.get('office')
    user_type = user_info.get('user_type')

    # Initialize variables to hold the report data
    check_in_attendance = []
    check_out_attendance = []
    check_in_delays = []
    check_out_ahead = []
    clinic = []
    ezn = []
    agaza = []
    altmas = []
    data={}
    points={}
    #print("user_type" ,user_type )
    #print("user_office", user_office)
    #print('current_user.id' , current_user.id)
    # If the user is a manager, fetch data only for their office
    if user_type == 'manager':
        check_in_attendance = handle_attendance_reports(report_type='check_in_attendance', report_date=today, employee_office_name=user_office)
        check_out_attendance = handle_attendance_reports(report_type='check_out_attendance', report_date=today, employee_office_name=user_office)
        check_in_delays = handle_attendance_reports(report_type='check_in_delays', report_date=today, include_delay_minutes=True, employee_office_name=user_office)
        check_out_ahead = handle_attendance_reports(report_type='check_out_ahead', report_date=today, include_leave_early_time=True, employee_office_name=user_office)
        clinic = handle_attendance_reports(report_type='clinic', report_date=today, employee_office_name=user_office)
        ezn = handle_attendance_reports(report_type='ezn', report_date=today, employee_office_name=user_office)
        agaza = handle_attendance_reports(report_type='agaza', report_date=today, employee_office_name=user_office)
        altmas = handle_attendance_reports(report_type='altmas', report_date=today, employee_office_name=user_office)
        rest = handle_attendance_reports(report_type='rest', report_date=today, employee_office_name=user_office)
        data = {
        'check_in_attendance': len(check_in_attendance),
        'check_out_attendance': len(check_out_attendance),
        'check_in_delays': len(check_in_delays) - 1 if len(check_in_delays) > 0 else 0,
        'check_out_ahead': len(check_out_ahead) - 1 if len(check_out_ahead) > 0 else 0,
        'clinic': len(clinic),
        'ezn': len(ezn),
        'agaza': len(agaza),
        'altmas': len(altmas),
        'rest': len(rest)
         }
    
    elif user_type == 'employee':
        employee = Employee.query.filter_by(id=current_user.id).first_or_404()
        points={
        'tar7eel_points': employee.tar7eel_points,
        'sanwya_points': employee.sanwya_points,
        'arda_points': employee.arda_points
        }
        check_in_attendance = handle_attendance_reports(report_type='check_in_attendance', date_from=date_from, date_to=date_to, id=current_user.id)
        check_out_attendance = handle_attendance_reports(report_type='check_out_attendance', date_from=date_from, date_to=date_to, id=current_user.id)
        check_in_delays = handle_attendance_reports(report_type='check_in_delays', date_from=date_from, date_to=date_to, include_delay_minutes=True, id=current_user.id)
        check_out_ahead = handle_attendance_reports(report_type='check_out_ahead', date_from=date_from, date_to=date_to, include_leave_early_time=True, id=current_user.id)
        clinic = handle_attendance_reports(report_type='clinic', date_from=date_from, date_to=date_to, id=current_user.id)
        ezn = handle_attendance_reports(report_type='ezn', date_from=date_from, date_to=date_to, id=current_user.id)
        agaza = handle_attendance_reports(report_type='agaza', date_from=date_from, date_to=date_to, id=current_user.id)
        altmas = handle_attendance_reports(report_type='altmas', date_from=date_from, date_to=date_to, id=current_user.id)
        absent = get_absent_employees( date_from=date_from, date_to=date_to, employee_id=current_user.id)
        data = {
        'check_in_attendance': len(check_in_attendance),
        'check_out_attendance': len(check_out_attendance),
        'check_in_delays': len(check_in_delays) - 1 if len(check_in_delays) > 0 else 0,
        'check_out_ahead': len(check_out_ahead) - 1 if len(check_out_ahead) > 0 else 0,
        'clinic': len(clinic),
        'ezn': len(ezn),
        'agaza': len(agaza),
        'altmas': len(altmas),
        'absent': len(absent)
         }
    else:
        # Fetch data for all employees if the user is not a manager
        check_in_attendance = handle_attendance_reports(report_type='check_in_attendance', report_date=today , period='الفترة الصباحية')
        check_out_attendance = handle_attendance_reports(report_type='check_out_attendance', report_date=today, period='الفترة الصباحية')
        check_in_delays = handle_attendance_reports(report_type='check_in_delays', report_date=today, include_delay_minutes=True, period='الفترة الصباحية')
        check_out_ahead = handle_attendance_reports(report_type='check_out_ahead', report_date=today, include_leave_early_time=True, period='الفترة الصباحية')
        clinic = handle_attendance_reports(report_type='clinic', report_date=today, period='الفترة الصباحية')
        ezn = handle_attendance_reports(report_type='ezn', report_date=today, period='الفترة الصباحية')
        agaza = handle_attendance_reports(report_type='agaza_only', report_date=today, period='الفترة الصباحية')
        altmas = handle_attendance_reports(report_type='altmas', report_date=today, period='الفترة الصباحية')
        rest = handle_attendance_reports(report_type='rest', report_date=today, period='الفترة الصباحية')
        absent = get_absent_employees( specific_day=today, period='الفترة الصباحية')
        fr2a =handle_attendance_reports(report_type='fr2a', report_date=today, period='الفترة الصباحية')
        entdab =handle_attendance_reports(report_type='entdab', report_date=today, period='الفترة الصباحية')
        no_salary =handle_attendance_reports(report_type='no_salary', report_date=today, period='الفترة الصباحية')
       
                                
                # evening employees 
        check_in_attendance2 = handle_attendance_reports(report_type='check_in_attendance', report_date=today , period='الفترة المسائية')
        check_out_attendance2 = handle_attendance_reports(report_type='check_out_attendance', report_date=today, period='الفترة المسائية')
        check_in_delays2= handle_attendance_reports(report_type='check_in_delays', report_date=today, include_delay_minutes=True,period='الفترة المسائية')
        check_out_ahead2 = handle_attendance_reports(report_type='check_out_ahead', report_date=today, include_leave_early_time=True, period='الفترة المسائية')
        clinic2 = handle_attendance_reports(report_type='clinic', report_date=today,period='الفترة المسائية')
        ezn2 = handle_attendance_reports(report_type='ezn', report_date=today,period='الفترة المسائية')
        agaza2 = handle_attendance_reports(report_type='agaza_only', report_date=today, period='الفترة المسائية')
        altmas2 = handle_attendance_reports(report_type='altmas', report_date=today,period='الفترة المسائية')
        rest2 = handle_attendance_reports(report_type='rest', report_date=today,period='الفترة المسائية')
        absent2 = get_absent_employees( specific_day=today,period='الفترة المسائية')
        fr2a2= handle_attendance_reports(report_type='fr2a', report_date=today, period='الفترة المسائية')
        entdab2 =handle_attendance_reports(report_type='entdab', report_date=today, period='الفترة المسائية')
        no_salary2 =handle_attendance_reports(report_type='no_salary', report_date=today, period='الفترة المسائية')
        data = {
        'check_in_attendance_m': len(check_in_attendance),
        'check_out_attendance_m': len(check_out_attendance),
        'check_in_delays_m': len(check_in_delays) - 1 if len(check_in_delays) > 0 else 0,
        'check_out_ahead_m': len(check_out_ahead) - 1 if len(check_out_ahead) > 0 else 0,
        'clinic_m': len(clinic),
        'ezn_m': len(ezn),
        'agaza_m': len(agaza),
        'altmas_m': len(altmas),
        'rest_m': len(rest),
        'absent_m': len(absent),
        'fr2a_m':len(fr2a),
        'entdab_m':len(entdab),
        'no_salary_m':len(no_salary),
        'check_in_attendance_e': len(check_in_attendance2),
        'check_out_attendance_e': len(check_out_attendance2),
        'check_in_delays_e': len(check_in_delays2) - 1 if len(check_in_delays2) > 0 else 0,
        'check_out_ahead_e': len(check_out_ahead2) - 1 if len(check_out_ahead2) > 0 else 0,
        'clinic_e': len(clinic2),
        'ezn_e': len(ezn2),
        'agaza_e': len(agaza2),
        'altmas_e': len(altmas2),
        'rest_e': len(rest2),
        'absent_e': len(absent2),
        'fr2a_e':len(fr2a2),
        'entdab_e':len(entdab2),
        'no_salary_e':len(no_salary2),
         }
    

    
    current_date = format_date_to_arabic(datetime.today())

    return render_template('emplooye_affairs_admin/admin_dashboard.html', data=data, current_date=current_date, user_type=user_type , date_from= date_from , date_to=date_to , points = points , user_office=user_office)

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    form = UserSettingsForm(obj=current_user)

    if form.validate_on_submit():
        # Update user settings
        current_user.name = form.name.data

        # Update password if provided
        if form.password.data:
            current_user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Handle file upload
        if form.photo.data:
            photo = form.photo.data
            filename = secure_filename(photo.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, filename)

            # Debugging #print statements
            #print(f"Upload folder: {upload_folder}")
            #print(f"File path: {file_path}")
            #print(f"Filename: {filename}")

            # Create the directory if it does not exist
            if not os.path.exists(upload_folder):
                #print(f"Creating directory: {upload_folder}")
                os.makedirs(upload_folder)

            try:
                photo.save(file_path)
                #print(f"File saved successfully: {file_path}")
            except Exception as e:
                print(f"Error saving file: {e}")

            current_user.photo = filename  # Save the filename in the database

        # Commit changes to the database
        db.session.commit()
        flash('تم تحديث الإعدادات بنجاح!', 'success')
        return redirect(url_for('main.admin_settings'))

    return render_template('emplooye_affairs_admin/settings.html', form=form , user_type=current_user.user_type , user_office=current_user.office)

@main.route('/reports')
@login_required
def admin_reports():
    return render_template('emplooye_affairs_admin/reports.html' ,  user_type=current_user.user_type ,user_office=current_user.office)

@main.route('/admin_users')
@login_required
def admin_users():
    employees = Employee.query.all()
    return render_template('emplooye_affairs_admin/admin_users.html', employees=employees ,  user_type=current_user.user_type  ,user_office=current_user.office)

@main.route("/add_employee", methods=['GET', 'POST'])
@login_required
def add_employee():
    form = EmployeeForm()
    employee_id = request.args.get('employee_id')
    employee = None
    temp = 0
    if request.method == 'GET' and employee_id:
        employee = Employee.query.get_or_404(employee_id)

        if employee:
            # Pre-fill the form with the employee's data
            form.username.data = employee.username
            form.job_start_time.data = employee.job_start_time.strftime('%H:%M')
            form.job_end_time.data = employee.job_end_time.strftime('%H:%M')
            form.sat.data = employee.sat
            form.sun.data = employee.sun
            form.mon.data = employee.mon
            form.tues.data = employee.tues
            form.wed.data = employee.wed
            form.thr.data = employee.thr
            form.fri.data = employee.fri
            form.certificate.data = employee.certificate
            form.graduation_year.data = employee.graduation_year
                        # Convert birth_date to datetime object if it's a string
            if isinstance(employee.employment_start_year, str):
                try:
                    if len(employee.employment_start_year) == 4:  # Only a year
                        employee.employment_start_year = datetime.strptime(employee.employment_start_year, '%Y')
                    else:  # Full date
                        employee.employment_start_year = datetime.strptime(employee.employment_start_year, '%Y-%m-%d')
                except ValueError as e:
                    flash(f'Value Error: {e}', 'danger')
            form.employment_start_year.data = employee.employment_start_year
            form.office_name.data = employee.office_name
            form.period.data = employee.period
            form.employment_id.data = employee.employment_id
            form.nat_id.data = employee.nat_id
            form.name.data = employee.name
            
            # Convert birth_date to datetime object if it's a string
            if isinstance(employee.birth_date, str):
                try:
                    if len(employee.birth_date) == 4:  # Only a year
                        employee.birth_date = datetime.strptime(employee.birth_date, '%Y')
                    else:  # Full date
                        employee.birth_date = datetime.strptime(employee.birth_date, '%Y-%m-%d')
                except ValueError as e:
                    flash(f'Value Error: {e}', 'danger')

            form.birth_date.data = employee.birth_date if employee.birth_date else ''
            form.address.data = employee.address
            form.phone_number.data = employee.phone_number
            form.sec_phone_number.data = employee.sec_phone_number
            form.gender.data = employee.gender
            form.exp.data = employee.exp
            form.exp_type.data = employee.exp_type
            form.social.data = employee.social
            form.religion.data = employee.religion
            form.job_name_modli.data = employee.job_name_modli
            form.level.data = employee.level
            form.grade.data = employee.grade
            form.job_type.data = employee.job_type
            form.emp_type.data = employee.emp_type
            form.arda_points.data = employee.arda_points
            form.sanwya_points.data = employee.sanwya_points

            form.tar7eel_points.data = employee.tar7eel_points 
            form.doc_number.data = employee.doc_number 
            form.insurance_number.data = employee.insurance_number   
            form.active.data = employee.active  

    if request.method == 'POST':
        print("Add or edit employee")

        if form.validate_on_submit():
            try:

                job_start_time = datetime.strptime(form.job_start_time.data, '%H:%M').time()
                job_end_time = datetime.strptime(form.job_end_time.data, '%H:%M').time()
                
                if employee_id:

                    employee = Employee.query.get_or_404(employee_id)
                    temp = employee.sanwya_points
                    temp_Arda = employee.arda_points
                    current_year = datetime.now().year
                    agaza_duration_this_year2 = calculate_agaza_duration_this_year(employee_id, current_year,agaza_type= 'أعتيادية' )
                    agaza_duration_this_year3 = calculate_agaza_duration_this_year(employee_id, current_year,agaza_type= 'عارضة' )
                    print('agaza_duration_this_year2' , agaza_duration_this_year2)
                    if employee:
                        employee.username = form.username.data
                        employee.job_start_time = job_start_time
                        employee.job_end_time = job_end_time
                        employee.sat = form.sat.data
                        employee.sun = form.sun.data
                        employee.mon = form.mon.data
                        employee.tues = form.tues.data
                        employee.wed = form.wed.data
                        employee.thr = form.thr.data
                        employee.fri = form.fri.data
                        employee.certificate = form.certificate.data
                        employee.graduation_year = form.graduation_year.data
                        employee.employment_start_year = form.employment_start_year.data
                        employee.office_name = form.office_name.data
                        employee.period = form.period.data
                        employee.employment_id = employee.employment_id
                        employee.nat_id = form.nat_id.data
                        employee.name = form.name.data
                        employee.birth_date = form.birth_date.data
                        employee.address = form.address.data
                        employee.phone_number = form.phone_number.data
                        employee.sec_phone_number = form.sec_phone_number.data
                        employee.gender = form.gender.data
                        employee.exp = form.exp.data
                        employee.exp_type = form.exp_type.data
                        employee.social = form.social.data
                        employee.religion = form.religion.data
                        employee.job_name_modli = form.job_name_modli.data
                        employee.level = form.level.data
                        employee.grade = form.grade.data
                        employee.job_type = form.job_type.data
                        employee.emp_type = form.emp_type.data
                        employee.arda_points = form.arda_points.data
                        print('temp_Arda', temp_Arda)
                        print('temp_Arda', temp_Arda)
                        print('agaza_duration_this_year3' , agaza_duration_this_year3)
                        if temp_Arda < form.arda_points.data:
                            employee.arda_points = form.arda_points.data - agaza_duration_this_year3
                        else:
                            employee.arda_points = form.arda_points.data

                        if temp < form.sanwya_points.data:
                            employee.sanwya_points = form.sanwya_points.data - agaza_duration_this_year2
                        else:
                            employee.sanwya_points = form.sanwya_points.data
                            
                        employee.tar7eel_points = form.tar7eel_points.data 
                        employee.doc_number = form.doc_number.data 
                        employee.insurance_number = form.insurance_number.data  
                        employee.active = form.active.data 
                        user = User.query.get_or_404(employee_id)  # Assuming User has an employee_id foreign key
                        if user:
                            user.office = form.office_name.data  # Update the User office field
                            db.session.commit()  # Commit the changes for User
                        db.session.commit()
                        flash('تم تحديث الموظف بنجاح!', 'success')
                        return redirect(url_for('main.admin_users'))
                else:
                    print("Add new employee")
                    # Add new employee
                    employee = Employee(
                        username = form.username.data,
                        id=form.employment_id.data,

                        job_start_time=job_start_time,
                        job_end_time=job_end_time,
                        sat=form.sat.data,
                        sun=form.sun.data,
                        mon=form.mon.data,
                        tues=form.tues.data,
                        wed=form.wed.data,
                        thr=form.thr.data,
                        fri=form.fri.data,
                        certificate=form.certificate.data,
                        graduation_year=form.graduation_year.data,
                        employment_start_year=form.employment_start_year.data,
                        office_name=form.office_name.data,
                        period=form.period.data,
                        employment_id=form.employment_id.data,
                        nat_id=form.nat_id.data,
                        name=form.name.data,
                        birth_date=form.birth_date.data,
                        address=form.address.data,
                        phone_number=form.phone_number.data,
                        sec_phone_number=form.sec_phone_number.data,
                        gender=form.gender.data,
                        exp=form.exp.data,
                        exp_type=form.exp_type.data,
                        social=form.social.data,
                        religion=form.religion.data,
                        job_name_modli=form.job_name_modli.data,
                        level=form.level.data,
                        grade = form.grade.data,
                        job_type=form.job_type.data,
                        emp_type = form.emp_type.data,
                        arda_points = form.arda_points.data,
                        sanwya_points = form.sanwya_points.data, 
                        tar7eel_points = form.tar7eel_points.data, 
                        doc_number = form.doc_number.data, 
                        active = form.active.data,
                        insurance_number = form.insurance_number.data,
                        photo = form.employment_id.data+ ".jpg",   
                        
                    )
                    db.session.add(employee)
                    db.session.commit()
                    flash('!تمت إضافة الموظف بنجاح', 'success')
                    return redirect(url_for('main.admin_users'))
            except IntegrityError as IE:
                db.session.rollback()
                #print(f"An error occurred: {IE}")  # Print the error message
                flash('اسم المستخدم أو البريد الإلكتروني موجود بالفعل. يرجى المحاولة مرة أخرى.', 'danger')
            except ValueError as ve:
                flash(f'Value Error: {ve}', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'حدث خطأ غير متوقع: {e}', 'danger')
        else:
                    # Print form errors for debugging
            print('Form validation failed. Errors:', form.errors)
            flash('فشل التحقق من صحة النموذج. يرجى التحقق من المدخلات.', 'danger')
    print("add emp filled")
    return render_template('emplooye_affairs_admin/add_employee.html', form=form , user_type=current_user.user_type ,user_office=current_user.office,  employee_photo=employee.photo if employee else None)

@main.route("/delete_employee/<int:employee_id>", methods=['POST'])
@login_required
def delete_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        #print('employee:', employee)
        if employee:
            db.session.delete(employee)
            db.session.commit()
            
            flash('تم حذف الموظف بنجاح!', 'success')
        else:
            flash('لم يتم العثور على الموظف.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {e}', 'danger')

    # After deletion, redirect back to the admin users page
    return redirect(url_for('main.admin_users'))

@main.route('/admin/reports', methods=['GET', 'POST'])
@login_required
def reports():
    translations = {
        'Employee Name': 'اسم الموظف',
        'Office': 'المكتب',
        'Time': 'الوقت',
        'Delay Time': 'وقت التأخير',
        'Leave Early Time': 'وقت المغادرة المبكر',
        'date': 'التاريخ',
        'clinic_type': 'نوع العيادة',
        'back_time': 'وقت العودة',
        'result': 'النتيجة',
        'From Time': 'من الوقت',
        'From Date': 'من تاريخ',
        'To Date': 'إلى تاريخ',
        'To Time': 'إلى الوقت',
        'Out Time': 'وقت الخروج',
        'Back Time': 'وقت العوده',
        'atydya_points': 'نقاط اعتيادية',
        'arda_points': 'نقاط عارضة',
        'atydya_all': 'الكل الاعتيادية',
        'arda_all': 'الكل العارضة',
        'old_points': 'النقاط القديمة',
        'from_date': 'من التاريخ',
        'to_date': 'إلى التاريخ',
        'submit_date': 'تاريخ التقديم',
        'agza_type': 'نوع الاجازة',
        'Alternative': 'البديل',
        'Approval Status': 'حالة الموافقة',
        'Submit Date': 'تاريخ الطلب',
        'Type': 'نوع',
        'clone': 'البديل',
        'name': 'الاسم',
        'office_name': 'المكتب',
        'Message': 'الحالة',
        'Petition': 'الالتماس',
        'Diagnosis': 'تشخيص العيادة',
        'Clinic Type': 'نوع العيادة',
        'Date': 'تاريخ العيادة',
        'Rest Day': 'الراحة',
        'check_in_time': 'موعد العمل',
        'check_out_time':'موعد الانصراف',
        'notes_agaza_manager': 'ملاحظات المدير',
        'notes_agaza': 'ملاحظات الاجازة',
        'Arabic day':'يوم',
        'in':"حضور",
        'out':'انصرف',
        'Reason':'سبب المأمورية'
    }

    current_date = datetime.today().strftime('%Y-%m-%d')

    # Default report criteria for GET requests
    report_type = 'absent'   # Default report type (can be changed)
    report_from = current_date
    report_to = current_date
    period = None            # Default period (optional)

    # Determine if the current user is a manager
    user_office_name = None
    if current_user.user_type == 'manager':
        user_office_name = current_user.office

    # Check if the method is POST (form submission) or GET (button click)
    if request.method == 'POST':
        # If it's a POST request (from a form), retrieve the form data
        report_type = request.form['report_type']
        report_from = request.form['report_from']
        report_to = request.form['report_to']
        period = request.form.get('period', None)  # Optional for some report types

    elif request.method == 'GET':
        # Handle GET requests for fixed criteria
        # Example: Get the fixed criteria from query parameters or set defaults
        report_type = request.args.get('report_type', 'absent')  # Default to 'absent'
        report_to = request.args.get('report_to', current_date)
        report_from = request.args.get('report_from', current_date) # Default to today
        period = request.args.get('period', None)  # Default to None if not provided

    # Convert report_date to a datetime object
    report_from = datetime.strptime(report_from, '%Y-%m-%d').date()
    report_to = datetime.strptime(report_to, '%Y-%m-%d').date()
    current_date = datetime.strptime(current_date, '%Y-%m-%d').date()

    # Logic for report generation (either for POST or GET request)
    report_data = None

    if report_type == 'absent':
        # Call the get_absent_employees function
        report_data = get_absent_employees(
            date_from=report_from,
            date_to = report_to,
            period=period,
            office_name=user_office_name
        )

    elif report_type in ['check_in_attendance', 'check_in_delays','momrya' , 'check_out_attendance', 'check_out_ahead', 'no_check_out', 'rest', 'ezn', 'agaza', 'clinic', 'altmas' ,'check_all' , 'fr2a' , 'agaza_only', 'fr2a' , 'entdab', 'no_salary']:
        # Handle attendance-related reports using SQL queries
        report_data = handle_attendance_reports(
            report_type = report_type, 
            date_from=report_from,
            date_to = report_to,
            period = period, 
            include_delay_minutes=True, 
            include_leave_early_time=True,
            employee_office_name=user_office_name
        )

    if not report_data and request.method == 'POST':
        flash("لم يتم العثور على بيانات للمعايير المحددة.", "warning")
        return render_template('emplooye_affairs_admin/reports.html', current_date=current_date, user_type=current_user.user_type ,user_office=current_user.office)
    elif not report_data and request.method == 'GET':
        flash("لا يوجد بيانات في الوقت الحالي", "warning")
        return redirect(url_for('main.admin_dashboard'))

    return render_template('emplooye_affairs_admin/report_pdf.html', 
                           report_data=report_data, 
                           translations=translations, 
                           report_type=report_type, 
                           report_from=format_date_to_arabic(report_from), 
                           report_to=format_date_to_arabic(report_to),                           
                           current_date=format_date_to_arabic(current_date), 
                           user_type=current_user.user_type,
                           user_office=current_user.office,
                           count=len(report_data))
from flask import render_template, request, flash
from datetime import datetime




@main.route('/employee_report', methods=['GET', 'POST'])
@login_required
def employee_report():
    # Define the translation dictionary
    translations = {
        'Employee Name': 'اسم الموظف',
        'Office': 'المكتب',
        'Time': 'الوقت',
        'Delay Time': 'وقت التأخير',
        'Leave Early Time': 'وقت المغادرة المبكر',
        'date': 'التاريخ',
        'clinic_type': 'نوع العيادة',
        'back_time': 'وقت العودة',
        'result': 'النتيجة',
        'From Time': 'من الوقت',
        'From Date': 'من تاريخ',
        'To Date': 'إلى تاريخ',
        'To Time': 'إلى الوقت',
        'Out Time': 'وقت الخروج',
        'Back Time': 'وقت العوده',
        'atydya_points': 'نقاط اعتيادية',
        'arda_points': 'نقاط عارضة',
        'atydya_all': 'الكل الاعتيادية',
        'arda_all': 'الكل العارضة',
        'old_points': 'النقاط القديمة',
        'from_date': 'من التاريخ',
        'to_date': 'إلى التاريخ',
        'submit_date': 'تاريخ التقديم',
        'agza_type': 'نوع الاجازة',
        'Alternative': 'البديل',
        'Approval Status': 'حالة الموافقة',
        'Submit Date': 'تاريخ الطلب',
        'Type': 'نوع',
        'clone': 'البديل',
        'name': 'الاسم',
        'office_name': 'المكتب',
        'Message': 'الحالة',
        'Petition': 'الالتماس',
        'Diagnosis': 'تشخيص العيادة',
        'Clinic Type': 'نوع العيادة',
        'Date': 'تاريخ العيادة',
        'Rest Day': 'الراحة',
        'check_in_time': 'موعد العمل',
        'check_out_time':'موعد الانصراف',
        'notes_agaza_manager': 'ملاحظات المدير',
        'notes_agaza': 'ملاحظات الاجازة',
        'Arabic day':'يوم',
        'in':"حضور",
        'out':'انصرف',
        'Reason':'سبب المأمورية'
    }

    # Get user office from current_user
    user_office = current_user.office
    employee_id=None
    if current_user.user_type=='employee':
        employee_id = current_user.id
    # Fetch all offices for the dropdown
    all_offices = get_all_offices()  # Function to fetch all offices, implement as needed
    # Fetch employees for the user's office
    employees_in_office = get_employees_by_office(user_office)
    current_date = datetime.today().strftime('%Y-%m-%d')
    report_data = []  # Initialize as empty list in case no data is found

    if request.method == 'POST':
        report_type = request.form['report_type']
        date_from = request.form['date_from']
        date_to = request.form['date_to']
        employee_id = request.form['employee_name']
        report_date = f"من تاريخ: {date_from}  إلى: {date_to}"

        if report_type == 'absent':
            # Handle absent report
            #print(f"Generating absent report for {date_from} to {date_to}")
            report_data = get_absent_employees(specific_day=None, date_from=date_from, date_to=date_to, employee_id=employee_id, office_name=user_office)
        
        elif report_type in ['check_in_attendance', 'check_in_delays', 'momrya', 'check_out_attendance', 'check_out_ahead', 'no_check_out', 'rased', 'ezn', 'agaza', 'clinic', 'altmas' , 'rest' , 'check_all']:
            # Handle attendance related reports using SQL queries
            #print(f"Generating {report_type} report")
            report_data = handle_attendance_reports(report_type=report_type, date_from=date_from, date_to=date_to, id=employee_id, include_delay_minutes=True, include_leave_early_time=True)

        if not report_data:
            flash("لم يتم العثور على بيانات للمعايير المحددة.", "warning")
            return render_template('emplooye_affairs_admin/employee_report.html', current_date=current_date, user_type=current_user.user_type, user_office=user_office, all_offices=all_offices, employees=employees_in_office , employee_id=current_user.id)
        date_from = format_date_to_arabic( datetime.strptime(date_from, '%Y-%m-%d').date())
        date_to = format_date_to_arabic(datetime.strptime(date_to, '%Y-%m-%d').date())
        current_date =format_date_to_arabic(datetime.strptime(current_date, '%Y-%m-%d').date())
        report_date = f"من تاريخ: {date_from}  |||||  إلى: {date_to}"
        return render_template('emplooye_affairs_admin/report_pdf.html', report_data=report_data, translations=translations, report_type=report_type, report_date=report_date, current_date=current_date, user_type=current_user.user_type, user_office=user_office , count=len(report_data))

    return render_template('emplooye_affairs_admin/employee_report.html', user_type=current_user.user_type, user_office=user_office, all_offices=all_offices, employees=employees_in_office ,  employee_id=current_user.id)

def get_all_offices():
    return [
        ('تشغيل الحواسب'),
        ('شئون الدارسين'),
        ('التخطيط'),
        ('المكتبة'),
        ('اللغة العبريه'),
        ('الشئون الفنية'),
        ('الاجنحه التعليمية'),
        ('خدمة معاونة'),
        ('المطبعة'),
        ('اللغة العربية'),
        ('الدورات التعليمية'),
        ('الترجمة'),
        ('الامتحانات العسكرية'),
        ('الامتحانات المدنية'),
        ('التطوير'),
        ('السكرتارية'),
        ('الحسابات'),
        ('متابعة المدير'),
        ('الامن والاستعلامات'),
        ('شئون العاملين المدنيين'),
        ('الترجمة المدنية'),
        ('قسم الجودة'),
        ('اركان حرب مبنى 1'),
        ('اركان حرب مبنى 3'),
        ('اجازة بدون مرتب'),
        ('انتداب خارج وزارة الدفاع')
    ]


@main.route('/get_employees/<office>')
@login_required
def get_employees(office):
    try:
        # Fetch all employees for the given office with active status 'ظهور'
        employees = Employee.query.filter_by(office_name=office, active='ظهور').all()

        # Prepare the employee data to be returned
        employee_data = [
            {'id': e.id, 'name': e.name, 'period': e.period}
            for e in employees
        ]

        return jsonify(employee_data)

    except Exception as e:
        # Log error with context of the office
        print(f"Error fetching employees for office '{office}': {str(e)}")

        # Return a JSON error response with 500 status
        return jsonify({"error": f"An error occurred while fetching employees for office '{office}': {str(e)}"}), 500

def get_employees_by_office(office_name):
    employees = Employee.query.filter_by(office_name=office_name, active='ظهور').all()
    employee_data = []
    for e in employees:
       try:
           employee_data.append({'id': e.id, 'name': e.name, 'period': e.period})
       except Exception as sub_error:
           print(f"Skipped employee due to error: {sub_error}")   
    return employee_data

@main.route('/official_holidays')
@login_required
def official_holidays():
    holidays = OfficialHoliday.query.all()
    return render_template('emplooye_affairs_admin/official_holidays.html', holidays=holidays ,  user_type=current_user.user_type , user_office=current_user.office)

@main.route('/add_official_holidays', methods=['GET', 'POST'])
@login_required
def add_official_holiday():
    form = HolidayForm()
    if form.validate_on_submit():
        new_holiday = OfficialHoliday(
            name=form.name.data,
            from_date=form.from_date.data,
            to_date=form.to_date.data,
            type=form.type.data
        )
        db.session.add(new_holiday)
        db.session.commit()
        manage_agaza()
        flash('تمت إضافة الاجازة بنجاح!', 'success')
        return redirect(url_for('main.add_official_holiday'))
    return render_template('emplooye_affairs_admin/add_official_holiday.html', form=form, title='Add Holiday' , user_type=current_user.user_type , user_office=current_user.office)

@main.route('/official_holidays/edit/<int:holiday_id>', methods=['GET', 'POST'])
@login_required
def edit_official_holiday(holiday_id):
    holiday = OfficialHoliday.query.get_or_404(holiday_id)
    form = HolidayForm(obj=holiday)
    if form.validate_on_submit():
        holiday.name = form.name.data
        holiday.from_date = form.from_date.data
        holiday.to_date = form.to_date.data
        holiday.type = form.type.data
        holiday.submit_date = datetime.now(timezone.utc)
        db.session.commit()
        flash('تمت تحديث تاتجتزة بنجاح!', 'success')
        return redirect(url_for('main.official_holidays'))
    return render_template('emplooye_affairs_admin/add_official_holiday.html', form=form, title='Edit Holiday' , user_type=current_user.user_type ,user_office=current_user.office)

@main.route('/holidays/delete/<int:holiday_id>', methods=['POST'])
@login_required
def delete_official_holiday(holiday_id):
    holiday = OfficialHoliday.query.get_or_404(holiday_id)
    db.session.delete(holiday)
    db.session.commit()
    flash('تمت حذف الاجازة بنجاح!', 'success')
    return redirect(url_for('main.official_holidays'))
    


@main.route('/add_job_schedule_override', methods=['GET', 'POST'])
@login_required
def add_job_schedule_override():
    form = JobScheduleOverrideForm()

    if request.method == 'POST':
        # Ensure the choices are populated before form validation
        office = form.office_name.data if form.office_name.data else ''
        employees = Employee.query.filter_by(office_name=office).all() if office else []
        form.employee_name.choices = [(emp.id, f"{emp.name} ({emp.job_start_time} - {emp.job_end_time})") for emp in employees]
        
        if form.validate_on_submit():
            employee_id = form.employee_name.data
            dates_str = form.dates.data
            # Extract only the date part without time
            dates = [datetime.strptime(date.strip(), '%Y-%m-%d').date() for date in dates_str.split(',') if date.strip()]

            # Get start time and end time from the new select fields
            start_hour = form.job_start_hour.data
            start_minute = form.job_start_minute.data
            end_hour = form.job_end_hour.data
            end_minute = form.job_end_minute.data

            # Combine hours and minutes to form time objects
            job_start_time = time(int(start_hour), int(start_minute))
            job_end_time = time(int(end_hour), int(end_minute))

            # Check for date conflicts
            date_conflicts = []
            for date in dates:
                existing_override = JobScheduleOverride.query.filter_by(employee_id=employee_id, date=date).first()
                if existing_override:
                    date_conflicts.append(date)

            if date_conflicts:
                flash(f"تأكد: الجدولة موجودة بالفعل للتواريخ التالية: {', '.join(map(str, date_conflicts))}.", 'error')
                return redirect(url_for('main.add_job_schedule_override'))

            # If no conflicts, add the new overrides
            try:
                for date in dates:
                    override = JobScheduleOverride(
                        employee_id=employee_id,
                        date=date,  # Store only the date (yyyy-mm-dd)
                        job_start_time=job_start_time,
                        job_end_time=job_end_time
                    )
                    db.session.add(override)
                db.session.commit()
                flash('تمت إضافة تجاوزات جدول العمل بنجاح!', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('حدث خطأ أثناء إضافة تجاوزات جدول العمل. يرجى المحاولة مرة أخرى.', 'error')

            return redirect(url_for('main.add_job_schedule_override'))
        else:
            print("Form did not validate")
            print(form.errors)

    office = form.office_name.data if form.office_name.data else ''
    employees = Employee.query.filter_by(office_name=office).all() if office else []
    form.employee_name.choices = [(emp.id, f"{emp.name} ({emp.job_start_time} - {emp.job_end_time})") for emp in employees]

    return render_template('emplooye_affairs_admin/add_job_schedule_override.html', 
                            form=form, 
                            employees=[{'id': emp.id, 'name': emp.name , 'start': emp.job_start_time,'end': emp.job_end_time} for emp in employees], 
                            user_type=current_user.user_type,
                            user_office=current_user.office)


@main.route('/get_employee_schedule/<int:employee_id>', methods=['GET'])
@login_required
def get_employee_schedule(employee_id):
    try:
        # Check if the current user is an admin
        if current_user.user_type == 'admin':
            # Admins can access any employee's schedule
            employee = Employee.query.get_or_404(employee_id)
        else:
            # Non-admins can only access employees within the same office
            current_office = current_user.office
            employee = Employee.query.filter_by(id=employee_id, office=current_office).first()

        if employee:
            employee_data = {
                'id': employee.id,
                'job_start_time': employee.job_start_time.strftime('%H:%M') if employee.job_start_time else '',
                'job_end_time': employee.job_end_time.strftime('%H:%M') if employee.job_end_time else '',
                'name': employee.name
            }
            return jsonify(employee_data)
        else:
            return jsonify({'error': 'Employee not found or does not belong to your office'}), 404
    except Exception as e:
        #print(f"Error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@main.route('/job_schedule_override', methods=['GET'])
@login_required
def job_schedule_override():
    office = current_user.office  # Assuming current_user has an office_name attribute
    date = request.args.get('filter_date')

    # Build the initial query with a join to the Employee table
    query = JobScheduleOverride.query.join(Employee).with_entities(
        JobScheduleOverride.id, JobScheduleOverride.date, JobScheduleOverride.job_start_time,
        JobScheduleOverride.job_end_time, JobScheduleOverride.submit_date,
        Employee.id.label('employee_id'), Employee.name.label('employee_name')
    )

    # Filter by user's office if the user is an employee or manager
    if current_user.user_type in ['employee', 'manager']:
        query = query.filter(Employee.office_name == office)

    # Filter by date if provided
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            start_of_day = datetime.combine(filter_date, datetime.min.time())
            end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(JobScheduleOverride.date >= start_of_day, JobScheduleOverride.date <= end_of_day)
        except ValueError as e:
            print(f"Date parsing error: {e}")

    overrides = query.all()
    employees_with_overrides = {override.employee_id: override.employee_name for override in overrides}

    return render_template('emplooye_affairs_admin/job_schedule_override.html', overrides=overrides, employees_with_overrides=employees_with_overrides, user_type=current_user.user_type ,user_office=current_user.office)

@main.route('/delete_job_schedule_override/<int:override_id>', methods=['POST'])
@login_required
def delete_job_schedule_override(override_id):
    override = JobScheduleOverride.query.get_or_404(override_id)
    db.session.delete(override)
    db.session.commit()
    flash('تم حذف تجاوز العمل بنجاح.', 'success')
    return redirect(url_for('main.job_schedule_override'))

@main.route('/add_request', methods=['GET', 'POST'])
@login_required
def add_request():
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        
        if report_type == 'clinic':
            return handle_clinic_request()
        elif report_type == 'ezn':
            return handle_ezn_request()
        elif report_type == 'agaza':
            return handle_agaza_request(user_type=current_user.user_type , user_office=current_user.office, )
        elif report_type == 'altmas':
            return handle_altmas_request()
        elif report_type == 'momrya':
            return handle_momrya_request()
        else:
            flash('نوع الطلب غير صالح.', 'danger')
            return redirect(url_for('main.add_request'))
    
    # For GET requests, render the form
    all_offices = get_all_offices()  # Get the list of all offices
    return render_template(
        'emplooye_affairs_admin/add_request.html',
        user_type=current_user.user_type,
        id = current_user.id,
        user_office=current_user.office,
        all_offices=all_offices  # Pass all offices to the template
    )

def handle_clinic_request():
    form = ClinicForm()
    
    # Populate employee choices based on office_name
    office = form.office_name.data if form.office_name.data else ''
    employees = Employee.query.filter_by(office_name=office).all() if office else []
    form.employee_name.choices = [(emp.id, emp.name) for emp in employees]  # Use (id, name) tuples for choices
    
    if form.validate_on_submit():
        #print("ClinicForm is valid")
        

        
        clinic = Clinic(
            employee_id=form.employee_name.data,
            clinic_type=form.clinic_type.data,
            date=form.date.data,
            submit_date=datetime.now().date()
        )
        db.session.add(clinic)
        db.session.commit()

        # Add to Approvals table
        approval = Approvals(request_type='clinic', request_id=clinic.id)
        db.session.add(approval)
        db.session.commit()


        employee = Employee.query.get_or_404(form.employee_name.data)
        user_name = get_user_name_by_office(employee.office_name)
        report_data = {
                'clinic_date': format_date_to_arabic(form.date.data ),
                'today_date': datetime.now().date(),
                
                'today_arabic': format_date_to_arabic(datetime.now().date()),
                'employee_name': employee.name,
                'job_name_modli': employee.job_name_modli,
                'manger_name': user_name  # Include the user's name from User table
            }
        report_data_json = json.dumps(report_data)
        flash('تم إرسال طلب العيادة بنجاح.', 'success')
        return redirect(url_for('main.report_clinic_on_submit', report_data=report_data_json))
    else:
        #print("ClinicForm is invalid")
        #print("Errors:", form.errors)
        #print("Form data:", form.data)
        flash('خطأ في تقديم الطلب.', 'danger')
        return redirect(url_for('main.add_request'))
def handle_momrya_request():
    form = MomryaForm()
    
    # Populate employee choices based on office_name
    office = form.office_name.data if form.office_name.data else ''
    employees = Employee.query.filter_by(office_name=office).all() if office else []
    form.employee_name.choices = [(emp.id, emp.name) for emp in employees]  # Use (id, name) tuples for choices
    
    if form.validate_on_submit():
        #print("ClinicForm is valid")
        

        
        momrya = Momrya(
            employee_id=form.employee_name.data,
            reason=form.reason.data,
            date=form.date.data,
            to_date = form.to_date.data,
            submit_date=datetime.now().date()
        )
        db.session.add(momrya)
        db.session.commit()

        # Add to Approvals table
        approval = Approvals(request_type='momrya', request_id=momrya.id)
        db.session.add(approval)
        db.session.commit()


        employee = Employee.query.get_or_404(form.employee_name.data)
        user_name = get_user_name_by_office(employee.office_name)
        report_data = {
                'today_date': datetime.now().date(),  
                'today_arabic': format_date_to_arabic(datetime.now().date()),
                'employee_name': employee.name,
                'job_name_modli': employee.job_name_modli,
                'manger_name': user_name , # Include the user's name from User table
                'date':  format_date_to_arabic(form.date.data ) ,
                'to_date': format_date_to_arabic(form.to_date.data)
            }
        report_data_json = json.dumps(report_data)
        flash('تم إرسال طلب المأمورية بنجاح.', 'success')
        return redirect(url_for('main.report_momrya_on_submit', report_data=report_data_json))
    else:
        #print("ClinicForm is invalid")
        #print("Errors:", form.errors)
        #print("Form data:", form.data)
        flash('خطأ في تقديم الطلب.', 'danger')
        return redirect(url_for('main.add_request'))    
def handle_ezn_request():
    form = EznForm()
        # Populate employee choices based on office_name
    office = form.office_name.data if form.office_name.data else ''
    employees = Employee.query.filter_by(office_name=office).all() if office else []

    form.employee_name.choices = [(emp.id, emp.name) for emp in employees]  # Use (id, name) tuples for choices
    if form.validate_on_submit():
        #print("EznForm is valid")
        ezn = Ezn(
            employee_id=form.employee_name.data,
            from_time=datetime.strptime(form.from_time.data,'%H:%M').time(),
            to_time=datetime.strptime(form.to_time.data,'%H:%M').time(),
            submit_date=datetime.now().date()
        )
        db.session.add(ezn)
        db.session.commit()

        # Add to Approvals table
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get the count of all ezn records for this employee in the current month
        ezn_count = Ezn.query.filter(
            Ezn.employee_id == form.employee_name.data,
            db.extract('month', Ezn.submit_date) == current_month,
            db.extract('year', Ezn.submit_date) == current_year,
            Ezn.approval_status == 'Approved'
        ).count()
        
            #Set ezn_count to 1 if no approved records are found
        ezn_count = ezn_count if ezn_count > 0 else 1
        approval = Approvals(request_type='ezn', request_id=ezn.id)
        db.session.add(approval)
        db.session.commit()
        employee = Employee.query.get_or_404(form.employee_name.data)
        user_name = get_user_name_by_office(employee.office_name)
        today_date = datetime.today().strftime('%Y-%m-%d')
        print('today_date',today_date)
        report_data = {
                'today_date': today_date,
                'ezn_form_time': format_time_to_arabic(datetime.strptime(form.from_time.data,'%H:%M').time()),
                'submit_date': datetime.now().date(),
                'ezn_to_time': format_time_to_arabic(datetime.strptime(form.to_time.data,'%H:%M').time()),
                'employee_name': employee.name,
                'employee_job_name': employee.job_name_modli,
                'user_name': user_name,  # Include the user's name from User table
                'employee_office': employee.office_name,
                'ezn_count': ezn_count  # Include the count of ezn records for the current month
            }
        report_data_json = json.dumps(report_data)
        flash('تم إرسال اذن بنجاح.', 'success')
        return redirect(url_for('main.report_ezn_on_submit', report_data=report_data_json))
    else:
        #print("EznForm is invalid")
        #print("Errors:", form.errors)
        flash('خطأ في تقديم الاذن.', 'danger')

    return redirect(url_for('main.add_request'))
def handle_agaza_request(user_type ,user_office ):
    form = AgazaForm()
    
    # Populate employee choices based on office_name
    office = form.office_name.data if form.office_name.data else ''
    employees = Employee.query.filter_by(office_name=office).all() if office else []
    form.employee_name.choices = [(emp.id, emp.name) for emp in employees]
    print("form.impact_type.data" , form.impact_type.data)
    deducat = form.impact_type.data if form.impact_type.data else 'غير مؤثر'
    # Populate alternative choices with default and employees
    if employees:
        form.alternative.choices = [(9980, 'لا يوجد بديل')] + [(emp.id, emp.name) for emp in employees]
    else:
        form.alternative.choices = [(9980, 'لا يوجد بديل')]

    if form.validate_on_submit():

        from_date = form.from_date.data 
        to_date = form.to_date.data
        # Calculate the number of days for the agaza
        if from_date == to_date:
            agaza_days = 1  # Set to 1 day if the from_date and to_date are the same
        else:
            agaza_days = (to_date - from_date).days +1

        employee = Employee.query.get_or_404(form.employee_name.data)
        if not employee:
            flash('الموظف غير موجود.', 'danger')
            return redirect(url_for('main.add_request'))
        
        # Check availability of points
        if form.agaza_type.data == 'عارضة':
            if employee.arda_points < agaza_days:
                flash(f"لا توجد نقاط كافية للإجازة. طلبت {agaza_days} يوم، لكن لديك {employee.arda_points} فقط.", 'danger')
                return redirect(url_for('main.add_request'))
            else:
                # Deduct the points and show a flash message
                
                flash(f"سيتم خصم {agaza_days} نقاط من نقاط عارضةاذا تمت الموافقه على الاجازة", 'info')
        
        elif form.agaza_type.data in ['أعتيادية' , 'اجازة بدل انصراف']:
            if employee.sanwya_points >= agaza_days:
                # Enough sanwya_points
                
                flash(f"سيتم خصم {agaza_days}  نقاط من نقاط أعتيادية اذا تمت الموافقة على الاجازة", 'info')
            else:
                # Not enough sanwya_points
                remaining_days = agaza_days - employee.sanwya_points
                deducted_sanwya = employee.sanwya_points
                
                
                if employee.tar7eel_points >= remaining_days:
                    # Deduct remaining days from tar7eel_points

                    flash(f"سيتم خصم {deducted_sanwya} نقاط من نقاط أعتيادية و{remaining_days} نقاط من نقاط ترحيل اذا تمت الموافقه على الاجازة", 'info')
                else:
                    # Not enough points in both sanwya_points and tar7eel_points
                    flash(f"لا توجد نقاط كافية للإجازة. طلبت {agaza_days} يوم، ولكن لديك {deducted_sanwya} نقاط فقط في أعتيادية و{employee.tar7eel_points} نقاط في ترحيل.", 'danger')
                    return redirect(url_for('main.add_request'))
        
        print(deducat)
        # Determine if the agaza type is 'منحة' or 'فرقة'
        if form.agaza_type.data in ['انتداب','منحة', 'فرقة', 'مرضي' , 'اجازة بدل انصراف' , 'بدون مرتب' ]:
            # Automatically approve the agaza request
            agaza = Agaza(
                employee_id=form.employee_name.data,
                from_date=from_date,
                to_date=to_date,
                submit_date=datetime.now().date(),
                type=form.agaza_type.data,
                alternative=form.alternative.data,
                notes_agaza=form.notes_agaza.data,
                approval_status='Approved' ,
                deducat = deducat# Automatically set to 'approved'
            )
            db.session.add(agaza)
            db.session.commit()

            # Automatically approve in the Approvals table
            approval = Approvals(
                request_type='agaza',
                request_id=agaza.id,
                office_manager_approval_status='Approved',
                employee_affairs_approval_status='Approved',
                secretary_approval_status='Approved',
                vice_president_approval_status='Approved',
                president_follower_approval_status='Approved',
                president_approval_status='Approved'
            )
            db.session.add(approval)
            db.session.commit()

        else:
            # Normal agaza request without automatic approval
            agaza = Agaza(
                employee_id=form.employee_name.data,
                from_date=from_date,
                to_date=to_date,
                submit_date=datetime.now().date(),
                type=form.agaza_type.data,
                alternative=form.alternative.data,
                notes_agaza=form.notes_agaza.data,
                deducat = deducat
            )
            db.session.add(agaza)
            db.session.commit()

            # Standard process for adding to Approvals table (without preset approval statuses)
            approval = Approvals(
                request_type='agaza',
                request_id=agaza.id
            )
            db.session.add(approval)
            db.session.commit()
        
        employee = Employee.query.filter_by(id=form.employee_name.data).first()
        alternative = Employee.query.filter_by(id=form.alternative.data).first()
        # Calculate the duration of agaza
        agaza_duration = days_between_dates(agaza.from_date.strftime('%Y-%m-%d'), agaza.to_date.strftime('%Y-%m-%d'))+1
        print('agaza_duration' ,agaza_duration )
        # Get the current year
        current_year = datetime.now().year
        alt_name = "لا يوجد بديل"
        # Initialize default values
        most7ak = None
        year_agazas = None
        agaza_duration_this_year = None
        tar7eel_points = None
        sanwya_points = None
        arda_points = None
        # Check the type of agaza
        if agaza.type in ['أعتيادية', 'عارضة' ,'عارضة طارئة' , 'اجازة بدل انصراف']:
            agaza_duration_this_year = calculate_agaza_duration_this_year(form.employee_name.data, current_year,agaza_type= agaza.type ,submit_date= agaza.submit_date)
            agaza_duration_this_year2 = calculate_agaza_duration_this_year(form.employee_name.data, current_year,agaza_type= agaza.type )
            agaza_duration_this_year3 = calculate_agaza_duration_this_year(form.employee_name.data, current_year,agaza_type= agaza.type  , after=agaza.submit_date)
            print('agaza_duration_this_year' , agaza_duration_this_year)
            if agaza.type in ['أعتيادية' , 'اجازة بدل انصراف']:
                most7ak = agaza_duration_this_year2 + employee.sanwya_points  # Only for اعتياديه points
                tar7eel_points = convert_to_arabic_numerals(employee.tar7eel_points)
                sanwya_points = convert_to_arabic_numerals(employee.sanwya_points + agaza_duration_this_year3)
            
            elif agaza.type in [ 'عارضة' ,'عارضة طارئة']:
                print('in_arda')
                most7ak = agaza_duration_this_year2 + employee.arda_points  # Only for عارضه points
                arda_points = convert_to_arabic_numerals(employee.arda_points + agaza_duration_this_year3)
            
            year_agazas =agaza_duration_this_year
            print('year_agazas' , year_agazas)
        # Handle alternative employee name
        if alternative:
            alt_name = alternative.name
        # Prepare the report data
        print("agaza.from_date - timedelta(days=1)" , agaza.from_date - timedelta(days=1))
        report_data = {
            'employee_id': form.employee_name.data,
            'alternative': alt_name,
            'submit_date': datetime.today().strftime('%Y-%m-%d'),
            'from_date': format_date_to_arabic(agaza.from_date),
            'to_date': format_date_to_arabic(agaza.to_date),
            # Adjust the dates
            'from_date2': format_date_to_arabic(agaza.from_date - timedelta(days=1)),
            'to_date2': format_date_to_arabic(agaza.to_date + timedelta(days=1)),
            'today_date': datetime.today().strftime('%Y-%m-%d'),
            'agaza_type': agaza.type,
            'most7ak': convert_to_arabic_numerals(most7ak) if most7ak else None,
            "year_agazas": convert_to_arabic_numerals(year_agazas) if year_agazas else 0,
            'employee_name': employee.name,
            'job_name_modli': employee.job_name_modli,
            'office_name': employee.office_name,
            'agaza_duration': convert_to_arabic_numerals(agaza_duration),
            'agaza_duration_this_year': convert_to_arabic_numerals(agaza_duration_this_year) if agaza_duration_this_year else None,
            'tar7eel_points': tar7eel_points,
            'sanwya_points': sanwya_points,
            'arda_points': arda_points,
        }
        print('report_data' , report_data['agaza_type'])
        report_data_json = json.dumps(report_data)
        manage_agaza()

        return redirect(url_for('main.report_agaza_on_submit', report_data=report_data_json))
    else:
        
        #print("AgazaForm is invalid")
        #print("Form data:", form.data)
        #print("Errors:", form.errors)
        flash('خطأ في تقديم الاجازة.', 'danger')
                # Loop through the form errors and flash each one
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')

    return redirect(url_for('main.add_request'))
def handle_altmas_request():
    form = AltmasForm()
        # Populate employee choices based on office_name
    office = form.office_name.data if form.office_name.data else ''
    employees = Employee.query.filter_by(office_name=office).all() if office else []
    form.employee_name.choices = [(emp.id, emp.name) for emp in employees]  # Use (id, name) tuples for choices
    if form.validate_on_submit():
        #print("AltmasForm is valid")
        altmas = Altmas(
            employee_id=form.employee_name.data,
            petition=form.petition.data,
            submit_date=datetime.now().date()
        )
        db.session.add(altmas)
        db.session.commit()

        # Add to Approvals table
        approval = Approvals(request_type='altmas', request_id=altmas.id)
        db.session.add(approval)
        db.session.commit()
        employee = Employee.query.get_or_404(form.employee_name.data)
        user_name = get_user_name_by_office(employee.office_name)
        today_date =  datetime.today().strftime('%Y-%m-%d')
            
        report_data = {
                'today_date': today_date,
                'submit_date': today_date,
                'altmas_petition': form.petition.data,
                'employee_name': employee.name,
                'user_name': user_name,
                'employee_office': employee.office_name,
                'employee_job_name': employee.job_name_modli
            }
        report_data_json = json.dumps(report_data)
        flash('تم إرسال طلب العيادة بنجاح.', 'success')
        return redirect(url_for('main.report_altmas_on_submit', report_data=report_data_json))
    else:
        #print("AltmasForm is invalid")
        #print("Form data:", form.data)
        #print("Errors:", form.errors)
        flash('خطأ في تقديم الالتماس.', 'danger')

    return redirect(url_for('main.add_request'))

@main.route('/report_clinic_on_submit')
@login_required
def report_clinic_on_submit():
    # Get and deserialize the report_data from the query parameters

    report_data_json = request.args.get('report_data')
    report_data = json.loads(report_data_json) if report_data_json else {}
    flash('تم إرسال طلب العيادة بنجاح.', 'success')
    return render_template('emplooye_affairs_admin/report_clinic.html', data=report_data, sig=False)

@main.route('/report_momrya_on_submit')
@login_required
def report_momrya_on_submit():
    # Get and deserialize the report_data from the query parameters

    report_data_json = request.args.get('report_data')
    report_data = json.loads(report_data_json) if report_data_json else {}
    flash('تم إرسال طلب المأمورية بنجاح.', 'success')
    return render_template('emplooye_affairs_admin/report_momrya.html', data=report_data, sig=False)

@main.route('/report_ezn_on_submit')
@login_required
def report_ezn_on_submit():
    # Get and deserialize the report_data from the query parameters
    report_data_json = request.args.get('report_data')
    report_data = json.loads(report_data_json) if report_data_json else {}
    flash('تم إرسال طلب الاذن بنجاح.', 'success')
    return render_template('emplooye_affairs_admin/report_ezn.html', data=report_data , sig = False)

@main.route('/report_agaza_on_submit')
@login_required
def report_agaza_on_submit():
    # Get and deserialize the report_data from the query parameters
    report_data_json = request.args.get('report_data')
    report_data = json.loads(report_data_json) if report_data_json else {}
    flash('تم إرسال طلب الاجازة بنجاح.', 'success')
    return render_template('emplooye_affairs_admin/report_agaza.html', data=report_data, sig=False)

@main.route('/report_altmas_on_submit')
@login_required
def report_altmas_on_submit():
    # Get and deserialize the report_data from the query parameters
    report_data_json = request.args.get('report_data')
    report_data = json.loads(report_data_json) if report_data_json else {}
    flash('تم إرسال طلب الالتماس بنجاح.', 'success')
    return render_template('emplooye_affairs_admin/report_altmas.html', data=report_data, sig=False)

@main.route('/load_form/<report_type>', methods=['GET'])
def load_form(report_type):
    if report_type == 'clinic':
        form = ClinicForm()
    elif report_type == 'ezn':
        form = EznForm()
    elif report_type == 'agaza':
        form = AgazaForm()
    elif report_type == 'altmas':
        form = AltmasForm()
    elif report_type == 'momrya':
        form = MomryaForm()    
    else:
        return jsonify({"error": "Invalid report type"}), 400

    return render_template('emplooye_affairs_admin/dynamic_form.html', form=form ,  user_type=current_user.user_type, id = current_user.id, user_office=current_user.office)

@main.route('/api/requests_data', methods=['GET'])
def get_requests_data():
    date = request.args.get('filter_date')
    request_type = request.args.get('request_type')
    
    user_type = current_user.user_type
    user_office = current_user.office
    email = current_user.email
    user_employee_id = email.split('@')[0]

    # Function to fetch data for each request type
    def fetch_data_for_request_type(request_type):
        main_employee, alternative_employee = None, None

        # Determine the appropriate query based on request type
        if request_type == 'clinic':
            query = Clinic.query.join(Employee).with_entities(
                Clinic.id, Clinic.date, Clinic.out_time, Clinic.back_time,
                Clinic.diagnosis, Clinic.submit_date, Clinic.approval_status, Clinic.clinic_type,
                Employee.employment_id.label('employee_id'), Employee.name.label('employee_name'), 
                Employee.job_name_modli.label('job_title'), Employee.office_name.label('employee_office')
            )
        elif request_type == 'momrya':
            query = Momrya.query.join(Employee).with_entities(
                Momrya.id, Momrya.date,Momrya.to_date ,Momrya.out_time, Momrya.back_time,
                Momrya.reason, Momrya.submit_date, Momrya.approval_status,
                Employee.employment_id.label('employee_id'), Employee.name.label('employee_name'),
                Employee.job_name_modli.label('job_title'), Employee.office_name.label('employee_office')
            )
        elif request_type == 'ezn':
            query = Ezn.query.join(Employee).with_entities(
                Ezn.id, Ezn.from_time, Ezn.to_time, Ezn.out_time, 
                Ezn.back_time, Ezn.submit_date, Ezn.approval_status,
                Employee.employment_id.label('employee_id'), Employee.name.label('employee_name'),
                Employee.job_name_modli.label('job_title'), Employee.office_name.label('employee_office')
            )
        elif request_type == 'agaza':
            main_employee = aliased(Employee)
            alternative_employee = aliased(Employee)
            query = Agaza.query \
                .join(main_employee, main_employee.employment_id == Agaza.employee_id) \
                .outerjoin(alternative_employee, alternative_employee.employment_id == Agaza.alternative) \
                .filter(
                    (user_type == 'admin' and user_office in ['متابعة المدير', 'المدير', 'نائب المدير'])
                    or ~Agaza.type.in_(['انتداب', 'اجازة بدل انصراف', 'بدون مرتب'])
                ).with_entities(
                    Agaza.id, Agaza.from_date, Agaza.to_date, Agaza.submit_date,
                    Agaza.type, Agaza.approval_status,
                    Agaza.notes_agaza, Agaza.notes_agaza_manager,
                    main_employee.employment_id.label('employee_id'), main_employee.name.label('employee_name'),
                    main_employee.job_name_modli.label('job_title'), main_employee.office_name.label('employee_office'),
                    alternative_employee.name.label('alternative_employee_name')
                )
        elif request_type == 'altmas':
            query = Altmas.query.join(Employee).with_entities(
                Altmas.id, Altmas.petition, Altmas.submit_date, Altmas.approval_status,
                Employee.employment_id.label('employee_id'), Employee.name.label('employee_name'),
                Employee.job_name_modli.label('job_title'), Employee.office_name.label('employee_office')
            )

        # Apply date filter if available, otherwise default to today
        if date and request_type in ['agaza', 'clinic', 'ezn', 'altmas', 'momrya']:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            if request_type == 'agaza':
                query = query.filter(Agaza.submit_date == date_obj)
            elif request_type == 'clinic':
                query = query.filter(or_(Clinic.submit_date == date_obj, Clinic.date == date_obj))
            elif request_type == 'ezn':
                query = query.filter(Ezn.submit_date == date_obj)
            elif request_type == 'altmas':
                query = query.filter(Altmas.submit_date == date_obj)
            elif request_type == 'momrya':
                query = query.filter(Momrya.submit_date == date_obj)
        else:
            today = datetime.today().date()
            if request_type == 'agaza':
                query = query.filter(Agaza.submit_date == today)
            elif request_type == 'clinic':
                query = query.filter(or_(Clinic.submit_date == today, Clinic.date == today))
            elif request_type == 'ezn':
                query = query.filter(Ezn.submit_date == today)
            elif request_type == 'altmas':
                query = query.filter(Altmas.submit_date == today)
            elif request_type == 'momrya':
                query = query.filter(Momrya.submit_date == today)

        # Order the results by submit_date

        query = query.order_by(getattr(globals()[request_type.capitalize()], 'submit_date').desc())

        # Apply role-based filtering
        if user_type == 'admin' or (user_type == 'manager' and user_office== 'السكرتارية'):
            return query.all()
        elif user_type == 'manager':
            return query.filter((main_employee if main_employee else Employee).office_name == user_office).all()
        elif user_type == 'employee':
            return query.filter((main_employee if main_employee else Employee).employment_id == user_employee_id).all()

        return []

    # Fetch data for each request type
    results = {req_type: fetch_data_for_request_type(req_type) for req_type in
               ['clinic', 'ezn', 'agaza', 'altmas' , 'momrya']} if not request_type else {
                  request_type: fetch_data_for_request_type(request_type)}

    # Processing the fetched results with approval messages
    results_with_messages = {req_type: [] for req_type in ['clinic', 'ezn', 'agaza', 'altmas' , 'momrya']}
    for req_type, req_list in results.items():
        for item in req_list:
            approval = Approvals.query.filter_by(request_type=req_type, request_id=item.id).first()
            
            if item.approval_status == "Rejected" and current_user.id != item.employee_id:
                continue
                
            result_item = {
                'req_type': req_type,
                'id': item.id,
                'approval_id': approval.approval_id if approval else 'لم تسجل بعد',
                'approval_status_message': approval.approval_status_message() if approval else 'لم تسجل بعد',
                'employee_id': item.employee_id,
                'office_manager_approval_status': approval.office_manager_approval_status if approval else 'لم تسجل بعد',
                'secretary_approval_status':approval.secretary_approval_status if approval else 'لم تسجل بعد',
                'president_follower_approval_status':approval.president_follower_approval_status if approval else 'لم تسجل بعد',
                'employee_affairs_approval_status': approval.employee_affairs_approval_status if approval else 'لم تسجل بعد',
                'vice_president_approval_status': approval.vice_president_approval_status if approval else 'لم تسجل بعد',
                'president_approval_status': approval.president_approval_status if approval else 'لم تسجل بعد',
                'data': {
                    'date': item.date.strftime('%Y-%m-%d') if hasattr(item, 'date') and item.date else 'لم تسجل بعد',
                    'from_date': item.from_date.strftime('%Y-%m-%d') if hasattr(item, 'from_date') and item.from_date else 'لم تسجل بعد',
                    'to_date': item.to_date.strftime('%Y-%m-%d') if hasattr(item, 'to_date') and item.to_date else 'لم تسجل بعد',
                    'type': item.type if hasattr(item, 'type') else 'لم تسجل بعد',
                    'alternative_employee_name': item.alternative_employee_name if hasattr(item, 'alternative_employee_name') else 'لا يوجد بديل',
                    'notes_agaza': item.notes_agaza if hasattr(item, 'notes_agaza') else 'لم تسجل',
                    'notes_agaza_manager': item.notes_agaza_manager if hasattr(item, 'notes_agaza_manager') else 'لم تسجل',
                    'planned': item.planned if hasattr(item, 'planned') else 'لم تسجل',
                    'petition': item.petition if hasattr(item, 'petition') else 'لم تسجل',
                    'out_time': item.out_time.strftime('%H:%M:%S') if hasattr(item, 'out_time') and item.out_time else 'لم تسجل بعد',
                    'back_time': item.back_time.strftime('%H:%M:%S') if hasattr(item, 'back_time') and item.back_time else 'لم تسجل بعد',
                    'from_time': item.from_time.strftime('%H:%M:%S') if hasattr(item, 'from_time') and item.from_time else 'لم تسجل بعد',
                    'to_time': item.to_time.strftime('%H:%M:%S') if hasattr(item, 'to_time') and item.to_time else 'لم تسجل بعد',
                    'submit_date': item.submit_date.strftime('%Y-%m-%d') if item.submit_date else 'لم تسجل بعد',
                    'diagnosis': item.diagnosis if hasattr(item, 'diagnosis') else 'لم تسجل بعد',
                    'clinic_type': item.clinic_type if hasattr(item, 'clinic_type') else 'لم تسجل بعد',
                    'reason': item.reason if hasattr(item, 'reason') else 'لم تسجل بعد',
                    'employee_name': item.employee_name if hasattr(item, 'employee_name') else 'لم تسجل بعد',
                    'job_title': item.job_title if hasattr(item, 'job_title') else 'لم تسجل بعد',
                    'employee_office': item.employee_office if hasattr(item, 'employee_office') else 'لم تسجل بعد',
                    'approval_status': item.approval_status if hasattr(item, 'approval_status') else 'لم تسجل بعد',
                    'office_manager_approval_status': approval.office_manager_approval_status if approval else 'لم تسجل بعد',
                    'secretary_approval_status':approval.secretary_approval_status if approval else 'لم تسجل بعد',
                    
                    'president_follower_approval_status':approval.president_follower_approval_status if approval else 'لم تسجل بعد',
                    'employee_affairs_approval_status': approval.employee_affairs_approval_status if approval else 'لم تسجل بعد',
                    'vice_president_approval_status': approval.vice_president_approval_status if approval else 'لم تسجل بعد',
                    'president_approval_status': approval.president_approval_status if approval else 'لم تسجل بعد',
                }
            }
            results_with_messages[req_type].append(result_item)

    return jsonify(results_with_messages)

@main.route('/requests_veiws.html', methods=['GET'])
def requests_veiws():
    return render_template(
        'emplooye_affairs_admin/requests_veiws.html',
        user_type=current_user.user_type,
        user_office=current_user.office,    
        user_id=current_user.id,
        user_name=current_user.name
    )
    
# Server-side code (Python/Flask)
def process_request_action(approval_id, action_type):
    # Retrieve the approval object
    approval = Approvals.query.filter_by(approval_id=approval_id).first()

    if not approval:
        return jsonify({'status': 'error', 'message': 'Request not found.'}), 404
    
    # Define the stages in order
    stages = [
        'office_manager_approval_status',
        'employee_affairs_approval_status',
        'secretary_approval_status',
        'vice_president_approval_status',
        'president_follower_approval_status',
        'president_approval_status',
    ]
    
    # If delete action is requested
    if action_type == 'delete':
        try:
            db.session.delete(approval)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'Request deleted successfully.',
                'action_type': 'delete',
                'approval_id': approval_id
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Error occurred while deleting the request.'}), 500

    # Ensure valid action type
    if action_type not in ['approve', 'reject']:
        return jsonify({'status': 'error', 'message': 'Invalid action type.'}), 400

    current_stage = None
    action_taken = False
    
    # Loop through stages to approve or reject
    for stage in stages:
        status = getattr(approval, stage, None)

        if status == 'Pending':
            current_stage = stage
            if action_type == 'approve':
                if stage == 'president_approval_status':
                    setattr(approval, stage, 'Approved')
                    manage_agaza()
                setattr(approval, stage, 'Approved')
                action_taken = True
            elif action_type == 'reject':
                setattr(approval, stage, 'Rejected')
                action_taken = True
            break

    if not action_taken:
        return jsonify({'status': 'error', 'message': 'No pending stages found.'}), 400

    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Request {action_type}d successfully.',
            'action_type': action_type,
            'approval_id': approval_id,
            'stage': current_stage,
            'new_status': 'Approved' if action_type == 'approve' else 'Rejected'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Error occurred while processing the request action.'}), 500

@main.route('/api/handle_request_action', methods=['POST'])
def handle_request_action():
    data = request.get_json()
    approval_id = data.get('approval_id')
    action_type = data.get('action_type')
    
    if not approval_id or not action_type:
        return jsonify({'status': 'error', 'message': 'Missing required parameters.'}), 400
        
    return process_request_action(approval_id, action_type)

@main.route('/generate_print_report', methods=['POST'])
@login_required
def generate_print_report():
    # Get the report type from the form

    report_type = request.json.get('report_type')
    request_id = request.json.get('request_id')
    employee_id = request.json.get('employee_id')
    # Determine which template and data to use based on the report type
    if report_type == 'agaza':
        # Get additional data specific to agaza
        agaza_id = request_id

        # Query the Agaza and Employee data
        agaza = Agaza.query.filter_by(id=agaza_id, employee_id=employee_id).first()
        employee = Employee.query.filter_by(id=employee_id).first()

        alternative = Employee.query.filter_by(id=agaza.alternative).first()
        
        if agaza and employee:
            # Calculate the duration of agaza
            agaza_duration = days_between_dates(agaza.from_date.strftime('%Y-%m-%d'), agaza.to_date.strftime('%Y-%m-%d'))+1

            # Get the current year
            current_year = datetime.now().year
            alt_name = "لا يوجد بديل"

            # Initialize default values
            most7ak = None
            year_agazas = None
            agaza_duration_this_year = None
            tar7eel_points = None
            sanwya_points = None
            arda_points = None
            # Check the type of agaza
            if agaza.type in ['أعتيادية', 'عارضة' , 'عارضة طارئة' , 'اجازة بدل انصراف']:
                agaza_duration_this_year = calculate_agaza_duration_this_year(employee_id, current_year,agaza_type= agaza.type ,submit_date= agaza.submit_date)
                agaza_duration_this_year2 = calculate_agaza_duration_this_year(employee_id, current_year,agaza_type= agaza.type )
                agaza_duration_this_year3 = calculate_agaza_duration_this_year(employee_id, current_year,agaza_type= agaza.type  , after=agaza.submit_date)
                print('agaza_duration_this_year' , agaza_duration_this_year)
                if agaza.type in ['أعتيادية' , 'اجازة بدل انصراف'] :
                    most7ak = agaza_duration_this_year2 + employee.sanwya_points  # Only for اعتياديه points
                    tar7eel_points = convert_to_arabic_numerals(employee.tar7eel_points)
                    sanwya_points = convert_to_arabic_numerals(employee.sanwya_points + agaza_duration_this_year3)
                
                elif agaza.type in [ 'عارضة' , 'عارضة طارئة']:
                    most7ak = agaza_duration_this_year2 + employee.arda_points  # Only for عارضه points
                    arda_points = convert_to_arabic_numerals(employee.arda_points + agaza_duration_this_year3)
                
                year_agazas =agaza_duration_this_year
                print('year_agazas' , year_agazas)
            # Handle alternative employee name
            if alternative:
                alt_name = alternative.name

            # Prepare the report data
            report_data = {
                'employee_id': employee_id,
                'notes': agaza.notes_agaza if agaza.notes_agaza  else None,
                'alternative': alt_name,
                'submit_date': agaza.submit_date,
                'from_date': format_date_to_arabic(agaza.from_date),
                'to_date': format_date_to_arabic(agaza.to_date),
                'from_date2': format_date_to_arabic(agaza.from_date - timedelta(days=1)),
                'to_date2': format_date_to_arabic(agaza.to_date + timedelta(days=1)),
                'today_date': datetime.today().strftime('%Y-%m-%d'),
                'agaza_type': agaza.type,
                'most7ak': convert_to_arabic_numerals(most7ak) if most7ak else None,
                "year_agazas": convert_to_arabic_numerals(year_agazas) if year_agazas else 0,
                'employee_name': employee.name,
                'job_name_modli': employee.job_name_modli,
                'office_name': employee.office_name,
                'agaza_duration': convert_to_arabic_numerals(agaza_duration),
                'agaza_duration_this_year': convert_to_arabic_numerals(agaza_duration_this_year) if agaza_duration_this_year else None,
                'tar7eel_points': tar7eel_points,
                'sanwya_points': sanwya_points,
                'arda_points': arda_points,
            }
            print(report_data)

        return render_template('emplooye_affairs_admin/report_agaza.html', data=report_data , sig=True)
    
    elif report_type == 'clinic':
        clinic_id = request_id
        # Get clinic-specific data directly here
        clinic_record = Clinic.query.filter_by(id=clinic_id,employee_id=employee_id).order_by(Clinic.date.desc()).first()
        employee = Employee.query.get_or_404(employee_id)
        
        if clinic_record and employee:
            today_date = datetime.today().strftime('%Y-%m-%d')
            user_name = get_user_name_by_office(employee.office_name)
            
            report_data = {
                'clinic_date': clinic_record.date,
                'today_date': today_date,
                
                'today_arabic': format_date_to_arabic(clinic_record.date),
                'employee_name': employee.name,
                'job_name_modli': employee.job_name_modli,
                'manger_name': user_name  # Include the user's name from User table
            }
            return render_template('emplooye_affairs_admin/report_clinic.html', data=report_data , sig = True) 
    elif report_type == 'momrya':
        momrya_id = request_id
        # Get clinic-specific data directly here
        momrya_record = Momrya.query.filter_by(id=momrya_id,employee_id=employee_id).order_by(Momrya.date.desc()).first()
        employee = Employee.query.get_or_404(employee_id)
        
        if momrya_record and employee:
            today_date = datetime.today().strftime('%Y-%m-%d')
            user_name = get_user_name_by_office(employee.office_name)
            
            report_data = {
                'today_date': datetime.now().date(),  
                'today_arabic': format_date_to_arabic(datetime.now().date()),
                'employee_name': employee.name,
                'job_name_modli': employee.job_name_modli,
                'manger_name': user_name , # Include the user's name from User table
                'date':  format_date_to_arabic(momrya_record.date ) ,
                'to_date': format_date_to_arabic(momrya_record.to_date)
            }
            return render_template('emplooye_affairs_admin/report_momrya.html', data=report_data)      

    elif report_type == 'ezn':
        ezn_id = request_id
        # Get ezn-specific data
        ezn_records = Ezn.query.filter_by(id=ezn_id, employee_id=employee_id).first()
        employee = Employee.query.get_or_404(employee_id)

        if ezn_records and employee:
            # Get the current month and year
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Get the count of all ezn records for this employee in the current month
            ezn_count = Ezn.query.filter(
                Ezn.employee_id == employee_id,
                db.extract('month', Ezn.submit_date) == current_month,
                db.extract('year', Ezn.submit_date) == current_year,
                Ezn.approval_status == 'Approved'
            ).count()
        
            #Set ezn_count to 1 if no approved records are found
            ezn_count = ezn_count if ezn_count > 0 else 1
            # Prepare report data
            today_date = datetime.today().strftime('%Y-%m-%d')
            user_name = get_user_name_by_office(employee.office_name)
            
            report_data = {
                'today_date': today_date,
                'ezn_form_time': format_time_to_arabic(ezn_records.from_time),
                'submit_date': ezn_records.submit_date,
                'ezn_to_time': format_time_to_arabic(ezn_records.to_time),
                'employee_name': employee.name,
                'employee_job_name': employee.job_name_modli,
                'user_name': user_name,  # Include the user's name from User table
                'employee_office': employee.office_name,
                'ezn_count': ezn_count  # Include the count of ezn records for the current month
            }

            return render_template('emplooye_affairs_admin/report_ezn.html', data=report_data , sig = True)

    elif report_type == 'altmas':
        altmas_id = request_id
        # Get the most recent altmas record for the employee
        altmas_record = Altmas.query.filter_by(id=altmas_id ,employee_id=employee_id).order_by(Altmas.submit_date.desc()).first()
        employee = Employee.query.get_or_404(employee_id)
        user_name = get_user_name_by_office(employee.office_name)

        if altmas_record and employee:
            today_date =  datetime.today().strftime('%Y-%m-%d')
            
            report_data = {
                'today_date': today_date,
                'submit_date': altmas_record.submit_date,
                'altmas_petition': altmas_record.petition,
                'employee_name': employee.name,
                'user_name': user_name,
                'employee_office': employee.office_name,
                'employee_job_name': employee.job_name_modli
            }
            return render_template('emplooye_affairs_admin/report_altmas.html', data=report_data , sig =True)
        
 

    else:
        # Handle the case where the report type is not recognized
        return "Invalid report type specified", 400
 
@main.route('/api/update_request/<string:request_type>/<int:request_id>', methods=['POST'])
def update_request_details(request_type, request_id):
    """
    Simplified function to handle updating various types of requests.
    
    Args:
        request_type (str): Type of request ('agaza', 'momrya', 'ezn', 'clinic')
        request_id (int): ID of the request
    """
    try:
        data = request.json
        field = data.get('field')
        value = data.get('value')
        
        # Map request types to their corresponding models
        model_map = {
            'agaza': Agaza,
            'momrya': Momrya,  # Using Agaza model for momrya
            'ezn': Ezn,
            'clinic': Clinic
        }


        if request_type not in model_map:
            return jsonify({'success': False, 'error': 'Invalid request type'}), 400
            
                # Retrieve the Approvals record first
        approval_record = Approvals.query.get_or_404(request_id)
        actual_request_id = approval_record.request_id

        # Now retrieve the actual record from the mapped model
        record = model_map[request_type].query.get_or_404(actual_request_id)
        
        # Handle different field types
        if field in ['out_time', 'back_time']:
            try:
                setattr(record, field, datetime.strptime(value, "%H:%M").time())
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid time format for {field}'}), 400
                
        elif field in ['from_date', 'to_date']:
            try:
                setattr(record, field, datetime.strptime(value, '%Y-%m-%d').date())
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid date format for {field}'}), 400
                
        elif field in ['notes_agaza', 'notes_agaza_manager', 'diagnosis']:
            setattr(record, field, value)
            
        else:
            return jsonify({'success': False, 'error': 'Invalid field'}), 400
            
        db.session.commit()
        return jsonify({'success': True})
        
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    except Exception as e:
        print("Exception occurred:", e)
        print("Traceback:", traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500



recognized_person_id = [None]  # Mutable object to store the recognized ID
last_recognized_id = None
last_recognition_time = None
lock = Lock()
@main.route('/face-recognition')
def face_recognition():
    return render_template('emplooye_affairs_admin/attendence.html', user_type=current_user.user_type)

@main.route('/video_feed/')
def video_feed():
    # Return the response directly from the generate_frames function
    return Response(generate_frames(recognized_person_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route('/recognized_id_feed')
def recognized_id_feed():
    def event_stream():
        while True:
            try:
                # Wait for an employee ID to be put into the queue
                employee_id = event_queue.get(timeout=10)  # Timeout to avoid indefinite blocking
                if employee_id:
                    try:
                        employee_data = fetch_employee_data(employee_id)
                        yield f'data: {json.dumps(employee_data)}\n\n'
                    except Exception as e:
                        print('Error fetching employee data:', e)
            except Empty:
                # Optionally handle cases when queue is empty or provide a status
                #print(' EmptyEmptyEmptyEmptyEmptyEmptyEmpty')
                continue  # Or use `break` if you want to end the stream when empty
    
    return Response(event_stream(), mimetype="text/event-stream")

def fetch_employee_data(employee_id):
    """Function to fetch employee data in the application context."""
    context_data = {}
    
    def get_employee_data():
        app = create_app()  # Create a new app instance for the context
        with app.app_context():  # Use create_app() to set up the application context

            employee = Employee.query.filter_by(id=employee_id).first()
            
            # Check if the employee exists
            if employee:
                # Get the current date and time
                now = datetime.now()
                current_date = now.strftime('%Y-%m-%d')
                current_time = now.strftime('%H:%M:%S')
                
                # Calculate the period based on the current date and job start/end times
                
                
                # Prepare the result data
                result_data = {
                    'employee_id': employee.id,
                    'name': employee.name,
                    'office_name': employee.office_name,
                    'job_start_time': employee.job_start_time.strftime('%H:%M:%S'),
                    'job_end_time': employee.job_end_time.strftime('%H:%M:%S'),
                    'date_of_today': current_date,
                    'time_now': current_time,
                    'period': employee.period,
                    'img':employee.photo
                }
                context_data['data'] = result_data
            else:
                context_data['data'] = {'error': 'Employee not found'}
    
    # Create and start the thread
    thread = Thread(target=get_employee_data)
    thread.start()
    thread.join()  # Wait for the thread to finish

    return context_data['data']

def get_margin_time(job_time, margin_hours=0, margin_minutes=0):
    """Get margin time before or after a job time."""
    return job_time - timedelta(hours=margin_hours, minutes=margin_minutes)

def get_max_margin_time(job_time, margin_hours=0, margin_minutes=0):
    """Get maximum margin time after a job time."""
    return job_time + timedelta(hours=margin_hours, minutes=margin_minutes)

def process_attendance_for_employee(employee_id):
    today = datetime.now().date()

    # Retrieve employee and job schedule override
    try:
        employee = db.session.query(Employee).filter_by(id=employee_id).one()
    except NoResultFound:
        print(f"No employee found with ID {employee_id}")
        return

    override = db.session.query(JobScheduleOverride).filter_by(employee_id=employee_id, date=today).first()
    job_start_time = override.job_start_time if override else employee.job_start_time
    job_end_time = override.job_end_time if override else employee.job_end_time

    # Define margins
    check_in_margin_start = get_margin_time(datetime.combine(today, job_start_time), margin_hours=4)
    check_in_margin_end = get_margin_time(datetime.combine(today, job_start_time), margin_hours=-1)
    # Check if today is Thursday (3 means Thursday)
    if today.weekday() == 3:
        # If today is Thursday
        check_out_margin_start = get_max_margin_time(datetime.combine(today, job_end_time), margin_hours=-1)
    else:
        # For other days
        check_out_margin_start = get_max_margin_time(datetime.combine(today, job_end_time), margin_hours=-0.01)
    check_out_margin_end = get_max_margin_time(datetime.combine(today, job_end_time), margin_hours=4)

    # Retrieve or create attendance record for today
    attendance = db.session.query(Attendance).filter_by(employee_id=employee_id, date=today).first()

    # Handle Check-in
    check_in_time_to_record = None
    if attendance and attendance.check_in_time:
        check_in_time = attendance.check_in_time
        check_in_datetime = datetime.combine(today, check_in_time)
        if check_in_margin_start <= check_in_datetime <= check_in_margin_end:

            check_in_time_to_record = check_in_time
    if not check_in_time_to_record:
        now = datetime.now()
        if check_in_margin_start <= now <= check_in_margin_end:
            check_in_time_to_record = now.time()
            #pygame.mixer.music.load('sound.mp3')
            #pygame.mixer.music.play()  
    # Handle Check-out
    check_out_time_to_record = None
    if attendance and attendance.check_out_time:
        check_out_time = attendance.check_out_time
        check_out_datetime = datetime.combine(today, check_out_time)
        now = datetime.now()
        if check_out_margin_start <= now <= check_out_margin_end:
            if now.time() > check_out_time:
                check_out_time_to_record = now.time()
                #pygame.mixer.music.load('sound.mp3')
                #pygame.mixer.music.play()   
            else:
                check_out_time_to_record = check_out_time
        else:
            check_out_time_to_record = check_out_time
    else:
        now = datetime.now()
        if check_out_margin_start <= now <= check_out_margin_end:
            check_out_time_to_record = now.time()
            #pygame.mixer.music.load('sound.mp3')
            #pygame.mixer.music.play()   

    if attendance:
        if check_in_time_to_record:
            attendance.check_in_time = check_in_time_to_record
         
        if check_out_time_to_record:
            attendance.check_out_time = check_out_time_to_record

        db.session.commit()

    else:
        attendance = Attendance(
            employee_id=employee_id,
            date=today,
            period='Work', # not used with anything 
            check_in_time=check_in_time_to_record,
            check_out_time=check_out_time_to_record
        )
        db.session.add(attendance)
        db.session.commit()
        #pygame.mixer.music.load('sound.mp3')
        #pygame.mixer.music.play()
    # Process permissions (Ezn records)
    ezns = db.session.query(Ezn).filter_by(employee_id=employee_id, submit_date=today, approval_status='Approved').all()
    for ezn in ezns:
        if ezn.from_time and ezn.to_time:
            from_time = datetime.combine(today, ezn.from_time)
            to_time = datetime.combine(today, ezn.to_time)

            # Define margins for exit and return times
            exit_margin_start = from_time
            exit_margin_end = get_max_margin_time(from_time, margin_minutes=30)
            return_margin_start = get_margin_time(to_time, margin_minutes=30)
            return_margin_end = get_max_margin_time(to_time, margin_minutes=30)

            now = datetime.now().time()

            if ezn.out_time is None and exit_margin_start <= datetime.now() <= exit_margin_end:
                # If `out_time` is None and within margin, record the current time
                ezn.out_time = now
                #pygame.mixer.music.load('sound.mp3')
                #pygame.mixer.music.play()
            elif ezn.out_time and exit_margin_start <= datetime.now() <= exit_margin_end:
                # If `out_time` is not None and within margin, compare and update if current time is greater
                if now > ezn.out_time:
                    ezn.out_time = now
                    #pygame.mixer.music.load('sound.mp3')
                    #pygame.mixer.music.play()
            if ezn.back_time is None and return_margin_start <= datetime.now() <= return_margin_end:
                # Record the first appearance within the `back_margin` period
                ezn.back_time = now
                #pygame.mixer.music.load('sound.mp3')
                #pygame.mixer.music.play()

            db.session.commit()

    # Process clinic records
    clinics = db.session.query(Clinic).filter_by(employee_id=employee_id, date=today, approval_status='Approved').all()
    for clinic in clinics:
        if clinic.from_time:
            from_time = datetime.combine(today, clinic.from_time)
            out_time_margin_start = from_time
            out_time_margin_end = get_max_margin_time(from_time, margin_minutes=30)

            now = datetime.now().time()

            if clinic.out_time is None and out_time_margin_start <= datetime.now() <= out_time_margin_end:
                # Record the first `out_time` within the margin
                clinic.out_time = now
                #pygame.mixer.music.load('sound.mp3')
                #pygame.mixer.music.play()
            elif clinic.out_time and out_time_margin_start <= datetime.now() <= out_time_margin_end:
                # If `out_time` is not None and within margin, update to the last time within margin
                if now > clinic.out_time:
                    clinic.out_time = now
                    #pygame.mixer.music.load('sound.mp3')
                    #pygame.mixer.music.play()
            if clinic.back_time is None and datetime.now() > out_time_margin_end:
                # Record the first `back_time` after the margin
                clinic.back_time = now
                #pygame.mixer.music.load('sound.mp3')
                #pygame.mixer.music.play()
            db.session.commit()

        ##print(today)

    print(f"Processed attendance and permissions for Employee ID: {employee_id}")
        
employee_appearance_tracker = defaultdict(int)
queue_count = 0
# Dictionary to track the last appearance time of each employee
last_appearance_times = {}
def record_appearance(employee_id):
    global queue_count
    app = create_app()  
    with app.app_context():
        now = datetime.now()
        current_time = now.time()
        current_date = now.date()

        # Check if the employee has been recorded within the last 10 seconds
        if employee_id in last_appearance_times:
            last_time = last_appearance_times[employee_id]
            elapsed_time = (now - last_time).total_seconds()

            if elapsed_time <= 10:
                print(f"Skipping duplicate appearance for employee {employee_id} within 10 seconds.")
                return  # Skip adding to the database

        # Update the last appearance time for the employee
        last_appearance_times[employee_id] = now

        # Proceed to record the appearance in the database
        appearance = Appear(
            employee_id=employee_id,
            appearance_time=current_time,
            appearance_date=current_date
        )
        db.session.add(appearance)
        db.session.commit()
        print('employee_id', employee_id)

        # Handle next actions
        process_attendance_for_employee(employee_id)

        # Track the number of appearances for the employee
        if queue_count == 0:
            # First appearance
            event_queue.put(employee_id)
            queue_count += 1
            # Directly trigger the event stream
            event_queue.put(employee_id)
        else:
            # Subsequent appearances
            if queue_count:
                event_queue.put(employee_id)
                queue_count += 1



@main.route('/Deduction', methods=['GET', 'POST'])
@login_required
def Deduction():
    # Fetch all deductions, ordered by submit date (most recent first)
    deductions = DED.query.order_by(DED.submit_date.desc()).all()

    # Define a map for converting float values to fractional representations
    fraction_map = {
        0.25: '1/4',
        0.5: '1/2',
        1.0: '1',
        2.0: '2',
        3.0: '3',
        4.0: '4',
        5.0: '5',
        6.0: '6',
        7.0: '7',
        8.0: '8',
        9.0: '9'
    }

    # Prepare report_data
    report_data = []

    for deduction in deductions:
        # Fetch the employee details
        employee = Employee.query.get(deduction.employee_id)
        if employee:
            employee_name = employee.name
        else:
            employee_name = "Unknown"

        # Get the fractional representation of the deduction points
        deduction_points_display = fraction_map.get(deduction.deduction_points, deduction.deduction_points)

        # Append data to report_data
        report_data.append({
            'id':deduction.id,
            'employee_name': employee_name,
            'reason': deduction.reason,
            'deduction_points': deduction_points_display,
            'submit_date': deduction.submit_date.strftime('%Y-%m-%d')  # Format date as needed
        })
        print(report_data)
    # Pass the report_data to the template
    return render_template('emplooye_affairs_admin/Deduction.html', report_data=report_data, user_type=current_user.user_type , user_office=current_user.office)


@main.route('/add_Deduction', methods=['GET', 'POST'])
@login_required
def add_Deduction():
    # Fetch all offices and employees
    all_offices = get_all_offices()  # Function to fetch all offices, implement as needed


    if request.method == 'POST':
        # Get form data
        employee_id = request.form.get('employee_name')  # This is actually employee.id
        reason = request.form.get('reason')
        deduction_points = request.form.get('deduction_points')
        
        try:
            # Convert deduction_points to a float
            deduction_points = float(deduction_points)

            # Insert the data into the Deduction table
            new_deduction = DED(
                reason=reason,
                deduction_points=deduction_points,
                employee_id=request.form.get('employee_name'),
                submit_date=datetime.now().date(),  # Automatically set the submit date to now
            )

            # Add to the database
            db.session.add(new_deduction)
            db.session.commit()

            flash('تم اضافة العقوبة بنجاح', 'success')
            return redirect(url_for('main.Deduction'))

        except Exception as e:
            # Handle any errors that occur during the process
            flash(f'An error occurred: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('emplooye_affairs_admin/add_Deduction.html', all_offices=all_offices, user_type=current_user.user_type , user_office=current_user.office)


@main.route('/Deduction/delete/<int:Deduction_id>', methods=['POST'])
@login_required
def delete_Deduction(Deduction_id):
    Deduction = DED.query.get_or_404(Deduction_id)
    db.session.delete(Deduction)
    db.session.commit()
    flash('تمت حذف العقوبة بنجاح!', 'success')
    return redirect(url_for('main.Deduction'))

@main.route('/tmam', methods=['GET', 'POST'])
@login_required
def tmam():
    if request.method == 'POST':
        # Retrieve form data
        report_date = request.form.get('report_date')
        type_field = request.form.get('type_field')
        period = request.form.get('period')  # Could be 'الفترة الصباحية', 'الفترة المسائية', or None

        # Generate attendance report based on the provided date and period
        attendance_report, summary_report = generate_attendance_report(report_date, period , type_field)
        report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        # Pass both attendance report and summary report to the template for rendering
        return render_template(
            'emplooye_affairs_admin/daily_tmam_report.html',
            attendance_report=attendance_report,  # Detailed employee attendance data
            summary_report=summary_report,        # Summary of the counts
            user_type=current_user.user_type,
            report_date=format_date_to_arabic(report_date)
        )
    
    # Render the form for GET requests
    return render_template('emplooye_affairs_admin/daily_tmam.html', user_type=current_user.user_type ,user_office=current_user.office)

@main.route('/mo2srat', methods=['GET', 'POST'])
@login_required
def mo2srat():
    if request.method == 'POST':
        # Retrieve form data
        office_name = request.form.get('office_name')
        employee_id = request.form.get('employee_name')  # Changed 'employee_name' to 'employee_id'
        from_date = request.form.get('date_from')
        to_date = request.form.get('date_to')
        emp_type = request.form.get('emp_type')
        report_type = request.form.get('report_type')  # Get the report type from the form
        try:
            print(employee_id)
            detailed_report, summary_report = generate_mo2srat_report(
                from_date=from_date,
                to_date=to_date,
                office=office_name,
                type = emp_type,
                employee_id=int(employee_id) if employee_id else None  # Convert employee_id to integer if provided
            )

            from_date = format_date_to_arabic(datetime.strptime(from_date, '%Y-%m-%d').date())
            to_date = format_date_to_arabic(datetime.strptime(to_date, '%Y-%m-%d').date())
            # Render the appropriate template based on the report type
            if report_type == 'count':
                # Only include summary report
                return render_template('emplooye_affairs_admin/mo2srat_report.html',summary_report=summary_report,user_type=current_user.user_type , from_date=from_date , to_date=to_date ,report_type=report_type)
            elif report_type == 'details':
                # Include both detailed and summary reports
                return render_template('emplooye_affairs_admin/mo2srat_report.html',attendance_report=detailed_report,summary_report=summary_report,user_type=current_user.user_type , from_date=from_date , to_date=to_date , report_type=report_type)
            else:
                # Handle unexpected report_type values
                flash("Invalid report type selected.", 'danger')
                return redirect(url_for('main.mo2srat'))

        except Exception as e:
            # Handle exceptions and provide feedback
            flash(f"An error occurred while generating the report: {e}", 'danger')
            return redirect(url_for('main.mo2srat'))

    # If it's a GET request, pre-populate the form with data
    all_offices = get_all_offices()  # Function to get all office names

    # Render the form template
    return render_template('emplooye_affairs_admin/mo2srat.html',all_offices=all_offices, user_type=current_user.user_type ,user_office=current_user.office)

@main.route('/attendnce_sign')
@login_required
def attendnce_sign():
    today = datetime.today().strftime('%Y-%m-%d')
    
    # Query all employees who are not on unpaid leave
    employees = Employee.query.filter(Employee.office_name != 'اجازة بدون مرتب' , Employee.active == 'ظهور').order_by(Employee.office_name).all()
    print('today',today)
    # For each employee, check if they have an attendance record for today
    attendance_records = []
    for employee in employees:
        # Check if an attendance record exists for today
        attendance = Attendance.query.filter(
            and_(
                Attendance.employee_id == employee.id,
                Attendance.date == today
            )
        ).first()
        print(attendance)
        # If no record exists for today, set check_in and check_out as None
        if attendance:
            check_in_time = attendance.check_in_time
            check_out_time = attendance.check_out_time
        else:
            check_in_time = None
            check_out_time = None
        
        attendance_records.append({
            'employee': employee,
            'check_in_time': check_in_time,
            'check_out_time': check_out_time
        })

    return render_template(
        'emplooye_affairs_admin/attendnce_sign.html', 
        attendance_records=attendance_records,
        user_type=current_user.user_type,
        user_office=current_user.office
    )
    
@main.route('/update_time', methods=['POST'])
def update_time():
    employee_id = request.form['employee_id']
    hours = int(request.form['hours'])
    minutes = int(request.form['minutes'])
    time_type = request.form['type']
    
    new_time = time(hour=hours, minute=minutes)
    current_date = datetime.today().date()
    
    # Find the specific employee record
    employee = Employee.query.get(employee_id)
    if not employee:
        flash("لم يتم العثور على الموظف", "error")
        return redirect(url_for('main.attendnce_sign'))
    
    # Find the specific attendance record for this employee
    record = Attendance.query.filter_by(employee_id=employee_id, date=current_date).first()
    
    if not record:
        # Create a new record if it doesn't exist
        record = Attendance(
            employee_id=employee_id,
            date=current_date,
            period="work"  # Default value as requested
        )
        db.session.add(record)
        flash("تم إضافة تسجيل جديد", "success")
    else:
        flash("تم تعديل التسجيل", "success")
    
    # Update the appropriate time field
    if time_type == 'check_in':
        record.check_in_time = new_time
    elif time_type == 'check_out':
        record.check_out_time = new_time
    
    # Save the record to the database
    db.session.commit()
    
    # Redirect back to the attendance sign page
    return redirect(url_for('main.attendnce_sign'))

@main.route('/delete_attendence/<int:employee_id>', methods=['POST'])
@login_required
def delete_attendence(employee_id):
    # Get today's date
    today = datetime.today().date()

    # Find the attendance record for the given employee and today's date
    attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()

    if attendance:
        try:
            # Delete the attendance record
            db.session.delete(attendance)
            db.session.commit()

            # Flash a success message
            flash('تم حذف تسجيل الحضور بنجاح.', 'success')
        except Exception as e:
            # If there's an error, rollback and flash an error message
            db.session.rollback()
            flash('حدث خطأ أثناء حذف تسجيل الحضور.', 'danger')
    else:
        # Flash a message if no attendance record is found for today
        flash('لا يوجد تسجيل حضور لهذا الموظف اليوم.', 'danger')

    # Redirect back to the attendance page or another relevant page
    return redirect(url_for('main.attendnce_sign'))

@main.route('/users')
@login_required
def users():

    users = User.query.order_by(
        case(
            (User.user_type == 'admin', 1),
            (User.user_type == 'manager', 2),
            (User.user_type == 'employee', 3),
            else_=4
        )
    ).all()
    return render_template('emplooye_affairs_admin/users.html', user_type=current_user.user_type, user_office=current_user.office , users=users)

@main.route('/add_user', methods=['GET', 'POST'])
@main.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_or_edit_user(user_id=None):
    print(f"Received request: user_id={user_id}")

    if user_id:
        user = User.query.get_or_404(user_id)
        form = UserForm(current_user_id=user.id, obj=user)
        print("Editing existing user")
        
        # Store original values for comparison
        original_values = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'name': user.name,
            'office': user.office,
            'user_type': user.user_type,
            # Photo is handled separately
        }
    else:
        user = None
        form = UserForm()
        print("Adding new user")

    if form.validate_on_submit():
        print("Form is valid, processing user data")

        if not user:
            print("Creating new user")
            user = User(
                id=form.id.data,  # Use provided ID
                email=form.email.data,
                username=form.username.data,
                user_type=form.user_type.data,
                name=form.name.data,
                office=form.office.data
            )
            user.password_hash = bcrypt.generate_password_hash(form.password.data)
        else:
            print("Updating existing user")
            # Update fields conditionally based on whether they've changed
            if form.id.data != original_values['id']:
                user.id = form.id.data  # Update User ID if changed

            if form.email.data != original_values['email']:
                user.email = form.email.data  # Update Email if changed
            
            # Update password only if a new one is provided
            if form.password.data:
                user.password_hash = bcrypt.generate_password_hash(form.password.data)
            
            # Always update these fields regardless of change
            user.username = form.username.data
            user.name = form.name.data
            user.office = form.office.data
            user.user_type = form.user_type.data



        db.session.add(user)
        db.session.commit()
        flash(f'User {"added" if not user_id else "updated"} successfully', 'success')
        print(f"User {'added' if not user_id else 'updated'}: {user}")
        return redirect(url_for('main.users'))

    print(f"Form validation failed with errors: {form.errors}")
    return render_template('emplooye_affairs_admin/add_users.html', form=form, user=user, user_type=current_user.user_type, user_office=current_user.office)

@main.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):

    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash(f"بنجاح  {user.name}  تم حذف ", "success")
    return redirect(url_for('main.users'))

@main.route('/employee_rates', methods=['GET', 'POST'])
@login_required
def employee_rates():
    if request.method == 'GET':
        user_office = current_user.office
        employees_data = Employee.query.filter_by(office_name=user_office, active='ظهور').all()
        employees =employees_data if employees_data else None
        for employee in employees:

            rates_count = EmployeeRates.query.filter_by(employee_id=employee.employment_id).count()

            if rates_count > 1:
                # If more than one rate exists, use the offset to get the second-to-last rate
                last_rate = EmployeeRates.query.filter_by(employee_id=employee.employment_id) \
                                            .order_by(EmployeeRates.id.desc()) \
                                            .limit(1) \
                                            .offset(1) \
                                            .first()
            else:
                # If there is only one rate, fetch the last rate directly without offset
                last_rate = EmployeeRates.query.filter_by(employee_id=employee.employment_id) \
                                            .order_by(EmployeeRates.id.desc()) \
                                            .first()
            employee.last_rate = last_rate.rate if last_rate else None
            
        return render_template('emplooye_affairs_admin/employee_rates.html', employees=employees ,   user_type=current_user.user_type, user_office=current_user.office )
    
    elif request.method == 'POST':
        data = request.json
        rates = data.get('rates', [])
        print('data_of_rates' , data)
        print('rates_of_rates' , rates)
        try:
            for rate_data in rates:
                employee_id = rate_data['employee_id']
                rate = rate_data['rate']
                
                if rate:  # Only create a new rate if a value was provided
                    new_rate = EmployeeRates(
                        employee_id=employee_id,
                        rate=float(rate),
                        submit_date=datetime.now().date()
                    )
                    db.session.add(new_rate)
            
            db.session.commit()
            return jsonify({'success': True}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error saving rates: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500