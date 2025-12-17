import csv


def read_csv_generator(filename):

    with open(filename, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield row


def parse_client(row):

    return {
        "name": row["name"].strip(),
        "device_type": row["device_type"].strip(),
        "browser": row["browser"].strip(),
        "sex": row["sex"].strip(),
        "age": row["age"].strip(),
        "bill": row["bill"].strip(),
        "region": row["region"].strip()
    }


def transform_client(client):

    client["sex_text"] = "мужского" if client["sex"] == "male" else "женского"
    client["verb"] = "совершил" if client["sex"] == "male" else "совершила"

    device_map = {
        "mobile": "мобильного",
        "tablet": "планшетного",
        "desktop": "настольного",
        "laptop": "портативного"
    }
    client["device_text"] = device_map.get(client["device_type"], "неизвестного")

    return client


def generate_description(client):

    return (
        f"Пользователь {client['name']} {client['sex_text']} пола, "
        f"{client['age']} лет {client['verb']} покупку на {client['bill']} у.е. "
        f"с {client['device_text']} браузера {client['browser']}. "
        f"Регион, из которого совершалась покупка: {client['region']}."
    )


def process_file(input_file, output_file):

    with open(output_file, "w", encoding="utf-8") as out:
        for row in read_csv_generator(input_file):
            client = parse_client(row)
            client = transform_client(client)
            out.write(generate_description(client) + "\n")



process_file(
    input_file="web_clients_correct.csv",
    output_file="output.txt"
)
