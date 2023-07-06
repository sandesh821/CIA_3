#Copyright (c) Microsoft. All rights reserved.
from   workflow.common.WindPlotly import WindPlotly
#from workflow.common import SolarPlotly
# from  workflow.common.PricePlotly import PricePlotly
# from workflow.common.DemandPlotly import DemandPlotly

def domainFactory(domain_name):
   # domains = {"demand": DemandPlotly, "solar":SolarPlotly, "wind": WindPlotly, "price":PricePlotly}
    domains = {"wind": WindPlotly}
    return domains[domain_name]