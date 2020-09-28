#!/usr/bin/env python3
# Script for automating schoolwork, attending class and generating a portfolio
# Maybe, but very small maybe, I will turn this into an AI

import sys
import os
import time
import requests
from bs4 import BeautifulSoup as Soup
from http.client import responses
from getpass import getpass
import hashlib
import re
import json

class HVABrightSpaceSSO:

	def __init__(self, base = "", username=None, password=None):
		self.base = "https://dlo.mijnhva.nl"
		self.adfs = self.base
		self.username = username
		self.password = password
		self.s = requests.Session()

	def prepare(self):
		dpage = self.s.get(self.adfs, allow_redirects=True).text
		soup = Soup(dpage, "html.parser")
		options = soup.find("form", {"id":"options"})
		self.adfs = str(options['action'])

	def Login(self, username=None, password=None):

		if self.username:
			username = self.username

		if self.password:
			password = self.password

		# request username if needed
		if username == None or len(username) < 3:
			username = str(input("username: "))
		
		# request password if needed
		if password == None or len(password) < 3:
			password=str(getpass())

		# Input validation
		if len(password) > 128:
			raise BaseException("Password too long, must be less than 128 characters.")


		credentials = {
			"UserName":username,
			"Password":password,
			"AuthMethod": "FormsAuthentication"
		}

		# Get the URL with the csrf token
		self.prepare()

		# Make the login request
		ADFSResponse = self.s.post(self.adfs, data=credentials, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}, allow_redirects=True)

		soup = Soup(ADFSResponse.text, "html.parser")

		# Check if an error occured
		error = soup.find("span", {"id":"errorText"})
		if error:
			error = error.text

		if error:
			raise BaseException(str(error))

		print("[+] Authenticated with domain controller SSO!")

		# Fetch redirect location for active directory SAML authentication
		ADController = soup.find("form", {"name":"hiddenform"})
		if not ADController:
			raise BaseException("An unknown error occured while authenticating with the controller.")

		ADController = ADController['action']
		if not ADController:
			raise BaseException("An unknown error occured while authenticating with the controller: No engine in response.")

		# Fetch SAML session
		SAMLResponse = soup.find("input", {"name":"SAMLResponse"})
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLResponse = SAMLResponse['value']
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLSession = {"SAMLResponse":SAMLResponse}

		# Finally log in at domain controller
		ADCTLResponse = self.s.post(ADController, data=SAMLSession, allow_redirects=True)

		# Check if authentication succeeded
		if ADCTLResponse.status_code != 200:
			raise BaseException("Authentication failure: "+responses[ADCTLResponse.status_code])

		print("[+] Got SAML session, can now authenticate with application.")


		# Continue to brightspace controller
		soup = Soup(ADCTLResponse.text, "html.parser")

		# Get the processform
		DLOController = soup.find("form", {"id":"ProcessForm"})

		if not DLOController:
			raise BaseException("Failed to retrieve DLO controller")

		# Retrieve  the brightspace controller
		DLOController = DLOController['action']

		if not DLOController:
			raise BaseException("Failed to retrieve DLO controller")

		# Fetch SAML session
		SAMLResponse = soup.find("input", {"name":"SAMLResponse"})
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLResponse = SAMLResponse['value']
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLSession = {
			"SAMLResponse": SAMLResponse,
		}

		# Authenticate with brightspace
		DLOCTLResponse = self.s.post(DLOController, data=SAMLSession, allow_redirects=True)

		if DLOCTLResponse.status_code != 200:
			print("Failed to login at brightspace, reason: %s" % responses[DLOCTLResponse.status_code])

		print("Welcome to the Digital Learning Environment of HVA")
		print("-"*25)

	def Route(self, target=""):

		ControllerResponse = self.s.get(self.base+"/d2l/login?sessionExpired=0&target="+target)

		soup = Soup(ControllerResponse.text, "html.parser")
		
		# Fetch redirect location for route with SAML authentication
		RouteController = soup.find("form", {"name":"hiddenform"})
		if not RouteController:
			raise BaseException("An unknown error occured while authenticating with the controller.")

		RouteController = RouteController['action']
		if not RouteController:
			raise BaseException("An unknown error occured while authenticating with the controller: No engine in response.")

		# Fetch SAML session
		SAMLResponse = soup.find("input", {"name":"SAMLResponse"})
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLResponse = SAMLResponse['value']
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLSession = {"SAMLResponse":SAMLResponse}

		RouteResponse = self.s.post(RouteController, data=SAMLSession, allow_redirects=True)

		# With the viewstate perform the route
		soup = Soup(RouteResponse.text, "html.parser")

		# Get the processform
		DLOController = soup.find("form", {"id":"ProcessForm"})

		if not DLOController:
			raise BaseException("Failed to retrieve DLO controller")

		# Retrieve  the brightspace controller
		DLOController = DLOController['action']

		if not DLOController:
			raise BaseException("Failed to retrieve DLO controller")

		# Fetch SAML session
		SAMLResponse = soup.find("input", {"name":"SAMLResponse"})
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLResponse = SAMLResponse['value']
		if not SAMLResponse:
			raise BaseException("An unknown error occured while authenticating with the controller: No SAML in response.")

		SAMLSession = {"SAMLResponse":SAMLResponse}

		# Get the Relaystate
		RelayState = soup.find("input", {"name":"RelayState"})

		if not RelayState:
			raise BaseException("Failed to retrieve RelayState")

		RelayState = RelayState['value']

		if not RelayState:
			raise BaseException("Failed to retrieve Relaystate")

		SAMLSession = {
			"SAMLResponse": SAMLResponse,
			"RelayState": RelayState
		}

		# Perform stage 1 to set the viewstate
		DLOCTLResponse = self.s.post(DLOController, data=SAMLSession, allow_redirects=True)
		if DLOCTLResponse.status_code != 200:
			raise BaseException("Failed to route through DLO controller (stage 1), reason: "+responses[DLOCTLResponse.status_code])

		# Perform stage 2, the actual route
		DLOCTLResponse = self.s.get(self.base+"/d2l/lp/auth/login/ProcessLoginActions.d2l", allow_redirects=True)
		if DLOCTLResponse.status_code != 200:
			raise BaseException("Failed to route through DLO controller (stage 2), reason: "+responses[DLOCTLResponse.status_code])

		return DLOCTLResponse



	def Request(self, target="", redirect=True):
		response = self.s.get(self.base+target, allow_redirects=True)
		soup = Soup(response.text, "html.parser")

		ROUTREQUIRE_MD5 = "195c898dd1ca9c4a1f3394728e668195" # Hash of HTML prefix used to identify we must use a controller
		PREFIX_MD5 = hashlib.md5(response.text[0:162].encode()).hexdigest() # HTML to hash and compare against

		if PREFIX_MD5 == ROUTREQUIRE_MD5:
			return self.Route(target)

		else:
			return response.text

class BongoClassroom:

	def __init__(self, sso = None, base = "", data = None):
		self.sso = sso
		self.base = base
		self.data = data

	def Join(self):
		pass


class CourseFUN:

	def __init__(self, sso=None):
		self.sso = sso


	def JoinClassroom(self):
		self.home = self.sso.Request("/d2l/home/196867")
		classroom = Soup(self.home, "lxml")
		classroom = classroom.find('d2l-menu-item-link', {"text":"Virtual Classroom"})
		self.classroom = Soup(self.sso.Request(classroom['href']), "html.parser")
		self.classroom = self.classroom.find("iframe", {"class":"d2l-iframe-offscreen"})
		self.classroom = Soup(self.sso.Request(self.classroom['src']), "html.parser")
		self.classroom = self.classroom.find("form", {"id":"LtiRequestForm"})

		bongobase = self.classroom['action']
		bongodata = {
			"launch_presentation_locale":"EN-GB",
			"tool_consumer_instance_guid":self.classroom.find("input", {"name":"tool_consumer_instance_guid"})['value'],
			"tool_consumer_instance_name":"YouSeeU",
			"tool_consumer_info_version":self.classroom.find("input", {"name":"tool_consumer_info_version"})['value'],
			"tool_consumer_info_product_family_code":"desire2learn",
			"context_id":str(self.classroom.find("input", {"name":"context_id"})['value']),
			"context_title":"Fundamentals 1",
			"context_label":str(self.classroom.find("input", {"name":"context_label"})['value']),
			"resource_link_description":"Virtual Classroom Launch",
			"lis_outcome_service_url":str(self.classroom.find("input", {"name":"lis_outcome_service_url"})['value']),
			"lti_version":str(self.classroom.find("input", {"name":"lti_version"})['value']),
			"lti_message_type":str(self.classroom.find("input", {"name":"lti_message_type"})['value']),
			"user_id":str(self.classroom.find("input", {"name":"user_id"})['value']),
			"roles":str(self.classroom.find("input", {"name":"roles"})['value']),
			"lis_person_name_given":str(self.classroom.find("input", {"name":"lis_person_name_given"})['value']),
			"lis_person_name_family":str(self.classroom.find("input", {"name":"lis_person_name_family"})['value']),
			"lis_person_name_full":str(self.classroom.find("input", {"name":"lis_person_name_full"})['value']),
			"lis_person_contact_email_primary":str(self.classroom.find("input", {"name":"lis_person_contact_email_primary"})['value']),
			"ext_d2l_tenantid":str(self.classroom.find("input", {"name":"ext_d2l_tenantid"})['value']),
			"ext_tc_profile_url":str(self.classroom.find("input", {"name":"ext_tc_profile_url"})['value']),
			"ext_d2l_context_id_history":str(self.classroom.find("input", {"name":"ext_d2l_context_id_history"})['value']),
			"ext_d2l_resource_link_id_history":str(self.classroom.find("input", {"name":"ext_d2l_resource_link_id_history"})['value']),
			"lis_result_sourcedid":str(self.classroom.find("input", {"name":"lis_result_sourcedid"})['value']),
			"ext_d2l_link_id":str(self.classroom.find("input", {"name":"ext_d2l_link_id"})['value']),
			"custom_links_outcome_service_url":str(self.classroom.find("input", {"name":"custom_links_outcome_service_url"})['value']),
			"launch_presentation_return_url":str(self.classroom.find("input", {"name":"launch_presentation_return_url"})['value']),
			"oauth_version":str(self.classroom.find("input", {"name":"oauth_version"})['value']),
			"oauth_nonce":str(self.classroom.find("input", {"name":"oauth_nonce"})['value']),
			"oauth_timestamp":str(self.classroom.find("input", {"name":"oauth_timestamp"})['value']),
			"oauth_signature_method":str(self.classroom.find("input", {"name":"oauth_signature_method"})['value']),
			"oauth_consumer_key":str(self.classroom.find("input", {"name":"oauth_consumer_key"})['value']),
			"oauth_callback":str(self.classroom.find("input", {"name":"oauth_callback"})['value']), # Test for XSS lmao
			"oauth_signature":str(self.classroom.find("input", {"name":"oauth_signature"})['value']),
			"ext_basiclti_submit":str(self.classroom.find("input", {"name":"ext_basiclti_submit"})['value'])
		}

		for el in self.classroom.find_all("input"):
			bongodata[el['name']] = el['value']

		print("Joining Virtual Classroom....")
		print(json.dumps(bongodata))

		self.classroom = self.sso.s.post(bongobase, data=bongodata, allow_redirects=True)
		s = self.classroom.text
		start = "redirectUrl = '"
		end="';"
		self.classroom = re.search('%s(.*)%s' % (start, end), s).group(1)
		self.classroom = self.sso.s.get(self.classroom, allow_redirects=True)


		if "You need to enable" in self.classroom.text:
			print("We joined bongo, hooray. However it requires JS and I still need to reverse engineer more of Bongo in order to join the classroom")

		else:
			print("Something went wrong while joining bongo")

class BrightSpace:

	def __init__(self):
		self.sso = HVABrightSpaceSSO()
		self.sso.Login()
		self.fun = CourseFUN(self.sso)

	def GetEvents(self):
		home = Soup(self.sso.Request("/d2l/home").text, "html.parser")
		upcoming = home.find("ul", {"class":"d2l-datalist"})
		events = upcoming.find_all("li", {"class":"d2l-datalist-item"})
		if len(events):
			print("\nUpcoming events:")
		for event in events:
			containers = event.findChildren("div", recursive=True)
			for container in containers:
				blocks=container.findChildren("div", {"class":"d2l-textblock"}, recursive=True)
				if blocks:
					if len(blocks) == 4:
						print("\t", blocks[0].text, blocks[1].text, "-", blocks[3].text, blocks[2].text)

if __name__ == "__main__":
	dlo = BrightSpace()
	dlo.GetEvents()
	dlo.fun.JoinClassroom()
