## Stack Notes

- Django entrypoint is usually `manage.py`.
- Prefer app-local tests and migrations scoped to the changed app.
- Run migrations through the project command documented in this repository, not ad hoc SQL.
- Use `/claude-tech-squad:squad` for model, serializer, API, and UI changes that span layers.

## Default Commands

```bash
python manage.py runserver
python manage.py test
python manage.py check
python manage.py migrate
```
