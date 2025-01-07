def convert_list(data_list):
    return [convert_str_to_number(item) for item in data_list]


def convert_str_to_number(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def to_vertical_representation(transactions):
    vertical = {}
    for tid, txn in enumerate(transactions, start=0):
        for item in txn:
            if item not in vertical:
                vertical[item] = set()
            vertical[item].add(tid)
    return vertical


def to_horizontal_representation(transactions, utility_of_each_item):
    horizontal = {}

    for transaction_ID, (items, utility) in enumerate(
        zip(transactions, utility_of_each_item), start=0
    ):
        horizontal[transaction_ID] = {item: util for item, util in zip(items, utility)}
    return horizontal


def calculate_total_utility(vertical, horizontal):  # -> dict:
    utility_values_of_mono_item = {}
    for item_name, list_id_transactions in vertical.items():
        utility_values_of_mono_item[item_name] = sum(
            [
                horizontal[transaction_ID][item_name]
                for transaction_ID in list_id_transactions
            ]
        )
    return utility_values_of_mono_item


class DataWarehouse:
    def __init__(self, data: str):
        self.data = data
        self.items = []
        self.transaction_utility = []
        self.utility_of_each_item = []
        self.utility_values_of_mono_item = {}
        self.vertical = None
        self.horizontal = None
        self.total_utility = 0
        self._process_data()
        self._create_representation_data()

    def _process_data(self):
        lines = self.data.strip().split("\n")
        for line in lines:
            items, transaction_utility, utility_of_each_item = line.split(":")
            self.items.append(convert_list(items.split()))
            self.transaction_utility.append(convert_str_to_number(transaction_utility))
            self.utility_of_each_item.append(convert_list(utility_of_each_item.split()))

    def _create_representation_data(self):
        self.vertical = to_vertical_representation(self.items)
        self.horizontal = to_horizontal_representation(
            self.items, self.utility_of_each_item
        )
        self.utility_values_of_mono_item = calculate_total_utility(
            self.vertical, self.horizontal
        )
        self.total_utility = sum(self.utility_values_of_mono_item.values())
    