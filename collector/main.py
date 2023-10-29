# See <https://www.bedca.net/bdpub/>


import json
import logging
import time

import bs4
import requests


BASE_URL = 'https://www.bedca.net/bdpub/procquery.php'
REQUEST_TEMPLATES_DIR_PATH = './request-templates'
LIST_TEMPLATE_BODY_PATH = f'{REQUEST_TEMPLATES_DIR_PATH}/list.xml'
DETAIL_TEMPLATE_BODY_PATH = f'{REQUEST_TEMPLATES_DIR_PATH}/detail.xml'
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
CALORIES_EUR_NAME = 'ENERC'
FAT_EUR_NAME = 'FAT'
PROTEIN_EUR_NAME = 'PROT'
CARBOHYDRATE_EUR_NAME = 'CHO'

OUTPUT_DIR_PATH = '../data'
OUTPUT_CSV_PATH = f'{OUTPUT_DIR_PATH}/data.csv'
OUTPUT_JSON_PATH = f'{OUTPUT_DIR_PATH}/data.json'


NutritionFacts = dict[str, str | float]


def main() -> None:
    logging.info(f'Started')
    start_seconds: float = time.time()

    data: list[NutritionFacts] = read_data()
    write_data(data)

    elapsed_seconds: float = time.time() - start_seconds
    logging.info(f'Done! Elapsed: {elapsed_seconds:.1f} s')


def read_data() -> list[NutritionFacts]:
    logging.info('Reading request body templates')
    list_template_body_template: str = read_request_template(LIST_TEMPLATE_BODY_PATH)
    detail_template_body_template: str = read_request_template(DETAIL_TEMPLATE_BODY_PATH)

    food_ids_and_names: list[tuple[int, str]] = list_foods(list_template_body_template)

    all_nutrition_facts: list[NutritionFacts] = []

    for food_id, food_name in food_ids_and_names:
        nutrition_facts: NutritionFacts | None = get_nutrition_facts(detail_template_body_template, food_id, food_name)

        if nutrition_facts is None:
            continue
        else:
            all_nutrition_facts.append(nutrition_facts)

    return all_nutrition_facts


def read_request_template(request_template_path: str) -> str:
    with open(request_template_path) as list_request_template_file:
        return list_request_template_file.read()


def list_foods(request_body_template: str) -> list[tuple[int, str]]:
    food_ids_and_names: list[tuple[int, str]] = []

    for letter in ALPHABET:
        logging.info(f'Getting foods starting by {letter.upper()}')

        response = requests.post(
            headers = {'Content-Type': 'text/xml'},
            data = request_body_template.replace('${letter}', letter),
            url = BASE_URL)

        if response.status_code != 200:
            raise Exception(f'Received HTTP {response.status_code}')

        soup = bs4.BeautifulSoup(response.text, features='xml')
        foods: bs4.element.ResultSet = soup.find_all('foodresponse')[0].find_all('food')
        
        for food in foods:
            id: int = int(food.find('f_id').string)
            name: str = str(food.find('f_ori_name').string)
            food_ids_and_names.append((id, name))

    if len(food_ids_and_names) != len(set(food_ids_and_names)):
        raise Exception('There are duplicated food IDs')

    return food_ids_and_names


def get_nutrition_facts(request_body_template: str, food_id: int, food_name: str) -> NutritionFacts | None:
    logging.info(f'Getting nutrition facts for food "{food_name}"')

    response = requests.post(
        headers = {'Content-Type': 'text/xml'},
        data = request_body_template.replace('${id}', str(food_id)),
        url = BASE_URL)

    if response.status_code != 200:
        raise Exception(f'Received HTTP {response.status_code}')

    soup = bs4.BeautifulSoup(response.text, features='xml')
    food = soup.find_all('foodresponse')[0].find('food')

    if food.find('f_ori_name') is None:
        return None

    name: str = food.find('f_ori_name').string
    energy: float = 0.0
    fat: float = 0.0
    carbohydrate: float = 0.0
    protein: float = 0.0

    for foodvalue in food.find_all('foodvalue'):
        eur_name: str = str(foodvalue.find('eur_name').string)
        value: str = foodvalue.find('best_location').string

        if value is None:
            continue
        elif eur_name == CALORIES_EUR_NAME:
            energy = round(float(value) / 4.184, 2)
        elif eur_name == FAT_EUR_NAME:
            fat = float(value)
        elif eur_name == CARBOHYDRATE_EUR_NAME:
            carbohydrate = float(value)
        elif eur_name == PROTEIN_EUR_NAME:
            protein = float(value)

    return {
        'name': name,
        'energy': energy,
        'fat': fat,
        'carbohydrate': carbohydrate,
        'protein': protein,
    }


def write_data(data: list[NutritionFacts]) -> None:
    with open(OUTPUT_JSON_PATH, 'w') as output_json_file:
        output_json_file.write(json.dumps(data, separators=(',', ':')))

    with open(OUTPUT_CSV_PATH, 'w') as output_csv_file: 
        keys: list[str] = list(data[0].keys())
        output_csv_file.write(';'.join(keys) + '\n')

        for i, element in enumerate(data):
            values: list = [element[key] for key in keys]
            output_csv_file.write(';'.join([str(value) for value in values]))

            if i < len(data) - 1:
                output_csv_file.write('\n')


if __name__ == '__main__':
    logging.basicConfig(
        format  = '%(asctime)-5s.%(msecs)03d | %(levelname)-7s | %(funcName)s | %(message)s',
        level   = logging.INFO,
        datefmt = '%Y-%m-%d %H:%M:%S')

    main()
