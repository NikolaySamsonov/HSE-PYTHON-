import csv


purchases = {}
with open('purchase_log.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        purchases[row['user_id']] = row['category']


with open('visit_log.csv', encoding='utf-8') as fin, \
     open('funnel.csv', 'w', encoding='utf-8', newline='') as fout:

    reader = csv.DictReader(fin)
    fieldnames = ['user_id', 'source', 'category']
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        user = row['user_id']
        if user in purchases:
            writer.writerow({
                'user_id': user,
                'source': row['source'],
                'category': purchases[user]
            })
