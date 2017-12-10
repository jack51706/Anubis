"""The target command."""

import socket

import nmap
import requests
import shodan

from anubis.API import *
from anubis.utils.ColorPrint import *

api = shodan.Shodan(SHODAN_KEY)
from .base import Base


class Target(Base):
	"""Main enumeration module"""
	domains = []
	ip = ""

	def init(self):
		try:
			self.ip = socket.gethostbyname(self.options["TARGET"])
		except:
			ColorPrint.red(
				"Error connecting to target! Make sure you spelled it correctly and it is a reachable address")

	def run(self):
		self.init()
		print("Searching for subdomains for", self.ip)
		self.subdomain_hackertarget()
		self.search_virustotal()
		print("Found", len(self.domains), "domains")

		# remove duplicates
		dedupe = set(self.domains)
		for domain in dedupe:
			ColorPrint.green(domain)

		should_scan_host = input("Scan host " + self.ip + "? (y or n)\n")
		if should_scan_host == "y" or should_scan_host == "yes":
			self.scan_host()

	def scan_host(self):
		print("Scanning for services...")
		nm = nmap.PortScanner()
		nm.scan(hosts=self.ip, arguments='-nPn -sV -sC')
		for host in nm.all_hosts():
			print('----------------------------------------------------')
			print('Host : %s (%s)' % (host, nm[host].hostname()))
			print('State : %s' % nm[host].state())
			for proto in nm[host].all_protocols():
				print('----------')
			print('Protocol : %s' % proto)
			lport = nm[host][proto].keys()
			for port in lport:
				print('port : %s\tstate : %s' % (port, nm[host][proto][port]))

	def subdomain_hackertarget(self):
		headers = {
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36', }
		params = (('q', self.options["TARGET"]),)

		results = requests.get('http://api.hackertarget.com/hostsearch/',
		                       headers=headers, params=params)
		results = results.text.split('\n')
		for res in results:
			if res.split(",")[0] != "":
				self.domains.append(res.split(",")[0])

	def search_virustotal(self):
		headers = {'dnt': '1', 'accept-encoding': 'gzip, deflate, br',
		           'accept-language': 'en-US,en;q=0.9,it;q=0.8',
		           'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
		           'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		           'authority': 'www.virustotal.com',
		           'cookie': 'VT_PREFERRED_LANGUAGE=en', }
		res = requests.get('https://www.virustotal.com/en/domain/' + self.options[
			"TARGET"] + '/information/', headers=headers)
		if res.status_code == 403:
			ColorPrint.red(
				"VirusTotal is currently ratelimiting this IP - go to virustotal.com and complete the captcha to continue.")
			return
		scraped = res.text
		trim_to_subdomain = scraped[
		                    scraped.find(" Observed subdomains"):scraped.rfind(
			                    "btn-more-observed-subdomains")].split('\n')
		for entry in trim_to_subdomain:
			if entry.strip().endswith(self.options["TARGET"]):
				self.domains.append(entry.strip())

	def search_shodan(self):
		if self.ip != "":
			try:
				results = api.search(self.ip)
				print('Results found: %s' % results['total'])
				for result in results['matches']:
					print('IP: %s' % result['ip_str'])
					print(result['data'])
			except shodan.APIError as e:
				print('Error: %s' % e)
