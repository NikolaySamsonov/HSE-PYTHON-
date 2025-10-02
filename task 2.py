
boys_list = input("Введите имена мальчиков через запятую: ")
boys = [s.strip() for s in boys_list.split(',')]
girls_list = input("Введите имена девочек через запятую: ")
girls = [s.strip() for s in girls_list.split(',')]
if len(boys) == len(girls):
    boys.sort()
    girls.sort()
    for i in range(len(boys)):
        print(boys[i], "и",girls[i])
else:
    print("Внимание, кто-то может остаться без пары.")