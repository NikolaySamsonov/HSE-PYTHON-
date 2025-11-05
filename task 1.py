# Ячейка 1: Исходные данные (можно разместить в отдельной ячейке в Jupyter или в начале файла в PyCharm)

def get_owner_by_number(doc_number, docs):

    for doc in docs:
        if doc['number'] == doc_number:
            print("Владелец документа: " + doc['name'])
            return doc['name']

    print("Владелец документа: владелец не найден")
    return None

def get_shelf_by_number(doc_number, dirs):

    for shelf, numbers in dirs.items():
        if doc_number in numbers:
            print("Документ хранится на полке: " + shelf)
            return shelf
    return None


documents = [
    {'type': 'passport', 'number': '2207 876234', 'name': 'Василий Гупкин'},
    {'type': 'invoice', 'number': '11-2', 'name': 'Геннадий Покемонов'},
    {'type': 'insurance', 'number': '10006', 'name': 'Аристарх Павлов'}
]

directories = {
    '1': ['2207 876234', '11-2'],
    '2': ['10006'],
    '3': []
}

print("введите команду")
command = input()
print("введите номер документа")
number = input()
if command == "P" :
    get_owner_by_number(number, documents)
if command == "S" :
    get_shelf_by_number(number, directories)