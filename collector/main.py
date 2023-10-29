import json


OUTPUT_DIR_PATH = '../data'
OUTPUT_CSV_PATH = f'{OUTPUT_DIR_PATH}/data.csv'
OUTPUT_JSON_PATH = f'{OUTPUT_DIR_PATH}/data.json'


NutritionFacts = dict[str, str | float]


def main() -> None:
    data: list[NutritionFacts] = read_data()
    write_data(data)


def read_data() -> list[NutritionFacts]:
    return [
        {
            'name': 'hard-boiled egg',
            'calories': 131.0,
            'fat': 9.0,
            'carbohydrate': 0.0,
            'protein': 12.6,
        },
        {
            'name': 'apple',
            'calories': 52.0,
            'fat': 0.2,
            'carbohydrate': 14.0,
            'protein': 0.3,
        }
    ]


def write_data(data: list[NutritionFacts]) -> None:
    with open(OUTPUT_JSON_PATH, 'w') as output_json_file:
        output_json_file.write(json.dumps(data, separators=(',', ':')))

    with open(OUTPUT_CSV_PATH, 'w') as output_csv_file:
        output_csv_file.write(",".join(data[0].keys()) + '\n')

        for i, element in enumerate(data):
            output_csv_file.write(",".join([str(value) for value in element.values()]))

            if i < len(data) - 1:
                output_csv_file.write('\n')


if __name__ == '__main__':
    main()
