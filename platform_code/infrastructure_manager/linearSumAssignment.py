#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from scipy.optimize import linear_sum_assignment

class NodeManagement():
    def __init__(self):
        print("Node Management initialized")

    def create_waste_matrix(self, jobs, bins, max_waste):
        large_cost_val = 100000
        waste_matrix = []
        for bin in bins:
            k = []
            for job in jobs:
                diff = job - bin[1]
                #Case 1: Job cannot fit the compute node
                if diff > 0:
                    k.append(large_cost_val)
                #Case 2: Wasteful assignment
                elif diff <0 and abs(diff)>max_waste:
                    k.append(large_cost_val)
                #Case 3: Other cases
                else:
                    k.append(abs(job - bin[1]))
            waste_matrix.append(k)
        return waste_matrix

    def remove_wasteful_assignments(self, row_inds, col_inds, waste_matrix, max_waste):
        node_inds, job_inds, kill_node_inds = [], [], []
        for row_ind, col_ind in zip(row_inds, col_inds):
            #print(f"NODE#:{row_ind}, JOB: {col_ind}, Waste: {waste_matrix[row_ind][col_ind]}")
            if waste_matrix[row_ind][col_ind] <= max_waste:
                node_inds.append(row_ind)
                job_inds.append(col_ind)
            else:
                kill_node_inds.append(row_ind)
        return node_inds, job_inds, kill_node_inds

    def apply_matching(self, jobs, bins, max_waste=2):
        waste_matrix = self.create_waste_matrix(jobs, bins, max_waste)
        initial_node_inds, initial_job_inds = linear_sum_assignment(waste_matrix)
        assigned_node_inds, assigned_job_inds, to_be_killed_node_ids = self.remove_wasteful_assignments(initial_node_inds, initial_job_inds, waste_matrix, max_waste)
        return assigned_node_inds, assigned_job_inds, to_be_killed_node_ids

if __name__ == '__main__':

    jobs = [32, 16, 8, 8, 4, 4, 4, 16, 8] #vCPU requirements
    bins = [('westus',64),('westus',16), ('eastus',4), ('eastus',4), ('westus',4), ('westus',8), ('westus',32)] #Available compute resources
    nd = NodeManagement()
    assigned_node_inds, assigned_job_inds, to_be_killed_node_ids = nd.apply_matching(jobs, bins)

    #Logic to kill unassigned nodes
    #We can also see if the killed nodes frees up cpu. if yes, we can add freed up vCPUs to the corresponding DC
    #Then apply bin packing