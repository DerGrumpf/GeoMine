import json
import requests
import glob
import gzip
import re
import sys
from pprint import pprint
from icmplib import traceroute, ping
from multiprocessing.pool import Pool
from functools import reduce
from operator import add
from model import Tag
from dataclasses import dataclass, asdict, field

@dataclass(match_args=False)
class GeoIP:
	status: str = field(default_factory=str)
	country: str = field(default_factory=str)
	countryCode: str = field(default_factory=str)
	region: str = field(default_factory=str)
	regionName: str = field(default_factory=str)
	city: str = field(default_factory=str)
	zip: str = field(default_factory=str)
	lat: float = field(default_factory=float)
	lon: float = field(default_factory=float)
	timezone: str = field(default_factory=str)
	isp: str = field(default_factory=str)
	org: str = field(default_factory=str)
	query: str = field(default_factory=str)

	@staticmethod
	def from_json(data):
		d = json.loads(data)
		del d['as']
		return GeoIP(**d)

def is_public_ip(ip):
    ip = list(map(int, ip.strip().split('.')[:2]))
    if ip[0] == 10: return False
    if ip[0] == 127: return False
    if ip[0] == 172 and ip[1] in range(16, 32): return False
    if ip[0] == 192 and ip[1] == 168: return False
    if ip[0] == 0 and ip[1] == 0: return False
    return True

def get_ips():
	logs = glob.glob("/usr/local/bin/*/logs/*.gz")
	pattern = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
	ips = list()

	for log in logs:
		with gzip.open(log, 'rb') as f:
			ips.append(re.findall(pattern, f.read().decode("utf-8")))

	logs = glob.glob("/usr/local/bin/*/logs/latest.log")

	for log in logs:
		with open(log, 'r') as f:
			ips.append(re.findall(pattern, f.read()))

	ips = list(set(reduce(add, ips)))
	ips = sorted(ips, key = lambda ip: [int(ip) for ip in ip.split(".")])
	ips = [ip for ip in ips if is_public_ip(ip)]

	return ips

def lookup(ip):
	request_url = 'http://ip-api.com/json/' + ip
	response = requests.get(request_url)
	result = response.content.decode()
	try:
		return GeoIP.from_json(result)
	except:
		return {"status": "fail"}

def get_trace(ip):
	hops = traceroute(ip, fast=True)
	hops = [hop for hop in hops if is_public_ip(hop.address)]
	dis = hops[-1].distance
	hops = [tag_factory(hop.address, hop.is_alive, hop.distance, []) for hop in hops]
	hops = [hop for hop in hops if hop is not None]
	return (hops, dis)

def tag_factory(ip, is_alive, hops, trace):
	geoip = lookup(ip)
	if type(geoip) is dict: return 
	return Tag(
		ip= ip,
		isp= geoip.isp,
		city= geoip.zip + ' ' + geoip.city,
		country= geoip.country + ', ' + geoip.countryCode,
		coordinates= (geoip.lat, geoip.lon),
		hops= hops,
		is_alive= is_alive,
		trace= trace
		)

def get_data(ip):
	print(ip)
	trace, dis = get_trace(ip)
	return tag_factory(
		ip,
		ping(ip, interval=0.2).is_alive,
		dis,
		trace
		)
	
def main():
	ips = get_ips()
	print("Ips to check:", len(ips))
	with Pool(20) as pool:
		data = pool.map(get_data, ips)
		data = [asdict(d) for d in data if d is not None]
	with open("ips.json", "w") as f:
		json.dump(data, f)	

if __name__ == '__main__':
	main()
