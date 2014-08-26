#Author: Victor Suarez Rovere
#Licensing: see file LICENSE.txt

import sys
import passkey_ui
from mechanize._form import ParseString, PasswordControl, TextControl
import traceback
import pprint
import ast
import publicsuffix
import urllib

class PwdDB:
	maindict = dict()
	
	def __init__(self, fname):
		self.fname = fname
		
	def save_maindict(self):
		with open(self.fname, 'w+') as stream:
			pprint.pprint(self.maindict, width=1, stream=stream)
		self.dump()
			
	def load_maindict(self):
		try:
			with open(self.fname, 'r') as stream:
				s = stream.read()
				self.maindict = ast.literal_eval(s)
		except:
			maindict = dict()
		#self.dump()
		
	def dump(self):
		print >>sys.stderr, "DB=", self.maindict
	

learning = True
learnedfields = {}

db = None
ui = None
psl = None

def start(ctx, argv):
	ctx.log("start")
	global ui, db, learning, psl

	db = PwdDB("passkeypwd.txt")
	db.load_maindict()
	
	learning = (db.maindict == dict())
	ui = passkey_ui.PasskeyUI()
	ui.notify_learningmode(learning)
	psl = publicsuffix.PublicSuffixList()
	
def find_formfields(formlist, typ):
	return dict(filter(lambda x: x[1], [(form.action, [u.name for u in filter(lambda x: x.type in typ, form.controls)]) for form in formlist]))

host2server = dict()

def request(context, flow):
	global learning, db
	ui.do_idle()
	ui.update()
	
	try:
		url = flow.request.get_url()
		host = flow.request.host
		#path = flow.request.path
		#print >>sys.stderr, "REQUEST url, host, path", url, host, path
		serverdomain = psl.get_public_suffix(host)
		company = host2server.get(host)
		
		if "application/x-www-form-urlencoded" in flow.request.headers["content-type"]:
			frm = flow.request.get_form_urlencoded()
			learnedentry = None
			
			if learning:
				fields = learnedfields.get(url)
				if fields:
					urlcut = url; urltailpos = url.find('?');
					if urltailpos > 0: urlcut = url[:urltailpos+1]
					doupdate = True
					if db.maindict.get(urlcut) is not None:
						doupdate = ui.ask_msg("Overwrite entry?", serverdomain)
					if doupdate:
						db.maindict.update({urlcut:dict()})
						for field in fields:
							value = frm.get(field)
							if value and value[0]: #si existe y tiene algun valor
								learnedentry = {field:value[0]}
								db.maindict[urlcut].update(learnedentry)

						if learnedentry is not None:
							learning = False #ya aprendio
							ui.notify_learningmode(learning)
							db.save_maindict()
							ui.display_msg("Data Learned for:", serverdomain, "*"*len(value[0]))
							ui.beep()
						else:
							ui.notify_learningmode(learning)
					else:
						learning = False #no era la idea learning
						ui.notify_learningmode(learning)
			else: #if not learning
				for urlprefix, entry in db.maindict.iteritems():
					if url.startswith(urlprefix):
						ask = True
						for var in entry.keys(): #todas las variables tiene que estar
							if frm.get(var) is None:
								ask = False
						if ask:
							if ui.ask_msg("LOGIN:", serverdomain, company):
								for var, value in entry.iteritems():
									frm[var] = [value]
								flow.request.confirmed = True #agrega atributo
							else: frm[var] = "" #del frm[var]
							flow.request.set_form_urlencoded(frm)

							ui.display_msg("Password sent to:", serverdomain)
							ui.beep()

	except Exception, e:
		#traceback.print_exception(file=sys.stderr)
		print >>sys.stderr, "Exception", e
	ui.update()


def response(context, flow):
	global learnedfields, learning, db
	ui.do_idle()
	ui.update()
	
	try:
		host = flow.response.request.host
		serverdomain = psl.get_public_suffix(host)
		company = host2server.get(host)
		if not company:
			if flow.response.cert is not None and hasattr(flow.response.cert, "subject"):
				certsubject = dict(flow.response.cert.subject)
				company = certsubject.get("O")
				if company: host2server[host] = company

		url = flow.response.request.get_url()




		if ui.key_was_pressed(ord('l')):
			learning = not learning;
			ui.notify_learningmode(learning)
		
		if learning:
			flow.response._assemble()
			contenttype = flow.response.headers.get("content-type")
			if contenttype and contenttype[0].startswith('text/html'):
				body = flow.response.get_decoded_content()
				formlist = [form for form in ParseString(body, url)]
				passwordfields = find_formfields(formlist, ['password'])
				if passwordfields: #algun password tiene que tener
					pwdandtextfields = find_formfields(formlist, ['text','password'])
					learnedfields.update(pwdandtextfields) #agrega usuario, etc.
					print >>sys.stderr, "Detected form fields=", pwdandtextfields
					ui.display_msg("Analyzing", serverdomain)
		else: #if not learning
			learnedfields = {}
			if hasattr(flow.response.request, "confirmed"):
				request_cookies = flow.request.get_cookies()
				response_cookies = flow.response.get_cookies()
				print >>sys.stderr, "COOKIES REQUEST=", [(key, value[0]) for key, value in request_cookies.iteritems()]
				print >>sys.stderr, "COOKIES RESPONSE=", [(key, value[0]) for key, value in response_cookies.iteritems()]
				newcookies = calc_new_cookies_names(request_cookies, response_cookies)
				newcookies = "PASSKEY:NEW-COOKIES=" + ";".join(newcookies)
				print >>sys.stderr, "COOKIES NEW=", newcookies
				flow.response.headers["pragma"] = [newcookies]
				print >>sys.stderr, "RESPONSE=", flow.response.headers, flow.response.get_decoded_content()

			
	except Exception, e:
		#traceback.print_exception(file=sys.stderr)
		print >>sys.stderr, "Exception", e
	ui.update()

def calc_new_cookies_names(oldcookies, newcookies):
	changed = []
	for newk, newvalue in newcookies.iteritems():
		oldvalue = oldcookies.get(newk.strip())
		if oldvalue is None or newvalue[0] != oldvalue[0]:
			changed.append(newk)
	return changed
