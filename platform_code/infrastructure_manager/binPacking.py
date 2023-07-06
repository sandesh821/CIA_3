#Copyright (c) Microsoft. All rights reserved.
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import random
import binpacking

class BinPacking():
    def __init__(self):
        print("Bin Packing initialized")
    
        # DISTRIBUTES A DICTIONARY OF LENGTHS (KEY-VALUE = ID-LENGTH PAIR) TO A MINIMAL NUMBER IF BINS WHICH CAN HAVE DIFFERENT VOLUME.
    def packing2dOptimizer(b, bin_bucket,loc_bucket):

        # OPTIMIZED BINS WILL BE STORED HERE
        bin_list = []
        # bin_bucket.append(0)
        # bin_bucket.sort(reverse=True)

        # LIST OF DIFFERENCES BETWEEN BIN SIZES
        difference = [0]
        if len(bin_bucket) > 1:
            for index in range(1, len(bin_bucket)):
                difference.append(bin_bucket[0] - bin_bucket[index])

        # FIND THE EXACT BIN WIDTH AS PER USAGE OF PACKINGS
        def checkFinalSize(total):
            bin_width = 0
            for i in bin_bucket: 
                if total <= i: bin_width = i
                else: break
            return bin_width

        # PACK ALL THE VALUES IN BINS WITH MAXIMUM SIZE
        packer_list = binpacking.to_constant_bin_number(b,len(bin_bucket))

        # CREATE A DETAILED DATA OF BINPACKING
        counter = 0
        for packer in packer_list:
            bin_usage = sum(packer.values())
            bin_width = checkFinalSize(bin_usage)
            bin_waste = bin_width - bin_usage
            bin_data = {
                'location': loc_bucket[counter],
                'bin_id': counter,
                'bin_width': bin_width,
                'bin_usage': bin_usage,
                'bin_waste': bin_waste,
                'pack_data': packer
            }
            counter += 1
            bin_list.append(bin_data)

        # PRINT THE LIST
        area_used = 0
        area_covered = 0
        area_waste = 0
        for i in bin_list: 
            area_used += i['bin_width']
            area_covered += sum(i['pack_data'].values())
            area_waste +=  i['bin_waste']

        # TAKES TWO PACKED BINS AND THE AVAILABLE SIZES OF ALL BINS AS ARGUMENT
        def optimizer(small_bin, big_bin):
            dict1 = small_bin['pack_data']
            dict2 = big_bin['pack_data']

            # CREATE A NEW DICTIONARY OF DATA OF THE BOTH PACKED BINS
            new_dict = dict1.copy()
            new_dict.update(dict2)
            max_val = max(list(new_dict.values()))

            # FIND A SUITABLE BIN WITH LOWEST SIZE AND WASTAGE
            for size in bin_bucket:
                if size >= max_val:
                    new_bins = binpacking.to_constant_volume(new_dict,size)    
                    if len(new_bins) <= 2:
                        final_bins = new_bins

            # UPDATE BOTH PACKED BIN VALUES AND RETURNS
            big_bin['pack_data'] = final_bins[0]
            small_bin['pack_data'] = final_bins[1]
            return small_bin, big_bin

        # OPTIMIZE THE BINS TO MINIMIZE THE WASTE
        bin_bucket.sort(reverse=True)

        if len(bin_bucket) > 1:
            for small_bin in bin_list:
                if small_bin['bin_width'] == bin_bucket[-2] and small_bin['bin_waste'] > 0:
                    for big_bin in bin_list:
                        if big_bin['bin_width'] > small_bin['bin_width']:
                            pack_data = list(big_bin['pack_data'].values())
                            for length in pack_data:
                                if length <= small_bin['bin_waste']:
                                    # CALL THE OPTIMIZER
                                    small_bin, big_bin = optimizer(small_bin, big_bin)
                                    
                                    # UPDATE THE BIN DATA
                                    bin_usage = sum(small_bin['pack_data'].values())
                                    bin_width = checkFinalSize(bin_usage)
                                    small_bin['bin_width'] = bin_width
                                    small_bin['bin_usage'] = bin_usage
                                    small_bin['bin_waste'] = bin_width - bin_usage

                                    bin_usage = sum(big_bin['pack_data'].values())
                                    bin_width = checkFinalSize(bin_usage)
                                    big_bin['bin_width'] = bin_width
                                    big_bin['bin_usage'] = bin_usage
                                    big_bin['bin_waste'] = bin_width - bin_usage

                                    break

            # SORT THE OPTIMIZED BINS BY BIN SIZE
            bin_list = sorted(bin_list, key = lambda i: i['bin_width'], reverse = True)

            # PRINT THE LIST
            area_used = 0
            area_covered = 0
            area_waste = 0
            for i in bin_list: 
                # print("Bin Cluster: ", i['location'])
                # print("Bin", i['bin_width'],":",i['pack_data'], i['bin_waste'])
                area_used += i['bin_width']
                area_covered += sum(i['pack_data'].values())
                area_waste +=  i['bin_waste']

        return bin_list