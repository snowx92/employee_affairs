from typing import Optional
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import FieldList, FileField, FormField, StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, IntegerField, HiddenField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp , Optional
from datetime import datetime
from flask_wtf.file import FileAllowed

from app.models import User
time_choices = [
    (f'{hour:02d}:{minute:02d}', f'{hour:02d}:{minute:02d}')
    for hour in range(8, 25)
    for minute in (0, 15, 30, 45)
]
class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('البريد الالكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('انشاء حساب')

class LoginForm(FlaskForm):
    email = StringField('البريد الالكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكرني ')
    submit = SubmitField('تسجيل الدخول')

class EmployeeForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])


    job_start_time = StringField('موعد الحضور (HH:MM)', validators=[DataRequired(), Regexp(r'^\d{2}:\d{2}$', message="Invalid time format. Use HH:MM.")])
    job_end_time = StringField('موعد الانصراف (HH:MM)', validators=[DataRequired(), Regexp(r'^\d{2}:\d{2}$', message="Invalid time format. Use HH:MM.")])
    sat = BooleanField('السبت')
    sun = BooleanField('الاحد')
    mon = BooleanField('الاتنين')
    tues = BooleanField('الثلاثاء')
    wed = BooleanField('الاربعاء')
    thr = BooleanField('الخميس')
    fri = BooleanField('الجمعة')
    certificate = StringField('الشهادة الجامعية', validators=[DataRequired()])
    graduation_year = SelectField('سنة التخرج', choices=[(str(year), str(year)) for year in range(1950, datetime.now().year + 1)], validators=[DataRequired()])
    grade = SelectField(
        'درجة الموظف', 
        choices=[
            ('الأولى', 'الأولى'),
            ('الثانية', 'الثانية'),
            ('الثالثة', 'الثالثة'),
            ('الرابعة', 'الرابعة'),
            ('الخامسة', 'الخامسة'),
            ('السادسة', 'السادسة'),
        ], 
        validators=[DataRequired()]
    )
    level = SelectField('مستوى الموظف', choices=[('أ','أ') , ('ب','ب') , ('ج','ج')], validators=[DataRequired()])
    employment_start_year = DateField('تاريخ التوظيف', format='%Y-%m-%d', validators=[DataRequired()])
    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),  ('الامتحانات المدنية', 'الامتحانات المدنية'),('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), ('الحسابات', 'الحسابات'), 
        ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), 
        ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')], validators=[DataRequired()])
    period = SelectField('الفتره', choices=[('الفترة الصباحية', 'الفترة الصباحية'), ('الفترة المسائية', 'الفترة المسائية')], validators=[DataRequired()])
    period_id = HiddenField('Period ID')
    employment_id = StringField('الموظف ID', validators=[DataRequired()])
    nat_id = StringField('الرقم القومي', validators=[DataRequired()])
    name = StringField('الاسم', validators=[DataRequired()])
    birth_date = DateField('تاريخ الميلاد', format='%Y-%m-%d', validators=[DataRequired()])
    address = StringField('العنوان', validators=[DataRequired()])
    phone_number = StringField('رقم الهاتف', validators=[DataRequired()])
    sec_phone_number = StringField('رقم هاتف اخر', validators=[DataRequired()])
    gender = SelectField('الجنس', choices=[('ذكر', 'ذكر'), ('انثي', 'انثي')], validators=[DataRequired()])
    exp = StringField('الخبرة (عدد السنين)', validators=[DataRequired()])
    exp_type = SelectField('نوع المؤهل', choices=[('عالى', 'عالى'), ('فوق متوسط', 'فوق متوسط') ,('بدون مؤهل', 'بدون مؤهل'), ('متوسط', 'متوسط')], validators=[DataRequired()])
    social = SelectField('الحالة الاجتماعية', choices=[('اعزب', 'اعزب'), ('متزوج', 'متزوج'),('متزوج ويعول', 'متزوج ويعول'), ('ارمل', 'ارمل')], validators=[DataRequired()])
    religion = SelectField('الديانة', choices=[('مسلم', 'مسلم'), ('مسيحي', 'مسيحي')], validators=[DataRequired()])
    job_name_modli = SelectField('الوظيفة ',choices=[('مُدخل بيانات', 'مُدخل بيانات'),('اخصائى شئون مالية', 'اخصائى شئون مالية'),('كاتب شئون مالية', 'كاتب شئون مالية'),('اخصائى خدمة اجتماعية', 'اخصائى خدمة اجتماعية'),('مُترجم', 'مُترجم'),('مُدرس', 'مُدرس'),('محاسب', 'محاسب'),('مُصمم جرافيك', 'مُصمم جرافيك'),('باحث نظم', 'باحث نظم'),('عامل نظافة', 'عامل نظافة'),('ترزى', 'ترزى'),('فنى كهرباء', 'فنى كهرباء'),('فنى طباعة', 'فنى طباعة'),('فنى زخرفة', 'فنى زخرفة'),('فنى تغذية', 'فنى تغذية'),('نجّار', 'نجّار'),('كاتب شئون ادارية', 'كاتب شئون ادارية'),('اخصائى متابعة', 'اخصائى متابعة'),('مدرسة', 'مدرسة'),('فنى ألوميتال', 'فنى ألوميتال'),('نائب رئيس شئون العاملين', 'نائب رئيس شئون العاملين'),('حلاق', 'حلاق'),('سبّاك', 'سبّاك'),('شئون ادارية', 'شئون ادارية'),('ادارة خدمة معاونة', 'ادارة خدمة معاونة') , ('باحث شئون عاملين', 'باحث شئون عاملين') , ('باحث تنظيم وادارة', 'باحث تنظيم وادارة') , ('باحث تنظيم', 'باحث تنظيم') , ('اخصائي شئون قانونية', 'اخصائي شئون قانونية')], validators=[DataRequired()])

    job_type = SelectField('المجموعة الوظيفية', choices=[('اداري', 'اداري'), ('قائم بالتدريس', 'قائم بالتدريس'), ('تخصصي', 'تخصصي') , ('فني', 'فني') , ('كتابي', 'كتابي'), ('حرفي', 'حرفي'), ('خدمة معاونة', 'خدمة معاونة')], validators=[DataRequired()])
    emp_type = SelectField('نوع التعاقد', choices=[('عقد', 'عقد'), ('معين', 'معين')], validators=[DataRequired()])
    contract_start_date = DateField('تاريخ بداية العقد', format='%Y-%m-%d', validators=[Optional()])
    contract_end_date = DateField('تاريخ نهاية العقد', format='%Y-%m-%d', validators=[Optional()])
    arda_points = IntegerField('النقاط العارضة')
    sanwya_points = IntegerField('النقاط الاعتيادية')
    tar7eel_points = IntegerField('النقاط المرحلة')
    doc_number = IntegerField('رقم الملف', validators=[DataRequired()])
    insurance_number = IntegerField('رقم التأمين', validators=[DataRequired()])
    active = SelectField('اخفاء الموظف', choices=[('اخفاء','اخفاء') , ('ظهور','ظهور')  ], validators=[DataRequired()])
    submit = SubmitField('اضافة موظف')


class HolidayForm(FlaskForm):
    name = StringField('اسم الاجازة', validators=[DataRequired()])
    from_date = DateField('من', format='%Y-%m-%d', validators=[DataRequired()])
    to_date = DateField('الي', default=datetime.today , format='%Y-%m-%d', validators=[DataRequired()])
    type = SelectField('النوع', choices=[('نصف يوم', 'نصف يوم'), ('يوم كامل', 'يوم كامل')], validators=[DataRequired()])
    submit = SubmitField('انشاء')
    

class UserSettingsForm(FlaskForm):

    name = StringField('الاسم', validators=[Optional(), Length(max=100)])
    password = PasswordField('كلمة المرور الجديدة', validators=[Optional(), Length(min=6)])
    photo = FileField('صورة الملف الشخصي', validators=[Optional()])
    submit = SubmitField('حفظ التغييرات')
    
class DateForm(FlaskForm):
    date = DateField('التاريخ', default=datetime.today , format='%Y-%m-%d', validators=[DataRequired()])
        
class JobScheduleOverrideForm(FlaskForm):
    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'), ('الامتحانات المدنية', 'الامتحانات المدنية'),('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), ('الحسابات', 'الحسابات'), 
        ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), 
        ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')], validators=[DataRequired()])
    
    employee_name = SelectField('اسم الموظف', choices=[], coerce=int, validators=[DataRequired()])
    dates = StringField('التاريخ', validators=[DataRequired()])
    # Hours SelectField (1-24)
    job_start_hour = SelectField(
        'ساعة الحضور (HH)',
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(1, 25)],
        validators=[DataRequired()]
    )
    # Minutes SelectField (0-59)
    job_start_minute = SelectField(
        'دقائق الحضور (MM)',
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(0, 60)],
        validators=[DataRequired()]
    )

    # Hours SelectField (1-24)
    job_end_hour = SelectField(
        'ساعة الانصراف (HH)',
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(1, 25)],
        validators=[DataRequired()]
    )
    # Minutes SelectField (0-59)
    job_end_minute = SelectField(
        'دقائق الانصراف (MM)',
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(0, 60)],
        validators=[DataRequired()]
    )
    submit = SubmitField('انشاء')
    
class EznForm(FlaskForm):
    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),('الامتحانات المدنية', 'الامتحانات المدنية'), ('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), ('الحسابات', 'الحسابات'), 
        ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), 
        ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')], validators=[DataRequired()])
        
    employee_name = SelectField('اسم الموظف', choices=[], coerce=int, validators=[DataRequired()])
    date = DateField('التاريخ', format='%Y-%m-%d', default=datetime.today , validators=[DataRequired()])
    from_time = SelectField('من الوقت (HH:MM)', choices=time_choices, validators=[DataRequired()])
    to_time = SelectField('إلى الوقت (HH:MM)', choices=time_choices, validators=[DataRequired()])
        
    submit = SubmitField('إرسال')
    
class ClinicForm(FlaskForm):
    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),('الامتحانات المدنية', 'الامتحانات المدنية'), ('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), ('الحسابات', 'الحسابات'), 
        ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), 
        ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')], validators=[DataRequired()])
    
    employee_name = SelectField('اسم الموظف', choices=[], coerce=int, validators=[DataRequired()])
    
    clinic_type = SelectField('نوع العيادة', choices=[
        ('أسنان', 'أسنان'), ('جلدية', 'جلدية'), ('عمود فقرى', 'عمود فقرى'), 
        ('عيون', 'عيون'), ('باطنة', 'باطنة'), ('مخ وأعصاب', 'مخ وأعصاب'), 
        ('صدر', 'صدر'), ('جهاز تنفسى', 'جهاز تنفسى'), ('عظام', 'عظام'), 
        ('رمد', 'رمد'), ('مسالك بولية', 'مسالك بولية'), ('أنف وأذن وحنجرة', 'أنف وأذن وحنجرة'),
        ('كلي', 'كلي'), ('نفسية', 'نفسية') ,('اختياري', 'اختياري')
    ], validators=[DataRequired()])
    
    date = DateField('التاريخ', format='%Y-%m-%d', default=datetime.today , validators=[DataRequired()])
    
    submit = SubmitField('إرسال')  
    
class MomryaForm(FlaskForm):
    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),('الامتحانات المدنية', 'الامتحانات المدنية'), ('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), ('الحسابات', 'الحسابات'), 
        ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), 
        ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')], validators=[DataRequired()])
    
    employee_name = SelectField('اسم الموظف', choices=[], coerce=int, validators=[DataRequired()])
    
    reason = TextAreaField('سبب المأمورية', validators=[DataRequired()])
    
    date = DateField('من', format='%Y-%m-%d', default=datetime.today , validators=[DataRequired()])
    to_date = DateField('الي', format='%Y-%m-%d', default=datetime.today , validators=[DataRequired()])
    
    submit = SubmitField('إرسال')        
    
class AltmasForm(FlaskForm):
    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),('الامتحانات المدنية', 'الامتحانات المدنية'), ('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), ('الحسابات', 'الحسابات'), 
        ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), 
        ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')], validators=[DataRequired()])
    
    employee_name = SelectField('اسم الموظف', choices=[], coerce=int, validators=[DataRequired()])
    
    petition = TextAreaField('الرسالة', validators=[DataRequired()])
    
    submit = SubmitField('إرسال')    


    

class AgazaForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(AgazaForm, self).__init__(*args, **kwargs)
        # Set choices for agaza_type based on current_user
        self.set_agaza_choices()

    office_name = SelectField('المكتب التابع له', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), 
        ('شئون الدارسين', 'شئون الدارسين'),
        ('التخطيط', 'التخطيط'),
        ('المكتبة', 'المكتبة'),
        ('اللغة العبريه', 'اللغة العبريه'),
        ('الشئون الفنية', 'الشئون الفنية'),
        ('الاجنحه التعليمية', 'الاجنحه التعليمية'),
        ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'),
        ('اللغة العربية', 'اللغة العربية'),
        ('الدورات التعليمية', 'الدورات التعليمية'),
        ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),
        ('الامتحانات المدنية', 'الامتحانات المدنية'),
        ('التطوير', 'التطوير'),
        ('السكرتارية', 'السكرتارية'),
        ('الحسابات', 'الحسابات'),
        ('متابعة المدير', 'متابعة المدير'),
        ('الامن والاستعلامات', 'الامن والاستعلامات'),
        ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'),
        ('الترجمة المدنية', 'الترجمة المدنية'),
        ('قسم الجودة', 'قسم الجودة'),
        ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'),
        ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'),
        ('اجازة بدون مرتب', 'اجازة بدون مرتب'),
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')
    ], validators=[DataRequired()])
    
    
    employee_name = SelectField('اسم الموظف', choices=[], coerce=int, validators=[DataRequired()])
    alternative = SelectField('الموظف البديل', choices=[], coerce=int, validators=[DataRequired()])
    
    from_date = DateField('من تاريخ', 
                         format='%Y-%m-%d', 
                         default=datetime.today, 
                         validators=[DataRequired()])
    
    to_date = DateField('إلى تاريخ', 
                       format='%Y-%m-%d', 
                       validators=[DataRequired()])
    
    agaza_type = SelectField('نوع الاجازة', 
                            choices=[], 
                            validators=[DataRequired()],
                            id='agaza_type')  # Explicit ID
                            
    impact_type = SelectField('نوع التأثير', 
                            choices=[ ('غير مؤثر', 'غير مؤثر') ,('مؤثر', 'مؤثر')],
                            validators=[Optional()],
                            id='impact_type')  # Explicit ID
    notes_agaza = TextAreaField('ملا حظات الاجازةً')
    submit = SubmitField('إرسال')

    def set_agaza_choices(self):
        base_choices = [
            ('أعتيادية', 'أعتيادية'),
            ('عارضة', 'عارضة'),
            ('مرضي', 'مرضي'),
            ('بدون مرتب', 'بدون مرتب'),
            ('بالخصم', 'بالخصم'),
            ('وضع', 'وضع'),
            ('فرقة', 'فرقة'),
            ('مأمورية', 'مأمورية'),
            ('انتداب', 'انتداب'),
            ('حجز في المستشفي', 'حجز في المستشفي'),
            ('اجازة بدل انصراف', 'اجازة بدل انصراف')
        ]
        
        try:
            if current_user.is_authenticated and hasattr(current_user, 'user_type'):
                if current_user.user_type == 'admin':
                    base_choices.append(('منحة', 'منحة'))
        except Exception as e:
            print(f"Error accessing current_user: {e}")
            
        self.agaza_type.choices = base_choices

    def validate_to_date(self, field):
        if self.from_date.data > field.data:
            raise ValidationError('يجب أن يكون تاريخ "من" أقل من تاريخ "إلى".')

class UserForm(FlaskForm):
    id = IntegerField('User ID', validators=[DataRequired()])

    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])

    password = PasswordField('Password', validators=[Length(min=6, max=100)])

    username = StringField('Username', validators=[DataRequired(), Length(max=50)])

    user_type = SelectField('User Type', choices=[('employee', 'موظف'), ('manager', 'رئيس فرع'), ('admin', 'إدارة')], validators=[DataRequired()])

    name = StringField('Name', validators=[DataRequired(), Length(max=100)])

    office = SelectField('Office', choices=[
        ('تشغيل الحواسب', 'تشغيل الحواسب'), ('شئون الدارسين', 'شئون الدارسين'), ('التخطيط', 'التخطيط'), ('المكتبة', 'المكتبة'), 
        ('اللغة العبريه', 'اللغة العبريه'), ('الشئون الفنية', 'الشئون الفنية'), ('الاجنحه التعليمية', 'الاجنحه التعليمية'), ('خدمة معاونة', 'خدمة معاونة'),
        ('المطبعة', 'المطبعة'), ('اللغة العربية', 'اللغة العربية'), ('الدورات التعليمية', 'الدورات التعليمية'), ('الترجمة', 'الترجمة'),
        ('الامتحانات العسكرية', 'الامتحانات العسكرية'),  ('الامتحانات المدنية', 'الامتحانات المدنية'), ('التطوير', 'التطوير'), ('السكرتارية', 'السكرتارية'), 
        ('الحسابات', 'الحسابات'), ('متابعة المدير', 'متابعة المدير'), ('الامن والاستعلامات', 'الامن والاستعلامات'), 
        ('شئون العاملين المدنيين', 'شئون العاملين المدنيين'), ('الترجمة المدنية', 'الترجمة المدنية'), ('قسم الجودة', 'قسم الجودة'), 
        ('اركان حرب مبنى 1', 'اركان حرب مبنى 1'), ('اركان حرب مبنى 3', 'اركان حرب مبنى 3'), ('اجازة بدون مرتب', 'اجازة بدون مرتب'), 
        ('انتداب خارج وزارة الدفاع', 'انتداب خارج وزارة الدفاع')
    ], validators=[DataRequired()])

    photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])

    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        self.current_user_id = kwargs.pop('current_user_id', None)
        super(UserForm, self).__init__(*args, **kwargs)

    # Custom validation for unique user ID
    def validate_id(self, id):
        # For new users, just check if ID already exists
        if self.current_user_id is None:
            if User.query.filter_by(id=id.data).first():
                raise ValidationError('This User ID already exists. Please choose a different one.')
        else:
            # For existing users, ignore validation if it's the user's own ID
            if id.data != self.current_user_id and User.query.filter_by(id=id.data).first():
                raise ValidationError('This User ID already exists. Please choose a different one.')

    # Custom validation for unique email
    def validate_email(self, email):
        # Check if this is a new user (self.current_user_id is None)
        if self.current_user_id is None:
            # For new users, just check if email already exists
            if User.query.filter_by(email=email.data).first():
                raise ValidationError('This email is already in use. Please choose a different one.')
        else:
            # For existing users, ignore validation if it's the user's own email
            current_user = User.query.get(self.current_user_id)
            if current_user and email.data != current_user.email and User.query.filter_by(email=email.data).first():
                raise ValidationError('This email is already in use. Please choose a different one.')



