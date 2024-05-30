import csv

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    stack = [(parent_key, d)]
    
    while stack:
        current_key, current_dict = stack.pop()

        for k, v in current_dict.items():
            new_key = f"{current_key}{sep}{k}" if current_key else k

            if isinstance(v, dict):
                stack.append((new_key, v))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    item_key = f"{new_key}{sep}{i}"
                    items.extend([(item_key, val) for val in flatten_dict({item_key: item, **current_dict}).values()])
            else:
                items.append((new_key, v))

    return dict(items)

# Example usage:

nested_dict = {
    'person1': {
        'name': 'John',
        'age': 30,
        'address': {
            'city': 'New York',
            'zip': '10001'
        },
        'phones': ['555-1234', '555-5678']
    },
    'person2': {
        'name': 'Alice',
        'age': 25,
        'address': {
            'city': 'San Francisco',
            'zip': '94105'
        },
        'phones': ['555-9876', '555-4321']
    }
}

# Flatten the dictionary
flattened_data = [flatten_dict({key: value}, key) for key, value in nested_dict.items()]

# Write to CSV
csv_filename = 'output.csv'
with open(csv_filename, 'w', newline='') as csvfile:
    fieldnames = set(key for row in flattened_data for key in row.keys())
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(flattened_data)