from datetime import date


def calculate_pto(emp, today=None):
    if today is None:
        today = date.today()
    
    jan = date(today.year, 1, 1)

    hire_date = date.fromisoformat(emp["hire_date"])
    total = float(emp["total_pto"])
    rate = total/52

    start = max(hire_date, jan)

    if start > today:
        return 0.0

    weeks = (today - start).days // 7
    accrued = weeks * rate

    return round(accrued, 2)


def calculate_used_pto(employee_id, usage_records, horizon=None):
    if horizon is None:
        horizon = date.today()

    total = 0.0
    for usage in usage_records:
        if usage["employee_id"] == employee_id:
            used_date = date.fromisoformat(usage["date"])
            if used_date.year == horizon.year:
                total += float(usage["hours"])
    return round(total, 2)


def calculate_available_pto(emp, usage_records, horizon=None):
    if horizon is None:
        horizon = date.today()
        
    carryover = float(emp["carryover"])
    accrued = calculate_pto(emp, today=horizon)
    used = calculate_used_pto(emp["id"], usage_records, horizon)
    return round(accrued + carryover - used, 2)

