def reserve_capacity(available_hours, demands):
    """Reserve an employee's capacity across demand lines in order."""
    remaining = available_hours
    reservations = []

    for demand_hours in demands:
        reserved = min(remaining, demand_hours)
        reservations.append(reserved)
        remaining -= reserved

    return reservations


def test_one_employee_capacity_is_not_promised_twice():
    reservations = reserve_capacity(10, [8, 7])

    assert reservations == [8, 2]
    assert sum(reservations) == 10
    assert sum(reservations) <= 10


def test_capacity_is_not_negative():
    reservations = reserve_capacity(5, [2, 4])

    assert reservations == [2, 3]
    assert all(hours >= 0 for hours in reservations)
