import sys

# This script calculates how much energy main memory has consumed based on CACTI and the stats file, and then adds it to the energy of everything else as estimated by McPAT to get a total number.
# The CACTI output, McPAT, then stats file is parsed.

if len(sys.argv) != 5:
    print("\n Argument format: <new stats file> <cpu mcpat out> <pim mcpat out> <name of tsv file for totals> \n")
    exit(0)

print("\tCalculating hybrid memory cube energy using memory access stats")

stats = open(str(sys.argv[1]), 'r')
stat_lines = stats.readlines()
stats.close()

sim_seconds = 0
num_reads = 0
num_writes = 0
num_act_pre = 0

total_energy = 0

gem5_act_total = 0
gem5_read_total = 0
gem5_write_total = 0
gem5_pre_total = 0
gem5_act_back_total = 0
gem5_pre_back_total = 0
gem5_refr_total = 0
pim_act_total = 0
pim_read_total = 0
pim_write_total = 0
pim_pre_total = 0
pim_act_back_total = 0
pim_pre_back_total = 0
pim_refr_total = 0
host_act_total = 0
host_read_total = 0
host_write_total = 0
host_pre_total = 0
host_act_back_total = 0
host_pre_back_total = 0
host_refr_total = 0

pim_reads = 0
pim_writes = 0
host_reads = 0
host_writes = 0
l2_accesses = 0

reads_from_pim = 0
writes_to_pim = 0

# TODO: could be interesting to look at interconnect accesses, committed instructions, memory accesses
for line in stat_lines[::-1]:
    cols = line.split()
    if len(cols):
        if cols[0] == "total_sim_seconds" in cols[0]:
	        sim_seconds = float(cols[1])

        if "reads_from_pim" in cols[0]:
            reads_from_pim += float(cols[1])  
        if "writes_to_pim" in cols[0]:
            writes_to_pim += float(cols[1])  

        if "total_reads" in cols[0]:
            num_reads += float(cols[1])
            if "pim" in cols[0]:
                pim_reads = float(cols[1])
            else:
                host_reads = float(cols[1])

        if "total_writes" in cols[0]:
            num_writes += float(cols[1])
            if "pim" in cols[0]:
                pim_writes = float(cols[1])
            else:
                host_writes = float(cols[1])

        if "activations" in cols[0]:
            num_act_pre += float(cols[1])  
            if "pim" in cols[0]:
                pim_act_pre = float(cols[1])
            else:
                host_act_pre = float(cols[1])

        if "total_actEnergy" in cols[0]:
            gem5_act_total += float(cols[1])/1e12 # Stats file records energy in pJ (1E-12 J)
            if "pim" in cols[0]:
                pim_act_total += float(cols[1])/1e12
            else:
                host_act_total += float(cols[1])/1e12

        if "total_readEnergy" in cols[0]:
            gem5_read_total += float(cols[1])/1e12
            if "pim" in cols[0]:
                pim_read_total += float(cols[1])/1e12
            else:
                host_read_total += float(cols[1])/1e12

        if "total_writeEnergy" in cols[0]:
            gem5_write_total += float(cols[1])/1e12
            if "pim" in cols[0]:
                pim_write_total += float(cols[1])/1e12
            else:
                host_write_total += float(cols[1])/1e12

        if "total_preEnergy" in cols[0]:
            gem5_pre_total += float(cols[1])/1e12
            if "pim" in cols[0]:
                pim_pre_total += float(cols[1])/1e12
            else:
                host_pre_total += float(cols[1])/1e12

        if "total_actBackEnergy" in cols[0]:
            gem5_act_back_total += float(cols[1])/1e12
            if "pim" in cols[0]:
                pim_act_back_total += float(cols[1])/1e12
            else:
                host_act_back_total += float(cols[1])/1e12

        if "total_preBackEnergy" in cols[0]:
            gem5_pre_back_total += float(cols[1])/1e12
            if "pim" in cols[0]:
                pim_pre_back_total += float(cols[1])/1e12
            else:
                host_pre_back_total += float(cols[1])/1e12

        if "total_refreshEnergy" in cols[0]:
            gem5_refr_total += float(cols[1])/1e12  
            if "pim" in cols[0]:
                pim_refr_total += float(cols[1])/1e12
            else:
                host_refr_total += float(cols[1])/1e12

        if cols[0] == "system.l2.ReadReq_accesses::total" or cols[0] == "system.l2.Writeback_accesses::total":
            l2_accesses += float(cols[1]) 

# Compare total energy by type of operation
activ_rw_prech = gem5_act_total + gem5_read_total + gem5_write_total + gem5_pre_total
act_pre_back = gem5_act_back_total + gem5_pre_back_total
total_energy += activ_rw_prech
total_energy += gem5_refr_total 
total_energy += act_pre_back

pim_mem_energy = pim_refr_total + pim_pre_back_total + pim_act_back_total + pim_pre_total + pim_write_total + pim_read_total + pim_act_total 
host_mem_energy = host_refr_total + host_pre_back_total + host_act_back_total + host_pre_total + host_write_total + host_read_total + host_act_total 

######################################################################################################
# For both host and PIM McPAT outputs
power_types = ["Processor", "Total Cores", "Total L2s", "Total NoCs (Network/Bus)", "Total MCs"]
name = "no name"
######################################################################################################

print("Getting host core, cache, interconnect, and memory controller McPAT numbers")
mcpat_file = open(str(sys.argv[2]), 'r') 
mcpat_lines = mcpat_file.readlines()
mcpat_file.close()

watts = 0
host_power_data = {}

# Finds first Gate Leakage and Runtime Dynamic power entries, which are for the whole system
for line in mcpat_lines:
    if ':' in line:
        name = line.strip().split(':')[0]
    if "Subthreshold Leakage" in line:
        host_power_data[name] = float(line.split()[3])
    if "Gate Leakage" in line:
        host_power_data[name] += float(line.split()[3])
    if "Runtime Dynamic" in line:
        host_power_data[name] += float(line.split()[3])
        if "Total MCs" in name:
            break

watts = sum(host_power_data.values()) / 2
host_energy = watts * sim_seconds
total_energy += host_energy

######################################################################################################

print("Getting pim core and memory controller McPAT numbers")
mcpat_file = open(str(sys.argv[3]), 'r') 
mcpat_lines = mcpat_file.readlines()
mcpat_file.close()

watts = 0
pim_power_data = {}

# Finds first Gate Leakage and Runtime Dynamic power entries, which are for the whole system
for line in mcpat_lines:
    if ':' in line:
        name = line.strip().split(':')[0]
    if "Subthreshold Leakage" in line:
        pim_power_data[name] = float(line.split()[3])
    if "Gate Leakage" in line:
        pim_power_data[name] += float(line.split()[3])
    if "Runtime Dynamic" in line:
        pim_power_data[name] += float(line.split()[3])
        if "Total MCs" in name:
            break

watts = sum(pim_power_data.values()) / 2
pim_energy = 0
if watts > 0: 
    pim_energy = watts * sim_seconds
    total_energy += pim_energy

print("\tTotal energy is " + str(total_energy) + " J. ")
power = total_energy/sim_seconds
print("\tAverage power is " + str(power) + " J. ")

result_file = open(str(sys.argv[4]), 'a')

# Energy breakdowns
result_file.write('%.6f' % total_energy + "\t")
result_file.write('%.6f' % (host_power_data["Total Cores"] * sim_seconds) + "\t")
result_file.write('%.6f' % (pim_power_data["Total Cores"] * sim_seconds) + "\t")
result_file.write('%.6f' % (host_power_data["Total MCs"] * sim_seconds) + "\t")
result_file.write('%.6f' % (pim_power_data["Total MCs"] * sim_seconds) + "\t")
result_file.write('%.6f' % (host_mem_energy) + "\t")
result_file.write('%.6f' % (pim_mem_energy) + "\t")
result_file.write('%.6f' % (host_power_data["Total L2s"] * sim_seconds) + "\t")
result_file.write('%.6f' % (host_power_data["Total NoCs (Network/Bus)"] * sim_seconds) + "\t")

# Power breakdowns 
result_file.write('%.4f' % power + "\t")
result_file.write('%.6f' % host_power_data["Total Cores"] + "\t")
result_file.write('%.6f' % pim_power_data["Total Cores"] + "\t")
result_file.write('%.6f' % host_power_data["Total MCs"] + "\t")
result_file.write('%.6f' % pim_power_data["Total MCs"] + "\t")
result_file.write('%.6f' % (host_mem_energy / sim_seconds)+ "\t")
result_file.write('%.6f' % (pim_mem_energy / sim_seconds) + "\t")
result_file.write('%.6f' % host_power_data["Total L2s"] + "\t")
result_file.write('%.6f' % host_power_data["Total NoCs (Network/Bus)"] + "\t")

# Host-PIM communication breakdown
result_file.write('%.0f' % reads_from_pim + "\t")
result_file.write('%.0f' % writes_to_pim + "\t")

# Memory access breakdowns 
result_file.write('%.0f' % num_reads + "\t")
result_file.write('%.0f' % host_reads + "\t")
result_file.write('%.0f' % pim_reads + "\t")
result_file.write('%.0f' % num_writes + "\t")
result_file.write('%.0f' % host_writes + "\t")
result_file.write('%.0f' % pim_writes + "\t")
result_file.write('%.0f' % num_act_pre + "\t")
result_file.write('%.0f' % host_act_pre + "\t")
result_file.write('%.0f' % pim_act_pre + "\t")

# Memory energy breakdowns
result_file.write('%.8f' % host_refr_total + "\t")
result_file.write('%.6f' % pim_refr_total + "\t")
result_file.write('%.8f' % host_act_total + "\t")
result_file.write('%.6f' % pim_act_total + "\t")
result_file.write('%.8f' % host_read_total + "\t")
result_file.write('%.6f' % pim_read_total + "\t")
result_file.write('%.6f' % host_write_total + "\t")
result_file.write('%.6f' % pim_write_total + "\t")
result_file.write('%.6f' % host_pre_total + "\t")
result_file.write('%.6f' % pim_pre_total + "\t")
result_file.write('%.6f' % host_act_back_total + "\t")
result_file.write('%.6f' % pim_act_back_total + "\t")
result_file.write('%.6f' % host_pre_back_total + "\t")
result_file.write('%.6f' % pim_pre_back_total + "\t")


result_file.write("\n")
result_file.close()

