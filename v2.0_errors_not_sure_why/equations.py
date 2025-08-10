import numpy as np

# Equations for manipulating data_analyzer.py

def absolute_val(col):
    """ Returns the absolute value of inputted value """
    return [abs(x) for x in col]


def filter_positive_values(v_data, c_data):
    """ Returns only positive values from voltage and current arrays """
    result_voltage_ps, result_current_ps = [], []

    for v, c in zip(v_data, c_data):
        if v >= 0:
            result_voltage_ps.append(v)
            result_current_ps.append(c)
        else:
            result_voltage_ps.append(0)
            result_current_ps.append(0)

    return result_voltage_ps, result_current_ps


def filter_negative_values(v_data, c_data):
    """ Returns only negative values from voltage and current arrays """
    result_voltage_ng, result_current_ng = [], []
    for v, c in zip(v_data, c_data):
        if v <= 0:
            result_voltage_ng.append(v)
            result_current_ng.append(c)
        else:
            result_voltage_ng.append(0)
            result_current_ng.append(0)

    return absolute_val(result_voltage_ng), absolute_val(result_current_ng)


def zero_devision_check(x, y):
    """ Prevents division by zero errors """
    try:
        return x / y
    except ZeroDivisionError:
        return 0


def resistance(v_data, c_data):
    """ Calculate resistance from voltage and current arrays """
    return [zero_devision_check(v, c) for v, c in zip(v_data, c_data)]


def log_value(array):
    """ Logarithm of each element in the array, avoiding zero errors """
    return [np.log(abs(x)) if x != 0 else 0 for x in array]


def current_density_eq(v_data, c_data, distance=100E-9, area=100E-6):
    """ Calculates current density using voltage and current arrays """
    current_density = []
    for v, c in zip(v_data, c_data):
        if v == 0 or c == 0:
            current_density.append(0)
            continue
        new_num = (distance / ((v / c) * area ** 2)) * (v / distance)
        current_density.append(new_num)
    return current_density


def electric_field_eq(v_data, distance=100E-9):
    """ Calculates electric field using voltage array """
    return [v / distance if v != 0 else 0 for v in v_data]


def inverse_resistance_eq(v_data, c_data):
    """ Inverse of resistance (current/voltage) """
    return [c / v if v != 0 and c != 0 else 0 for v, c in zip(v_data, c_data)]


def sqrt_array(value_array):
    """ Square root of an array """
    return [v ** 0.5 for v in value_array]
