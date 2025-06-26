# API Documentation

This document provides details about all the API endpoints available in the Employee Affairs Administration System.

## Table of Contents

1. [Authentication APIs](#authentication-apis)
   - [POST /register](#post-register)
   - [POST /login](#post-login)
   - [GET /logout](#get-logout)

2. [Request Management APIs](#request-management-apis)
   - [GET /api/requests_data](#get-apirequests_data)
   - [POST /api/handle_request_action](#post-apihandle_request_action)
   - [POST /api/update_request/:request_type/:request_id](#post-apiupdate_requestrequest_typerequest_id)
   - [GET /load_form/:report_type](#get-load_formreport_type)
   - [POST /add_request](#post-add_request)
   - [GET /requests_veiws.html](#get-requests_viewshtml)
   - [GET /report_clinic_on_submit](#get-report_clinic_on_submit)
   - [GET /report_momrya_on_submit](#get-report_momrya_on_submit)
   - [GET /report_ezn_on_submit](#get-report_ezn_on_submit)
   - [GET /report_agaza_on_submit](#get-report_agaza_on_submit)
   - [GET /report_altmas_on_submit](#get-report_altmas_on_submit)

3. [Employee Management APIs](#employee-management-apis)
   - [POST /add_employee](#post-add_employee)
   - [POST /delete_employee/:employee_id](#post-delete_employeeemployee_id)
   - [GET /employee_rates](#get-employee_rates)
   - [GET /employee_history/:employee_id](#get-employee_historyemployee_id)

4. [Employee Information APIs](#employee-information-apis)
   - [GET /api/employee_info/:employee_id](#get-apiemployee_infoemployee_id)
   - [GET /get_employee_schedule/:employee_id](#get-get_employee_scheduleemployee_id)
   - [GET /get_employees/:office](#get-get_employeesoffice)

5. [Report Generation APIs](#report-generation-apis)
   - [POST /api/report_count](#post-apireport_count)
   - [POST /employee_report_ajax](#post-employee_report_ajax)
   - [POST /generate_employee_report_pdf](#post-generate_employee_report_pdf)
   - [GET /employee_history_pdf/:employee_id/:report_type](#get-employee_history_pdfemployee_idreport_type)
   - [POST /generate_print_report](#post-generate_print_report)
   - [GET /employee_report](#get-employee_report)
   - [GET /admin/reports](#get-adminreports)
   - [GET /reports](#get-reports)

6. [Attendance Management APIs](#attendance-management-apis)
   - [GET /video_feed](#get-video_feed)
   - [GET /recognized_id_feed](#get-recognized_id_feed)
   - [POST /update_time](#post-update_time)
   - [POST /delete_attendence/:employee_id](#post-delete_attendenceemployee_id)
   - [GET /face-recognition](#get-face-recognition)
   - [GET /attendnce_sign](#get-attendnce_sign)
   - [GET /tmam](#get-tmam)
   - [GET /mo2srat](#get-mo2srat)

7. [Schedule Management APIs](#schedule-management-apis)
   - [GET /official_holidays](#get-official_holidays)
   - [POST /add_official_holidays](#post-add_official_holidays)
   - [POST /official_holidays/edit/:holiday_id](#post-official_holidayseditholiday_id)
   - [POST /holidays/delete/:holiday_id](#post-holidaysdeleteholiday_id)
   - [POST /add_job_schedule_override](#post-add_job_schedule_override)
   - [GET /job_schedule_override](#get-job_schedule_override)
   - [POST /delete_job_schedule_override/:override_id](#post-delete_job_schedule_overrideoverride_id)

8. [Deduction Management APIs](#deduction-management-apis)
   - [GET /Deduction](#get-deduction)
   - [POST /add_Deduction](#post-add_deduction)
   - [POST /Deduction/delete/:Deduction_id](#post-deductiondeletededuction_id)

9. [User Management APIs](#user-management-apis)
   - [GET /users](#get-users)
   - [POST /add_user](#post-add_user)
   - [POST /edit_user/:user_id](#post-edit_useruser_id)
   - [POST /delete_user/:user_id](#post-delete_useruser_id)

10. [Admin Dashboard APIs](#admin-dashboard-apis)
    - [GET /admin_dashboard](#get-admin_dashboard)
    - [GET /settings](#get-settings)
    - [GET /admin_users](#get-admin_users)

11. [Helper Functions](#helper-functions)
    - [Report Generation Helpers](#report-generation-helpers)
    - [Attendance Management Helpers](#attendance-management-helpers)
    - [Leave Management Helpers](#leave-management-helpers)
    - [Utility Helpers](#utility-helpers)

---

## Authentication APIs

### POST /register

Registers a new user in the system.

**Request Body (Form Data):**
```
username: "admin_user"
password: "secure_password"
password2: "secure_password" (confirmation)
```

**Response:**
- If successful: Redirects to the login page with success message
- If unsuccessful: Renders the registration form with error messages

**Notes:**
- Registration is restricted to admin users only
- Passwords must match and meet security requirements
- Username must be unique in the system

### POST /login

Authenticates a user and creates a session.

**Request Body (Form Data):**
```
username: "admin_user"
password: "secure_password"
remember_me: True/False
```

**Response:**
- If successful: Redirects to the appropriate dashboard based on user type
- If unsuccessful: Renders the login form with error messages

**Notes:**
- Checks if the user exists and the password is correct
- Sets remember_me cookie if requested
- Tracks the last login time

### GET /logout

Logs out the current user by removing the session.

**Response:**
- Redirects to the login page

**Notes:**
- Requires authentication (login_required)
- Clears the user session

## Request Management APIs

### GET /api/requests_data

Retrieves request data for different request types, filtered by date and user permissions.

**Parameters:**
- `filter_date` (Query Parameter, Optional): Date to filter requests (format: YYYY-MM-DD)
- `request_type` (Query Parameter, Optional): Type of request to filter ('clinic', 'ezn', 'agaza', 'altmas', 'momrya')

**Response:**
```json
{
  "clinic": [
    {
      "req_type": "clinic",
      "id": 123,
      "approval_id": 456,
      "approval_status_message": "موافقة المكتب: موافق",
      "employee_id": 789,
      "office_manager_approval_status": "Approved",
      "secretary_approval_status": "Pending",
      "president_follower_approval_status": "Pending",
      "employee_affairs_approval_status": "Pending",
      "vice_president_approval_status": "Pending",
      "president_approval_status": "Pending",
      "data": {
        "date": "2023-01-01",
        "clinic_type": "نوع العيادة",
        "diagnosis": "تشخيص العيادة",
        "out_time": "10:30:00",
        "back_time": "12:30:00",
        "submit_date": "2023-01-01",
        "employee_name": "اسم الموظف",
        "job_title": "وظيفة",
        "employee_office": "مكتب",
        "approval_status": "Approved"
      }
    }
  ],
  "ezn": [...],
  "agaza": [...],
  "altmas": [...],
  "momrya": [...]
}
```

**Notes:**
- Returns an object with keys for each request type
- Each request type contains an array of request objects
- Request data is filtered based on the user's role and office
- If a specific request type is provided, only data for that type is returned
- Without a filter date, defaults to today's date

### POST /api/handle_request_action

Handles approval, rejection, or deletion of request items.

**Request Body:**
```json
{
  "approval_id": 123,
  "action_type": "approve" // or "reject" or "delete"
}
```

**Response for Approval/Rejection:**
```json
{
  "status": "success",
  "message": "Request approved successfully.",
  "action_type": "approve",
  "approval_id": 123,
  "stage": "office_manager_approval_status",
  "new_status": "Approved"
}
```

**Response for Deletion:**
```json
{
  "status": "success",
  "message": "Request deleted successfully.",
  "action_type": "delete",
  "approval_id": 123,
  "points_returned": false,
  "agaza_duration": 0
}
```

**Notes:**
- For leave (agaza) requests, when deleted, the API calculates and returns any leave points
- The stages for approval follow a specific order: office manager → employee affairs → secretary → vice president → president follower → president
- Each approval moves the request to the next stage
- Rejection can happen at any stage

### POST /api/update_request/:request_type/:request_id

Updates specific fields of a request.

**URL Parameters:**
- `request_type`: Type of request ('agaza', 'momrya', 'ezn', 'clinic', 'altmas')
- `request_id`: ID of the approval record

**Request Body:**
```json
{
  "field": "to_date", // Field to update
  "value": "2023-01-15" // New value
}
```

**Response:**
```json
{
  "success": true
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message"
}
```

**Supported Fields by Request Type:**
- All types: 
  - `notes_agaza`, `notes_agaza_manager`, `diagnosis` (text fields)
- Time fields (`out_time`, `back_time`): Format: "HH:MM"
- Date fields (`from_date`, `to_date`): Format: "YYYY-MM-DD"

**Special Handling:**
- For `agaza` type with `to_date` field:
  - Calculates the change in duration
  - Adjusts employee leave points based on leave type
  - Ensures employees have enough points when extending leave

### POST /add_request

Creates a new request of various types (clinic, mission, permission, leave, petition).

**Request Body (Form Data):**
Varies based on request type:

**Clinic Request:**
```
report_type: "clinic"
employee_id: "123"
clinic_type: "نوع العيادة"
diagnosis: "تشخيص العيادة"
date: "2023-01-01"
out_time: "10:00"
back_time: "12:00"
```

**Mission Request:**
```
report_type: "momrya"
employee_id: "123"
momrya_type: "نوع المأمورية" 
from_date: "2023-01-01"
to_date: "2023-01-02"
```

**Permission Request:**
```
report_type: "ezn"
employee_id: "123"
ezn_type: "نوع الإذن"
date: "2023-01-01"
out_time: "10:00"
back_time: "12:00"
```

**Leave Request:**
```
report_type: "agaza"
employee_id: "123"
agaza_type: "نوع الإجازة"
from_date: "2023-01-01"
to_date: "2023-01-05"
```

**Petition Request:**
```
report_type: "altmas"
employee_id: "123"
altmas_type: "نوع الالتماس"
from_date: "2023-01-01"
to_date: "2023-01-02"
```

**Response:**
- If successful: Redirects to the appropriate report submission page
- If unsuccessful: Returns error messages

**Notes:**
- Requires authentication (login_required)
- Validates input data based on request type
- Creates appropriate database records and approval workflow

### GET /requests_veiws.html

Displays a page for viewing and managing requests.

**Response:**
- HTML page displaying request views

**Notes:**
- Requires authentication (login_required)
- Interface for interacting with requests of all types

### GET /report_clinic_on_submit
### GET /report_momrya_on_submit
### GET /report_ezn_on_submit
### GET /report_agaza_on_submit
### GET /report_altmas_on_submit

Series of endpoints that handle the successful submission of various request types.

**Query Parameters:**
- `report_data`: JSON string with serialized report data

**Response:**
- HTML page displaying confirmation of request submission with details

**Notes:**
- These endpoints are typically accessed via redirect after successful request submission
- Display formatted version of the submitted request data
- Include options for printing the request

## Employee Information APIs

### GET /api/employee_info/:employee_id

Retrieves basic information about an employee.

**URL Parameters:**
- `employee_id`: ID of the employee

**Response:**
```json
{
  "id": 123,
  "name": "اسم الموظف",
  "office_name": "اسم المكتب",
  "period": "الفترة الصباحية",
  "job_name_modli": "المسمى الوظيفي"
}
```

**Error Response:**
```json
{
  "error": "Error message"
}
```

**Notes:**
- Requires authentication (login_required)
- Returns 500 error if employee not found or other server error occurs

### GET /get_employee_schedule/:employee_id

Retrieves an employee's working schedule.

**URL Parameters:**
- `employee_id`: ID of the employee

**Response:**
```json
{
  "id": 123,
  "job_start_time": "08:00",
  "job_end_time": "15:00",
  "name": "اسم الموظف"
}
```

**Error Response:**
```json
{
  "error": "Employee not found or does not belong to your office"
}
```

**Notes:**
- Requires authentication (login_required)
- Non-admin users can only access employees in their own office
- Returns job schedule times for the employee

### GET /get_employees/:office

Retrieves all employees for a specific office.

**URL Parameters:**
- `office`: Name of the office

**Response:**
```json
[
  {
    "id": 123,
    "name": "اسم الموظف",
    "period": "الفترة الصباحية"
  },
  {
    "id": 124,
    "name": "اسم الموظف 2",
    "period": "الفترة المسائية"
  }
]
```

**Error Response:**
```json
{
  "error": "An error occurred while fetching employees for office 'office_name': error message"
}
```

**Notes:**
- Requires authentication (login_required)
- Returns only active employees (active='ظهور')
- Includes employee ID, name, and work period

## Report Generation APIs

### POST /api/report_count

Retrieves the count of records for various report types based on specified criteria.

**Request Body:**
```json
{
  "report_type": "absent", // or other report types
  "date_from": "2023-01-01",
  "date_to": "2023-01-31",
  "employee_id": 123, // optional
  "office": "اسم المكتب" // optional
}
```

**Response:**
```json
{
  "count": 15
}
```

**Error Response:**
```json
{
  "count": 0,
  "error": "An error occurred while getting the report count"
}
```

**Supported Report Types:**
- `absent`: Absent employees
- `check_in_attendance`: Check-in attendance records
- `check_in_delays`: Delayed check-ins
- `check_out_attendance`: Check-out attendance records
- `check_out_ahead`: Early check-outs
- `no_check_out`: Missing check-outs
- `rased`: Rased records
- `ezn`: Permission records
- `agaza`: Leave records
- `clinic`: Clinic visit records
- `altmas`: Petition records
- `rest`: Rest day records
- `check_all`: All attendance records
- `momrya`: Mission records

**Notes:**
- Requires authentication (login_required)
- The count is based on the number of records that match the criteria
- For efficiency, uses count_only=True parameter when possible

### POST /employee_report_ajax

Retrieves detailed report data for employees based on specified criteria (AJAX endpoint).

**Request Body (Form Data):**
```
report_type: "absent" // or other report types
date_from: "2023-01-01"
date_to: "2023-01-31"
employee_name: "123" // employee ID
```

**Response:**
```json
{
  "success": true,
  "report_type": "absent",
  "report_data": [
    {
      // Record details vary by report_type
      "employee_name": "اسم الموظف",
      "date": "2023-01-05",
      // Additional fields...
    }
  ],
  "count": 5
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "report_data": []
}
```

**Notes:**
- Requires authentication (login_required)
- Same report types supported as in `/api/report_count`
- Returns detailed record data, not just count
- Filters by user's office if current user is not an admin

### POST /generate_employee_report_pdf

Redirects to a PDF-formatted report page for employee data.

**Request Body (Form Data):**
```
report_type: "absent" // or other report types
date_from: "2023-01-01"
date_to: "2023-01-31"
employee_id: "123"
```

**Response:**
- Redirects to `/employee_report` with parameters and format=pdf

**Notes:**
- Requires authentication (login_required)
- Used to generate PDF reports
- Supports the same report types as other reporting endpoints

### GET /employee_history_pdf/:employee_id/:report_type

Generates a PDF report of an employee's history for a specific report type.

**URL Parameters:**
- `employee_id`: ID of the employee
- `report_type`: Type of report to generate

**Query Parameters:**
- `date_from` (Optional): Start date (format: YYYY-MM-DD)
- `date_to` (Optional): End date (format: YYYY-MM-DD)

**Response:**
- HTML content formatted for PDF printing with employee history data

**Notes:**
- Requires authentication (login_required)
- If dates are not provided, calculates appropriate default date range
- For 'overview' report type, provides summary statistics
- For other report types, provides detailed records
- Data is formatted with Arabic translations of field names

### POST /generate_print_report

Generates a formatted report for printing.

**Request Body (Form Data):**
```
report_type: "absent" // or other report types
date_from: "2023-01-01"
date_to: "2023-01-31"
employee_id: "123" // optional
office: "اسم المكتب" // optional
format: "pdf" // optional
```

**Response:**
- HTML page formatted for printing with report data

**Notes:**
- Requires authentication (login_required)
- Supports various report types (attendance, leaves, permissions, etc.)
- Formats data in a print-friendly layout
- Can specify format as PDF for download

### GET /employee_report

Displays employee reports based on specified criteria.

**Query Parameters:**
- `report_type`: Type of report to generate
- `date_from`: Start date for the report (format: YYYY-MM-DD)
- `date_to`: End date for the report (format: YYYY-MM-DD)
- `employee_id` (Optional): Filter by employee ID
- `office` (Optional): Filter by office name
- `format` (Optional): Output format (pdf, html)

**Response:**
- HTML or PDF with the requested report data

**Notes:**
- Requires authentication (login_required)
- Comprehensive reporting interface with multiple filter options
- Translates field names to Arabic for display
- Calculates summary statistics (totals, averages)

### GET /admin/reports
### GET /reports

Administrative interfaces for generating various system reports.

**Response:**
- HTML page with report generation options

**Notes:**
- Requires authentication (login_required)
- Provides UI for selecting report parameters
- Supports exporting to different formats

## Form Loading API

### GET /load_form/:report_type

Loads a form for a specific request type.

**URL Parameters:**
- `report_type`: Type of form to load ('clinic', 'ezn', 'agaza', 'altmas', 'momrya')

**Response:**
- HTML content with the appropriate form

**Error Response:**
```json
{
  "error": "Invalid report type"
}
```

**Notes:**
- Dynamically loads the appropriate form based on request type
- Returns error 400 for invalid report types
- Includes current user information in the rendered form

## Attendance Management APIs

### GET /video_feed

Provides a video stream with face recognition capability.

**Response:**
- MIME type: 'multipart/x-mixed-replace; boundary=frame'
- Stream of video frames

**Notes:**
- Used for real-time face recognition attendance system
- Connects to camera and processes frames

### GET /recognized_id_feed

Provides a server-sent events stream with recognized employee data.

**Response:**
- MIME type: "text/event-stream"
- Stream of employee data events

**Event Data Example:**
```json
{
  "employee_id": 123,
  "name": "اسم الموظف",
  "office_name": "اسم المكتب",
  "job_start_time": "08:00:00",
  "job_end_time": "15:00:00",
  "date_of_today": "2023-01-01",
  "time_now": "08:15:30",
  "period": "الفترة الصباحية",
  "img": "employee_photo.jpg"
}
```

**Notes:**
- Used in conjunction with /video_feed for attendance system
- Returns employee data when a face is recognized
- Connection stays open to receive continuous updates

### POST /update_time

Updates attendance check-in/check-out times for an employee.

**Request Body (Form Data):**
```
employee_id: "123"
hours: "8"
minutes: "15"
type: "check_in" // or "check_out"
```

**Query Parameters:**
- `date` (Optional): Date to update (format: YYYY-MM-DD, defaults to today)

**Response:**
- Redirects to /attendnce_sign with the selected date

**Notes:**
- Creates a new attendance record if none exists for the employee on the selected date
- Updates either check_in_time or check_out_time based on the 'type' parameter
- Displays success message upon completion

### POST /delete_attendence/:employee_id

Deletes an attendance record for an employee on a specific date.

**URL Parameters:**
- `employee_id`: ID of the employee

**Query Parameters:**
- `date` (Optional): Date of the attendance record (format: YYYY-MM-DD, defaults to today)

**Response:**
- Redirects to /attendnce_sign with the selected date

**Notes:**
- Requires authentication (login_required)
- Displays success message if the record is deleted
- Displays appropriate error message if no record exists

## Deduction Management APIs

### GET /Deduction

Displays a page for managing employee deductions.

**Query Parameters:**
- `office` (Optional): Filter by office name
- `year` (Optional): Filter by year
- `month` (Optional): Filter by month (1-12)

**Response:**
- HTML page with deduction management interface

**Notes:**
- Requires authentication (login_required)
- Lists all deductions with filtering options
- Shows deduction details including amount, type, and reason

### POST /add_Deduction

Adds a new deduction record for an employee.

**Request Body (Form Data):**
```
employee_id: "123"
deduction_date: "2023-01-15"
deduction_amount: "100"
deduction_reason: "سبب الخصم"
```

**Response:**
- Redirects to the deduction page with success message

**Notes:**
- Requires authentication (login_required)
- Records financial deductions from employee salary
- Validates input data before saving

### POST /Deduction/delete/:Deduction_id

Deletes a deduction record.

**URL Parameters:**
- `Deduction_id`: ID of the deduction record

**Response:**
- Redirects to /Deduction

**Notes:**
- Requires authentication (login_required)
- Displays success message upon successful deletion 

## User Management APIs

### GET /users

Displays a list of system users.

**Response:**
- HTML page with user management interface

**Notes:**
- Requires authentication (login_required)
- Admin-only access
- Lists all users with their roles and permissions

### POST /add_user

Creates a new system user.

**Request Body (Form Data):**
```
username: "new_user"
password: "secure_password"
password2: "secure_password"
employee_id: "123" // optional
user_type: "office_manager"
office: "اسم المكتب" // if applicable
```

**Response:**
- Redirects to users list with success message
- If errors: Displays form with validation messages

**Notes:**
- Requires authentication (login_required)
- Admin-only access
- Creates user account with specified permissions
- Optionally links to an employee record

### POST /edit_user/:user_id

Updates an existing user account.

**URL Parameters:**
- `user_id`: ID of the user to edit

**Request Body (Form Data):**
```
username: "updated_username"
password: "new_password" // optional
password2: "new_password" // optional
employee_id: "124" // optional
user_type: "admin"
office: "اسم المكتب المحدث" // if applicable
```

**Response:**
- Redirects to users list with success message
- If errors: Displays form with validation messages

**Notes:**
- Requires authentication (login_required)
- Admin-only access
- Can update username, password, linked employee, user type, and office
- Password fields can be left empty to keep current password

### POST /delete_user/:user_id

Deletes a user account.

**URL Parameters:**
- `user_id`: ID of the user to delete

**Response:**
- Redirects to users list with success message

**Notes:**
- Requires authentication (login_required)
- Admin-only access
- Cannot delete the currently logged-in user
- Permanently removes the user account

## Admin Dashboard APIs

### GET /admin_dashboard

Displays the main administrative dashboard.

**Response:**
- HTML page with administrative overview and statistics

**Notes:**
- Requires authentication (login_required)
- Shows system statistics and quick access to key functions
- Dashboard content varies based on user role

### GET /settings

Manages system-wide settings.

**Response:**
- HTML page with settings interface

**Notes:**
- Requires authentication (login_required)
- Admin-only access
- Allows configuration of system parameters
- Settings include default values, system behavior options, and appearance settings

### GET /admin_users

Administrative interface for user management.

**Response:**
- HTML page with user management interface

**Notes:**
- Requires authentication (login_required)
- Admin-only access
- Provides access to user CRUD operations
- Shows user statistics and status

## Helper Functions

This section documents the helper functions from `helpers.py` that support the application's APIs.

### Report Generation Helpers

#### handle_attendance_reports
```python
handle_attendance_reports(
    report_type, 
    report_date=None, 
    period=None, 
    id=None, 
    date_from=None, 
    date_to=None, 
    include_delay_minutes=False, 
    include_leave_early_time=False,
    employee_office_name=None,
    count_only=False
)
```

**Description:**
Processes attendance reports for various report types.

**Parameters:**
- `report_type`: Type of report to generate ('absent', 'check_in_attendance', 'check_in_delays', etc.)
- `report_date`: Specific date for the report (format: YYYY-MM-DD)
- `period`: Period to filter by ('الفترة الصباحية', 'الفترة المسائية')
- `id`: Employee ID to filter by
- `date_from`: Start date for the report range (format: YYYY-MM-DD)
- `date_to`: End date for the report range (format: YYYY-MM-DD)
- `include_delay_minutes`: Whether to include delay minutes in the report
- `include_leave_early_time`: Whether to include leave early time in the report
- `employee_office_name`: Office name to filter by
- `count_only`: If True, returns only the count of records instead of full report data

**Returns:**
- Report data or count based on the report type and parameters
- For `count_only=True`, returns an integer
- For `count_only=False`, returns a list of records with relevant data

#### handle_agaza_reports
```python
handle_agaza_reports(report_type, id, employee_office_name, date_from, date_to, report_date, period, status_translations)
```

**Description:**
Handles reports for leave (agaza) requests.

**Parameters:**
- `report_type`: Type of leave report
- `id`: Employee ID to filter by
- `employee_office_name`: Office name to filter by
- `date_from`: Start date for the report range
- `date_to`: End date for the report range
- `report_date`: Specific date for the report
- `period`: Period to filter by
- `status_translations`: Dictionary of status translations for localization

**Returns:**
- List of leave request records matching the criteria

#### count_agaza_reports
```python
count_agaza_reports(report_type, id, employee_office_name, date_from, date_to, report_date, period)
```

**Description:**
Counts leave (agaza) request records based on specified criteria.

**Parameters:**
- Same as `handle_agaza_reports` without the `status_translations` parameter

**Returns:**
- Integer count of matching leave request records

#### handle_ezn_report / handle_clinic_report / handle_altmas_report / handle_momrya_report
```python
handle_ezn_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
handle_clinic_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
handle_altmas_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
handle_momrya_report(id, employee_office_name, date_from, date_to, report_date, period, status_translations)
```

**Description:**
Handles reports for permission (ezn), clinic visits, petitions (altmas), and missions (momrya).

**Parameters:**
- `id`: Employee ID to filter by
- `employee_office_name`: Office name to filter by
- `date_from`: Start date for the report range
- `date_to`: End date for the report range
- `report_date`: Specific date for the report
- `period`: Period to filter by
- `status_translations`: Dictionary of status translations for localization

**Returns:**
- List of request records matching the criteria

#### count_ezn_report / count_clinic_report / count_altmas_report / count_momrya_report
```python
count_ezn_report(id, employee_office_name, date_from, date_to, report_date, period)
count_clinic_report(id, employee_office_name, date_from, date_to, report_date, period)
count_altmas_report(id, employee_office_name, date_from, date_to, report_date, period)
count_momrya_report(id, employee_office_name, date_from, date_to, report_date, period)
```

**Description:**
Count the number of records for each report type.

**Parameters:**
- Same as the corresponding handler functions without the `status_translations` parameter

**Returns:**
- Integer count of matching records

#### handle_rest_report / count_rest_report
```python
handle_rest_report(date_from, date_to, report_date, id, employee_office_name, period)
count_rest_report(date_from, date_to, report_date, id, employee_office_name, period)
```

**Description:**
Handles/counts reports for rest days.

**Parameters:**
- `date_from`: Start date for the report range
- `date_to`: End date for the report range
- `report_date`: Specific date for the report
- `id`: Employee ID to filter by
- `employee_office_name`: Office name to filter by
- `period`: Period to filter by

**Returns:**
- List of rest day records or count of matching records

#### handle_no_check_out_report / count_no_check_out_report
```python
handle_no_check_out_report(id, employee_office_name, date_from, date_to, report_date, period)
count_no_check_out_report(id, employee_office_name, date_from, date_to, report_date, period)
```

**Description:**
Handles/counts reports for employees who did not check out.

**Parameters:**
- `id`: Employee ID to filter by
- `employee_office_name`: Office name to filter by
- `date_from`: Start date for the report range
- `date_to`: End date for the report range
- `report_date`: Specific date for the report
- `period`: Period to filter by

**Returns:**
- List of no check-out records or count of matching records

#### handle_rased_report
```python
handle_rased_report(id, employee_office_name)
```

**Description:**
Handles reports for employee leave balance (rased).

**Parameters:**
- `id`: Employee ID to filter by
- `employee_office_name`: Office name to filter by

**Returns:**
- List of leave balance records matching the criteria

#### handle_deduction_report
```python
handle_deduction_report(
    report_date=None, 
    id=None, 
    date_from=None, 
    date_to=None, 
    period=None, 
    employee_office_name=None
)
```

**Description:**
Handles reports for employee deductions.

**Parameters:**
- `report_date`: Specific date for the report
- `id`: Employee ID to filter by
- `date_from`: Start date for the report range
- `date_to`: End date for the report range
- `period`: Period to filter by
- `employee_office_name`: Office name to filter by

**Returns:**
- Detailed report of deductions and total deduction amount

#### generate_mo2srat_report
```python
generate_mo2srat_report(from_date, to_date, office=None, employee_id=None, type=None)
```

**Description:**
Generates a report of employee absences and delays.

**Parameters:**
- `from_date`: Start date for the report
- `to_date`: End date for the report
- `office`: Office name to filter by
- `employee_id`: Employee ID to filter by
- `type`: Type of report ('absent', 'delay', etc.)

**Returns:**
- Detailed and summary reports of employee absences or delays

### Attendance Management Helpers

#### get_absent_employees
```python
get_absent_employees(specific_day=None, period=None, employee_id=None, date_from=None, date_to=None, office_name=None)
```

**Description:**
Retrieves a list of employees who were absent on specific dates.

**Parameters:**
- `specific_day`: Specific date to check for absences
- `period`: Period to filter by
- `employee_id`: Employee ID to filter by
- `date_from`: Start date for the range
- `date_to`: End date for the range
- `office_name`: Office name to filter by

**Returns:**
- List of absent employee records with details

#### process_attendance_for_employee
```python
process_attendance_for_employee(employee_id)
```

**Description:**
Processes attendance for an employee recognized by the face recognition system.

**Parameters:**
- `employee_id`: ID of the employee

**Returns:**
- Result of attendance processing

#### record_appearance
```python
record_appearance(employee_id)
```

**Description:**
Records an employee's appearance in the attendance system.

**Parameters:**
- `employee_id`: ID of the employee

**Returns:**
- Result of recording the employee's appearance

#### generate_attendance_report
```python
generate_attendance_report(report_date, period=None, type_field=None)
```

**Description:**
Generates an attendance report for all employees on a specific date.

**Parameters:**
- `report_date`: Date for the report
- `period`: Period to filter by
- `type_field`: Type of attendance to filter by

**Returns:**
- Attendance report for all employees

#### sort_attendance_report
```python
sort_attendance_report(attendance_report)
```

**Description:**
Sorts an attendance report by office name according to a predefined order.

**Parameters:**
- `attendance_report`: The report to sort

**Returns:**
- Sorted attendance report

### Leave Management Helpers

#### is_agaza_approved
```python
is_agaza_approved(employee_id, date)
```

**Description:**
Checks if an employee has an approved leave for a specific date.

**Parameters:**
- `employee_id`: ID of the employee
- `date`: Date to check for leave

**Returns:**
- Boolean indicating if the employee has an approved leave

#### calculate_agaza_duration_this_year
```python
calculate_agaza_duration_this_year(employee_id, current_year, agaza_type=None, submit_date=None, after=None)
```

**Description:**
Calculates the duration of leave taken by an employee in the current year.

**Parameters:**
- `employee_id`: ID of the employee
- `current_year`: Year to calculate for
- `agaza_type`: Type of leave to filter by
- `submit_date`: Optional date to filter leaves submitted after
- `after`: Optional date to filter leaves occurring after

**Returns:**
- Dictionary with leave durations by type and total

#### manage_agaza
```python
manage_agaza()
```

**Description:**
Manages employee leave balances and automatic updates.

**Returns:**
- None

### Utility Helpers

#### parse_time_str
```python
parse_time_str(time_str)
```

**Description:**
Parses a time string into hours and minutes.

**Parameters:**
- `time_str`: Time string to parse (format: "HH:MM" or "HH:MM:SS")

**Returns:**
- Tuple of (hours, minutes)

#### days_between_dates
```python
days_between_dates(date1_str, date2_str)
```

**Description:**
Calculates the number of days between two dates.

**Parameters:**
- `date1_str`: First date string (format: YYYY-MM-DD)
- `date2_str`: Second date string (format: YYYY-MM-DD)

**Returns:**
- Integer number of days between the dates

#### format_date_to_arabic / format_time_to_arabic
```python
format_date_to_arabic(date_obj)
format_time_to_arabic(time_obj)
```

**Description:**
Formats a date or time object into Arabic text.

**Parameters:**
- `date_obj` / `time_obj`: Date or time object to format

**Returns:**
- String with the date or time formatted in Arabic

#### convert_to_arabic_numerals
```python
convert_to_arabic_numerals(number)
```

**Description:**
Converts a number to Arabic numerals.

**Parameters:**
- `number`: Number to convert

**Returns:**
- String with the number in Arabic numerals

#### get_employee_info
```python
get_employee_info(employee_id)
```

**Description:**
Retrieves basic information about an employee.

**Parameters:**
- `employee_id`: ID of the employee

**Returns:**
- Dictionary with employee information

#### get_user_office_and_type
```python
get_user_office_and_type(user_id)
```

**Description:**
Retrieves the office and type of a user.

**Parameters:**
- `user_id`: ID of the user

**Returns:**
- Tuple of (office, type)

#### get_all_offices
```python
get_all_offices()
```

**Description:**
Retrieves a list of all offices.

**Returns:**
- List of office names

#### get_employees_by_office
```python
get_employees_by_office(office_name=None)
```

**Description:**
Retrieves employees for a specific office or all offices if no office is specified.

**Parameters:**
- `office_name`: Name of the office to filter by

**Returns:**
- List of employee records 

## Employee Management APIs

### POST /add_employee

Creates a new employee record or updates an existing one.

**Request Body (Form Data):**
Extensive form with employee details including:
```
id: "123" (optional, for updates)
name: "اسم الموظف"
code_number: "12345"
employee_number: "67890"
office: "اسم المكتب"
job_name_modli: "المسمى الوظيفي"
period: "الفترة الصباحية"
job_start_time: "08:00"
job_end_time: "15:00"
phone: "1234567890"
national_id: "1234567890123"
birth_date: "1990-01-01"
hire_date: "2020-01-01"
qualification: "المؤهل"
qualification_date: "2010-01-01"
address: "العنوان"
gender: "ذكر"
religion: "الديانة"
military_service: "حالة الخدمة العسكرية"
marital_status: "الحالة الاجتماعية"
years_of_experience: "5"
active: "ظهور"
points_agaza: "30"
points_3ardy: "5"
point_3tady: "15"
point_sany: "0"
salary: "5000"
rased_month: "12"
rased_year: "2023"
```

**Response:**
- If successful: Redirects to the employee list with success message
- If unsuccessful: Returns the form with validation errors

**Notes:**
- Requires authentication (login_required)
- Form includes personal, job, and leave balance information
- Supports both adding new employees and updating existing ones
- Performs validation on critical fields like national ID

### POST /delete_employee/:employee_id

Deletes an employee record.

**URL Parameters:**
- `employee_id`: ID of the employee to delete

**Response:**
- Redirects to the employee list with confirmation message

**Notes:**
- Requires authentication (login_required)
- Soft-deletes the employee by setting active status to "عدم ظهور"
- Maintains database integrity by preserving historical data

### GET /employee_rates

Displays and manages employee performance ratings.

**Query Parameters:**
- `office` (Optional): Filter by office name
- `month` (Optional): Month for ratings (1-12)
- `year` (Optional): Year for ratings (e.g., 2023)

**Response:**
- HTML page with employee rating form and existing ratings

**Notes:**
- Requires authentication (login_required)
- Allows rating employees on various performance metrics
- Supports filtering by office, month, and year

### GET /employee_history/:employee_id

Retrieves and displays the historical records for a specific employee.

**URL Parameters:**
- `employee_id`: ID of the employee

**Query Parameters:**
- `report_type` (Optional): Type of history to view ('absent', 'clinic', etc.)
- `date_from` (Optional): Start date for history (format: YYYY-MM-DD)
- `date_to` (Optional): End date for history (format: YYYY-MM-DD)

**Response:**
- HTML page with employee history data

**Notes:**
- Requires authentication (login_required)
- Shows comprehensive employee history including attendance, leaves, permissions
- Supports date range filtering
- Includes summary statistics and detailed records 

## Schedule Management APIs

### GET /official_holidays

Displays a list of official holidays.

**Response:**
- HTML page with the list of holidays

**Notes:**
- Requires authentication (login_required)
- Shows all configured holidays with their dates and descriptions

### POST /add_official_holidays

Adds a new official holiday to the system.

**Request Body (Form Data):**
```
description: "عيد الفطر"
date: "2023-06-15"
```

**Response:**
- Redirects to the holidays page with success message

**Notes:**
- Requires authentication (login_required)
- Validates that the holiday doesn't already exist

### POST /official_holidays/edit/:holiday_id

Updates an existing holiday record.

**URL Parameters:**
- `holiday_id`: ID of the holiday to edit

**Request Body (Form Data):**
```
description: "عيد الفطر المبارك"
date: "2023-06-16"
```

**Response:**
- Redirects to the holidays page with success message

**Notes:**
- Requires authentication (login_required)
- Updates the description and/or date of an existing holiday

### POST /holidays/delete/:holiday_id

Deletes a holiday record.

**URL Parameters:**
- `holiday_id`: ID of the holiday to delete

**Response:**
- Redirects to the holidays page with success message

**Notes:**
- Requires authentication (login_required)
- Permanently removes the holiday from the system

### POST /add_job_schedule_override

Creates a schedule override for specific employees.

**Request Body (Form Data):**
```
employee_id: "123"
start_date: "2023-01-01"
end_date: "2023-01-31"
override_type: "إجازة رسمية"
job_start_time: "10:00" // optional
job_end_time: "16:00" // optional
```

**Response:**
- Redirects to the job schedule override page with success message

**Notes:**
- Requires authentication (login_required)
- Used for temporary schedule changes
- Can override working hours or mark days as official leave

### GET /job_schedule_override

Displays a list of all job schedule overrides.

**Response:**
- HTML page with the list of schedule overrides

**Notes:**
- Requires authentication (login_required)
- Shows all active schedule overrides with their details

### POST /delete_job_schedule_override/:override_id

Deletes a job schedule override.

**URL Parameters:**
- `override_id`: ID of the override to delete

**Response:**
- Redirects to the job schedule override page with success message

**Notes:**
- Requires authentication (login_required)
- Permanently removes the schedule override 