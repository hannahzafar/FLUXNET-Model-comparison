#!/usr/bin/env python
# Process MERRA-2 data for fluxnet analysis

from merra2_tools import MERRA2_ROOT, find_MERRA2_files, create_vzarr_store

# NOTE: How am I going to select years, if Amerflux years varies across sites?
# AmeriFlux FLUXNET spans 1991-2021 across all the sites, individual sites vary, let's just start with that
start_yr, end_yr = [1991, 2021]
freq1 = "tavg"
freq2 = "M"
group = "slv"

fileslist = find_MERRA2_files(
    MERRA2_ROOT, freq1, freq2, group, str(start_yr), str(end_yr)
)

vstore_loc = create_vzarr_store(fileslist)
print(vstore_loc)

