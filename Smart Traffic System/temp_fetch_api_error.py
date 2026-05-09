import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/'
try:
    resp = urllib.request.urlopen(url)
    print('STATUS', resp.status)
    print(resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTPERROR', e.code)
    print(e.read().decode('utf-8'))
except Exception as e:
    print('ERROR', type(e).__name__, e)
