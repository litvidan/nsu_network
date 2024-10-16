def format_speed(speed):
    """Форматирует скорость для удобного отображения в байтах, КБ или МБ."""
    if speed < 1024:
        return f"{speed:.2f} байт/с"
    elif speed < 1024 * 1024:
        return f"{speed / 1024:.2f} КБ/с"
    else:
        return f"{speed / (1024 * 1024):.2f} МБ/с"


def format_size(size_in_bytes):
    """Форматирует размер в удобочитаемый вид."""
    if size_in_bytes < 0:
        return "Размер не может быть отрицательным"

    units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']
    unit_index = 0

    size = size_in_bytes
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"
