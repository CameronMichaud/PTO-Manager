## PTO Management Tool
- See PTO accrual at any date
<img width="896" height="513" alt="image" src="readme_screenshots/View_As_Of.png" />

- View employee PTO history and manage usage
<img width="1014" height="616" alt="image" src="readme_screenshots/Dashboard.png" />
<img width="1322" height="694" alt="image" src="readme_screenshots/PTO_History_Dashboard.png" />

- Edit Records Directly
<img width="896" height="510" alt="image" src="readme_screenshots/Edit_Cell.png" />

- Search
<img width="903" height="515" alt="image" src="readme_screenshots/Search.png" />

- Add Employee
<img width="901" height="513" alt="image" src="readme_screenshots/Add.png" />

### Importing / Exporting data
- Exporting PTO
  
Exporting PTO will output a CSV for each employee to the assigned directory with format: employee, date, hours

- Importing PTO
  
First create the employees inside of the app and then import any directory containing CSVs formatted as: employee, date, hours - with date being (mm-dd-yyyy) format. If employees are not created prior to the import then a new employee will be created and assigned the PTO according to the name but the hire date and total PTO fields will be 0 and can be edited later.

Note: importing app data from a prior export of app data will carry over both employee information and PTO information.

- Import/Export App Data
  
This will export both the employee and PTO usage tables which can be loaded back into the same program with all data via the import function.
