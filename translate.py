import sublime, sublime_plugin, re
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib import error
from json import loads

api = 'https://translate.googleapis.com/translate_a/single?'
headers = {
	'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'
}
settings = False
class TranslateCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		settings = sublime.load_settings("translate.sublime-settings")
		# READ USER SETTINGS
		es_en_only = settings.get('es_en_only') or False
		source_lang = settings.get('source_lang') or 'auto'
		target_lang = settings.get('target_lang') or 'es'

		v = self.view
		regions = v.sel() # Seleccion

		for region in regions:

			# si no hay selección -> traduce la palabra más cercana
			pt = region.empty() and region or v.word(region)
			phrase = v.substr(pt)
			# si la palabra es más corta que 1 -> no traduce
			if len(phrase.strip()) > 1:
				invert = re.search('[а-я]', phrase, flags=re.IGNORECASE)
				params = {
					'client': 'gtx',
					'dt'	: 'bd',
					'dj'	: 1,
					'sl'	: es_en_only and ('es' if invert else 'en') or source_lang,
					'tl'	: es_en_only and ('en' if invert else 'es') or target_lang,
					'q'		: phrase
				}
				sublime.status_message( 'translate: ' + params['sl'] + ' => ' + params['tl'])
				# PREPARA LA SOLICITUD
				req = Request(api + urlencode(params) + '&dt=t', headers = headers)

				# INTENTE HACER LA SOLICITUD; TIEMPO DE ESPERA EN SEGUNDOS
				try:
					json = urlopen(req, timeout = 4).read()

				# RECOGER ERRORES SI LOS HAY
				except error.HTTPError as err:
					if err.code == 404:
						return sublime.status_message('404')
					else:
						return sublime.status_message(str(err))

				res = loads(json.decode('utf-8'), '')

				items = [''.join(map(lambda x: x['trans'], res['sentences'])), '-'];

				if 'dict' in res:
					for list in res['dict']:
						items.extend(list['terms'])
						items.append('-')

				def on_select(i):
					if i > -1:
						# Remplazar toda la seleccion
						regions.add(region.cover(pt));
						v.replace(edit, pt, items[i])


				if len(regions) < 2 and len(items) > 4: 
					v.show_popup_menu(items, on_select)
				else:
					on_select(0)

