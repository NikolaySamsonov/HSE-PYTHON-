from datetime import datetime

formats = [
    ("%A, %B %d, %Y", "The Moscow Times"),
    ("%A, %d.%m.%y", "The Guardian"),
    ("%A, %d %B %Y", "Daily News")
]

print("Введите дату (или 'q' для выхода):")

while True:
    date_str = input("> ")

    if date_str.lower() == 'q':
        print("Завершение программы.")
        break

    parsed = False

    for fmt, source in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            print(f"{source}: {dt}")
            parsed = True
            break
        except ValueError:
            continue

    if not parsed:
        print("Неверный формат даты. Попробуйте снова.")
