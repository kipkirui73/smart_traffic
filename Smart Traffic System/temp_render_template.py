from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory='templates')
ctx = {
    'request': None,
    'violations': [(1, 2, '2026-05-02T12:00:00', 'evidence/vehicle_2_123.jpg')],
    'title': 'Test'
}
print(templates.env.get_template('dashboard.html').render(ctx))
