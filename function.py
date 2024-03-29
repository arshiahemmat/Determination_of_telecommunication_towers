import numpy as np
from math import exp,floor
import random
import math
import openfile

blocks_population, problem_config = openfile.read_files()

def conv(x_alley:list, y_d:list)->float:
    alley_loc = np.array([x_alley])
    d_loc = np.array([y_d])
    sigma = np.array([[1/8,0],[0,1/8]])
    dif_loc = alley_loc-d_loc
    dif_loc_t = dif_loc.T
    temp = np.matmul(dif_loc,sigma)
    temp2 = np.matmul(temp, dif_loc_t)
    return exp(-1/2*temp2)

def calculate_coordinates(location):
    x = location//20
    y = location % 20
    return [x,y]

def unique_random_list(length, start, end):
    """
    Generates a list of unique random integers within a given range.

    Args:
        length (int): The length of the list to generate.
        start (int): The start of the range (inclusive).
        end (int): The end of the range (exclusive).

    Returns:
        A list of unique random integers.
    """
    if length > end - start:
        raise ValueError("Cannot generate unique list of length greater than range.")
    nums = set()
    while len(nums) < length:
        nums.add(random.randint(start, end-1))
    return list(nums)

def euclidean_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def calulacte_conv_block_tower():
    dp = list() #conv
    dp2 = list() # Distance
    for i in range(0,400): #Tower location
        tower_coordinate = calculate_coordinates(i)
        each_list = list()
        each_dp_2 = list()
        for j in range(0,400): #Blocks location
            block_coordinate = calculate_coordinates(j)
            each_list.append(conv(block_coordinate, tower_coordinate))
            each_dp_2.append(euclidean_distance(tower_coordinate, block_coordinate))
        dp.append(each_list)
        dp2.append(each_dp_2)
    return dp,dp2

def assign_blocks(distance, tower_coordination):
    # blocks_population => population given from input
    # assigning eah neighbour to a tower based on weather that tower is consider closets to that neighbour
    each_tower_population = list([0 for x in range(400)]) #the indices are tower_ids and value is population assigned to that tower
    assign_dict = dict()
    for each in tower_coordination:
        # id_coordinate = each[0]*20 + each[1]
        assign_dict[each] = list()
        each_tower_population[each] = 0

    for i in range(400): # neighbours location
        min_d = 1e10
        min_id = None
        for each in tower_coordination:
            # id_coordinate = each[0]*20 + each[1]
            if distance[i][each] < min_d:
                min_d = distance[i][each]
                min_id = each
        # print(min_id, tower_coordination)
        assign_dict[min_id].append(i)
        each_tower_population[min_id] += blocks_population[i]
    # assign_dict => each tower has a list of neighbours
    return assign_dict, each_tower_population

dp = calulacte_conv_block_tower()

def estimate_max_bound_for_eachTower(tower_id :int, assign_blocks :dict, each_tower_population:dict , distance):
    # tower_id = int ,  assign_blocks =map_list , each_tower_population= list
    # it's assumed that tower_id is an int could be two dimentioned by calculate_coordinates(tower_id)
    assigned_neighbour = assign_blocks[tower_id] # list of neighbours assigned to tower_id

    # init the farthest to first neighbour
    Farthest_neighbour = assigned_neighbour[0]

    max_dis = distance[tower_id][assigned_neighbour[0]]
    # calculate the Farthest neighbour to the chosen tower
    for x in assigned_neighbour:
        if distance[x][tower_id] > max_dis:
            max_dis = distance[x][tower_id]
            Farthest_neighbour = x
        
    max_bound_towerId = ((3* each_tower_population[tower_id])//conv(calculate_coordinates(Farthest_neighbour), calculate_coordinates(tower_id)))
    return max_bound_towerId

def esitimate_bound_for_Towerlist(chromosome:list,assign_blocks :dict, each_tower_population:dict , distance , total_bound):
    # we use proportion to assign the max_bound for each toer based on totoal bound give
    esitimated_max_bound = []
    chosen_bound = []
    sum_estimated_max_bound = 0
    normalization = 1000
    for gene in chromosome :
        max_bound_each = math.ceil(estimate_max_bound_for_eachTower(gene, assign_blocks, each_tower_population , distance) / normalization)
        esitimated_max_bound.append(max_bound_each)
        sum_estimated_max_bound += max_bound_each

    step = total_bound / sum_estimated_max_bound
    for i in range(0, len(chromosome)) : 
        esitimated_max_bound[i] = step * esitimated_max_bound[i]
        tmp = random.randint(1,int(esitimated_max_bound[i]+2))
        chosen_bound.append(tmp)
    # chosen_bound is a list that returns a approximated bound for each gene in choromosome
    return chosen_bound

def calculate_satisfaction(assign_dict: dict, each_tower_population: list, bandwidth_towers: dict):

    # inputs
        # 1- assign_dict -> see what blocks are assigned to what tower
        # 2- each_tower_population -> needed for the calculation of the bound of each block
    # requirements
        # 1- number of towers + their bound -> calculate cost of towers
        # 2- population of each block and the tower assigned to that block -> calculate score of each block
    
    

    # getting costs and scores from config-file
    cost_to_build_tower = problem_config['tower_construction_cost']
    cost_to_increase_bandwidth = problem_config['tower_maintanance_cost']
    user_satisfaction_levels = problem_config['user_satisfaction_levels']
    user_satisfaction_scores = problem_config['user_satisfaction_scores']

    total_increasd_bound = 0
    total_score = 0

    for i in assign_dict:
        # get boundwidth of tower
        #bound_of_tower = estimate_max_bound_for_eachTower(i)
        bound_of_tower = bandwidth_towers[i]
        # add cost for increased bound
        total_increasd_bound += bound_of_tower * cost_to_increase_bandwidth
        # calculate score for each block assigned to tower[i]
        for block in assign_dict[i]:
            # getting the population of the block
            block_population = blocks_population[block]
            # need to specify boundwidth for each block
            block_bound = (block_population / each_tower_population[i]) * bound_of_tower
            # getting each user
            bound_of_each_user_in_block = block_bound / block_population
            # calculate the score
            score = 0
            for j in reversed(range(len(user_satisfaction_levels))):
                if bound_of_each_user_in_block >= user_satisfaction_levels[j]:
                    score = user_satisfaction_scores[j]
                    break
            # update total_score
            total_score += (score * block_population)
    # calculate the cost of building towers + their increased bandwidth
    total_cost_of_towers = total_increasd_bound + (len(assign_dict) * cost_to_build_tower)
            
    # return -abs(total_cost_of_towers) + total_score
    return total_score/abs(total_cost_of_towers)

