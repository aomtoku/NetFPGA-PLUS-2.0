# *************************************************************************
#
# Copyright 2020 Xilinx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# *************************************************************************
# CMAC user clock
create_clock -period 3.103 -name cmac_clk_0 [get_pins -hier -filter name=~*cmac_port[0]*cmac_gtwiz_userclk_tx_inst/txoutclk_out[0]]
create_clock -period 3.103 -name cmac_clk_1 [get_pins -hier -filter name=~*cmac_port[1]*cmac_gtwiz_userclk_tx_inst/txoutclk_out[0]]
# QDMA clock
create_clock -period 4.000 -name axis_aclk [get_nets u_top_wrapper/axis_aclk]
set_false_path -through [get_ports pci_rst_n]
# Datapath Clock - 340MHz
create_clock -period 2.941 -name dp_clk [get_pins -hier -filter name=~*u_clk_wiz_1/clk_out1]

set axis_aclk [get_clocks -of_object [get_nets u_top_wrapper/axis_aclk]]
foreach cmac_clk [get_clocks -of_object [get_nets u_top_wrapper/cmac_clk*]] {
    set_max_delay -datapath_only -from $axis_aclk -to $cmac_clk 4.000
    set_max_delay -datapath_only -from $cmac_clk -to $axis_aclk 3.103
}

set_false_path -from [get_clocks axis_aclk] -to [get_clocks dp_clk]
set_false_path -from [get_clocks dp_clk] -to [get_clocks axis_aclk]
set_false_path -from [get_clocks cmac_clk_1] -to [get_clocks dp_clk]
set_false_path -from [get_clocks dp_clk] -to [get_clocks cmac_clk_1]
set_false_path -from [get_clocks cmac_clk_0] -to [get_clocks dp_clk]
set_false_path -from [get_clocks dp_clk] -to [get_clocks cmac_clk_0]
set_false_path -from [get_clocks clk_out1_qdma_subsystem_clk_div] -to [get_clocks axis_aclk]
set_false_path -from [get_clocks dp_clk] -to [get_clocks clk_out1_qdma_subsystem_clk_div]

create_pblock pblock_qdma_subsystem
add_cells_to_pblock [get_pblocks pblock_qdma_subsystem] [get_cells -quiet [list u_top_wrapper/xilinx_nic_shell/inst/qdma_subsystem_inst]]
resize_pblock [get_pblocks pblock_qdma_subsystem] -add {SLR1}
