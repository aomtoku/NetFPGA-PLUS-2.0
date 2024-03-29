#!/usr/bin/env python3
#
# Copyright (c) 2015 University of Cambridge
# All rights reserved.
#
# This software was developed by Stanford University and the University of Cambridge Computer Laboratory 
# under National Science Foundation under Grant No. CNS-0855268,
# the University of Cambridge Computer Laboratory under EPSRC INTERNET Project EP/H040536/1 and
# by the University of Cambridge Computer Laboratory under DARPA/AFRL contract FA8750-11-C-0249 ("MRC2"), 
# as part of the DARPA MRC research programme.
#
# @NETFPGA_LICENSE_HEADER_START@
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @NETFPGA_LICENSE_HEADER_END@
#


from RouterLib import *

import re

import sys
import os

################################################################
# Name: nftest_set_router_MAC
#
# Sets the MAC of a port
#
# Arguments: ifaceName string
#            MAC       string in format xx:xx:xx:xx:xx:xx
#
# Return:
################################################################
def nftest_set_router_MAC(ifaceName, MAC):
	if not ifaceName.startswith('nf'):
		print("Interface has to be an nf2cX interface")
		sys.exit(1)
	portNum = int(ifaceName[2:3])
	portNum += 1
	set_router_MAC(portNum, MAC)

################################################################
# Name: nftest_get_router_MAC
#
# Gets the MAC of a port
#
# Arguments: ifaceName string
#
# Return: MAC address of interface in xx:xx:xx:xx:xx:xx format
################################################################
def nftest_get_router_MAC(ifaceName):
	if not ifaceName.startswith('nf'):
		print("Interface has to be an nf2cX interface")
		sys.exit(1)
	portNum = int(ifaceName[2:3])
	portNum += 1
	return get_router_MAC(portNum)

################################################################
# Name: nftest_add_LPM_table_entry
#
# Adds an entry to the routing table in the hardware.
#
# Arguments: entryIndex  int
#            subnetIP    string in format w.x.y.z
#            subnetMask  string in format w.x.y.z
#            nextHopIP   string in format w.x.y.z
#            outputPort  one-hot-encoded ports
#                        0x01 is MAC0, 0x02 is CPU0,
#                        0x04 is MAC1, 0x08 is CPU1,
#                        0x10 is MAC2, 0x20 is CPU2,
#                        0x40 is MAC3, 0x80 is CPU3,
# Return:
################################################################
def nftest_add_LPM_table_entry(entryIndex, subnetIP, subnetMask, nextHopIP, outputPort):
	add_LPM_table_entry(entryIndex, subnetIP, subnetMask, nextHopIP, outputPort)

################################################################
# Name: nftest_invalidate_LPM_table
#
# clears all entries in the routing table (by setting everything
# to 0)
#
# Arguments: depth       int
#
# Return:
################################################################
def nftest_invalidate_LPM_table(depth):
	for i in range(depth):
		invalidate_LPM_table_entry(i)

################################################################
# Name: nftest_invalidate_LPM_table_entry
#
# clears an entry in the routing table (by setting everything
# to 0)
#
# Arguments: entryIndex  int
#
# Return:
################################################################
def nftest_invalidate_LPM_table_entry(entryIndex):
	invalidate_LPM_table_entry(entryIndex)

################################################################
# Name: nftest_contains_LPM_table_entries
#
# Compares the expected_entries array against what is in hardware
# returning any expected_entries that do not exist in hardware
#
# Arguments: expected_entries array of entries, with each field
# separated by a hyphen ('-')
#
# Return: array of missing entries as strings
################################################################
def nftest_contains_LPM_table_entries(expected_entries):
	actual_entries = {}
	missing_entries = []

	for i in range(LPM_LUT_ROWS - 1):
		entry = get_LPM_table_entry(i)
		actual_entries[entry] = entry
	for expected_entry in expected_entries:
		try:
			tmp = actual_entries[expected_entry]
		except(KeyError):
			missing_entries.append(expected_entry)
	return missing_entries

################################################################
# Name: nftest_add_dst_ip_filter_entry
#
# Adds an entry in the IP destination filtering table. Any
# packets with IP dst addr that matches in this table is sent to
# the CPU. This is also used to set the IP address of the
# router's ports.
#
# Arguments: entryIndex  int
#            destIP      string in format w.x.y.z
# Return:
################################################################
def nftest_add_dst_ip_filter_entry(entryIndex, destIP):
	add_dst_ip_filter_entry(entryIndex, destIP)

################################################################
# Name: nftest_invalidate_dst_ip_filter_table
#
# Removes contents of the IP destination filtering table by
# setting all entries to 0.
#
# Arguments: depth       int
#
# Return:
################################################################
def nftest_invalidate_dst_ip_filter_table(depth):
	for i in range(depth):
		invalidate_dst_ip_filter_entry(i)

################################################################
# Name: nftest_invalidate_dst_ip_filter_entry
#
# Removes an entry from the IP destination filtering table by
# setting it to 0.
#
# Arguments: entryIndex  int
#
# Return:
################################################################
def nftest_invalidate_dst_ip_filter_entry(entryIndex):
	invalidate_dst_ip_filter_entry(entryIndex)

################################################################
# Name: nftest_contains_dst_ip_filter_entries
#
# Compares the expected_ips array against what is in hardware
# returning any expected_ips that do not exist in hardware
#
# Arguments: expected_ips array of ip address strings
#
# Return: array of missing ip address strings
################################################################
def nftest_contains_dst_ip_filter_entries(expected_ips):
	actual_ips = {}
	missing_ips = []
	for i in range(FILTER_ROWS - 1):
		ip = get_dst_ip_filter_entry(i)
		actual_ips[ip] = ip
	for expected_ip in expected_ips:
		try:
			tmp = actual_ips[dotted(expected_ip)]
		except(KeyError):
			missing_ips.append(expected_ip)
	return missing_ips

################################################################
# Name: nftest_add_ARP_table_entry
#
# adds an entry to the hardware's ARP table.
#
# Arguments: entryIndex  int
#            nextHopIP   string in format w.x.y.z
#            nextHopMAC  string in format w.x.y.z
#
# Return:
################################################################
def nftest_add_ARP_table_entry(entryIndex, nextHopIP, nextHopMAC):
	add_ARP_table_entry(entryIndex, nextHopIP, nextHopMAC)

################################################################
# Name: nftest_invalidate_ARP_table
#
# clears all entries from the hardware's ARP table by setting to
# all zeros.
#
# Arguments: depth       int
#
# Return:
################################################################
def nftest_invalidate_ARP_table(depth):
	for i in range(depth):
		invalidate_ARP_table_entry(i)

################################################################
# Name: nftest_invalidate_ARP_table_entry
#
# clears an entry from the hardware's ARP table by setting to
# all zeros.
#
# Arguments: entryIndex  int
#
# Return:
################################################################
def nftest_invalidate_ARP_table_entry(entryIndex):
	invalidate_ARP_table_entry(entryIndex)

################################################################
# Name: nftest_contains_ARP_table_entries
#
# Compares the expected_entries array against what is in hardware
# returning any expected_entries that do not exist in hardware
#
# Arguments: expected_entries array of entries, with each field
# separated by a hyphen ('-')
#
# Return: array of missing entries as strings
################################################################
def nftest_contains_ARP_table_entries(expected_entries):
	actual_entries = {}
	missing_entries = []
	for i in range(ARP_LUT_ROWS - 1):
		entry = get_ARP_table_entry(i)
		actual_entries[entry] = entry
	for expected_entry in expected_entries:
		try:
			tmp = actual_entries[expected_entry]
		except(KeyError):
			missing_entries.append(expected_entry)
	return missing_entries

################################################################
# Name: nftest_invalidate_all_tables
#
# Invalidates the entries in the following tables:
#  - ARP
#  - LPM
#  - dst IP filter
#
# Arguments: arp_depth             int
#            lpm_depth             int
#            dst_ip_filter_depth   int
#
# Default values taken from reg_defines.ROUTER_OP_LUT_*_TABLE_DEPTH
#
# Return:
################################################################
def nftest_invalidate_all_tables():
	invalidate_all_tables()
