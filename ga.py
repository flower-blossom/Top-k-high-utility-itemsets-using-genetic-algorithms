from typing import Union
from functools import reduce
import time
import random
import heapq
from itertools import combinations
from IO import DataWarehouse


def write_output(solution: list[dict], file_name: str, data) -> None:
    
    output_file_multiple_sets = file_name
    with open(output_file_multiple_sets, "w") as file:
        for s in solution:
            sorted_elements = sorted(s)
            line = " ".join(map(str, sorted_elements)) + f" #UTIL: {Genetic.evaluation(s, data)}"
            file.write(line + "\n")

class Genetic:
    def __init__(
        self,
        number_of_population,
        m,
        quantity_of_elite,
        alpha=0.5,
        beta=0.5,
        number_of_generations=10,
        k_tournament=5,
        number_population_s=5,
        stop_criteria_loop=1000,
        time_limit=600,
    ):
        self.number_of_population = number_of_population
        self.m = m
        self.quantity_of_elite = quantity_of_elite
        self.alpha = alpha
        self.beta = beta
        self.stop_criteria_loop = stop_criteria_loop
        self.number_population_s = number_population_s
        self.number_of_generations = number_of_generations
        self.k_tournament = k_tournament
        self.time_limit = time_limit

    def get_initial_solutions(self, data) -> list:
        items = data.items
        horizontal = data.horizontal
        transaction_utility = data.transaction_utility

        tu_values = [(i, values) for i, values in enumerate(transaction_utility)]
        candidate_transactions = sorted(tu_values, key=lambda x: x[1], reverse=True)[
            : self.number_of_population
        ]

        initial_solutions = []
        for id_transaction, _ in candidate_transactions:
            items_utility_of_transaction = horizontal[id_transaction]
            sorted_items = sorted(
                items[id_transaction],
                key=lambda x: items_utility_of_transaction.get(x, 0),
                reverse=True,
            )
            solution = [item for item in sorted_items[: self.m]]
            initial_solutions.append(solution)
        return initial_solutions

    @staticmethod
    def evaluation(solution, data: DataWarehouse) -> Union[int, float]:
        if not solution:
            return 0
        
        vertical = data.vertical
        set_id = [vertical[item] for item in solution]
        if len(solution) > 1:
            id_intersection = set.intersection(*set_id)
        else:
            id_intersection = vertical[list(solution)[0]]

        fitness = 0
        for tid in id_intersection:
            fitness += sum([data.horizontal[tid].get(item, 0) for item in solution])
        return fitness

    def wheel_selection(self, utility_values_of_mono_item, total_utility):
        items = list(utility_values_of_mono_item.keys())
        utilities = list(utility_values_of_mono_item.values())

        if len(items) != len(utilities):
            raise ValueError("Not same length of items and utilities !")

        cumulative_probabilities = []
        cumulative_sum = 0
        for utility in utilities:
            cumulative_sum += utility / total_utility
            cumulative_probabilities.append(cumulative_sum)

        random_value = random.random()

        for i, cumulative_probability in enumerate(cumulative_probabilities):
            if random_value <= cumulative_probability:
                return items[i]

    def genetic_operators(
        self, current_population, data: DataWarehouse, alpha, beta
    ) -> list:
        utility_values_of_mono_item = data.utility_values_of_mono_item
        new_population = []
        for first_solution, second_solution in combinations(current_population, 2):
            if len(first_solution) == 0 or len(second_solution) == 0:
                continue

            # Crossover
            if alpha > random.random():
                if self.evaluation(first_solution, data) > self.evaluation(
                    second_solution, data
                ):
                    x = min(
                        first_solution, key=lambda k: utility_values_of_mono_item[k]
                    )
                    y = max(
                        second_solution, key=lambda k: utility_values_of_mono_item[k]
                    )
                else:
                    x = max(
                        first_solution, key=lambda k: utility_values_of_mono_item[k]
                    )
                    y = min(
                        second_solution, key=lambda k: utility_values_of_mono_item[k]
                    )
                first_solution.remove(x)
                if x not in second_solution:
                    second_solution.add(x)
                if y not in first_solution:
                    first_solution.add(y)
                second_solution.remove(y)

            # Mutation
            for solution in [first_solution, second_solution]:
                if beta > random.random():
                    if 0.5 > random.random():
                        # print(solution)
                        x = min(
                            solution,
                            key=lambda k: utility_values_of_mono_item[k],
                            default=None,
                        )
                        if x is not None:
                            solution.remove(x)
                    else:
                        x = self.wheel_selection(
                            utility_values_of_mono_item, data.total_utility
                        )
                        if x not in solution:
                            solution.add(x)
                new_population.append(solution)
        return new_population

    def tournament_selector(self, data: DataWarehouse, population):
        s = []
        while len(s) < self.number_population_s:
            random_tour = random.sample(population, self.k_tournament)
            best_individual = set(max(random_tour, key=lambda x: self.evaluation(x, data)))
            
            if best_individual not in s:
                s.append(best_individual)
        return s

    @staticmethod
    def calculate_total_utility_of_population(population, data: DataWarehouse):
        return sum([Genetic.evaluation(solution, data) for solution in population])

    def get_new_elite_population(
        self, elite_population, new_population, data: DataWarehouse
    ):  # -> tuple[list, int | float]:
        population = elite_population + new_population

        values = [(x, self.evaluation(x, data)) for x in population]
        sorted_values = sorted(values, key=lambda x: x[1], reverse=True)

        sum_values = 0
        new_elite_population = []
        for sol, utility_val in sorted_values:
            if len(new_elite_population) >= self.quantity_of_elite:
                break

            if sol not in new_elite_population:
                new_elite_population.append(sol)
                sum_values += utility_val

        return new_elite_population, sum_values

    def update_parameters(
        self,
        status: bool,
    ):
        if status:
            self.alpha += 0.05
            self.beta -= 0.05
        else:
            self.alpha -= 0.05
            self.beta += 0.05
            
    def create_initial_elite_population(self, data: DataWarehouse):
        elite_population = heapq.nlargest(
            self.quantity_of_elite,
            data.utility_values_of_mono_item.keys(),
            key=lambda x: data.utility_values_of_mono_item[x],
        )
        return [{x} for x in elite_population]

    def solve(self, data: DataWarehouse):
        start_time = time.time()
        elite_population = self.create_initial_elite_population(data)
        population = self.get_initial_solutions(data)

        
        new_population = []
        stop_criteria = 0
        while stop_criteria < self.stop_criteria_loop:
            s = self.tournament_selector(data, population)
            new_population = self.genetic_operators(s, data, self.alpha, self.beta)
            old_util_values = self.calculate_total_utility_of_population(
                population, data
            )
            # print(new_population)
            elite_population, new_util_values = self.get_new_elite_population(
                elite_population, new_population, data
            )
            # print(new_util_values)
            # print(elite_population)

            if new_util_values > old_util_values:
                stop_criteria = 0
                self.update_parameters(True)
            else:
                stop_criteria += 1
                self.update_parameters(False)
            
            if time.time() - start_time > self.time_limit:
                break
        return elite_population