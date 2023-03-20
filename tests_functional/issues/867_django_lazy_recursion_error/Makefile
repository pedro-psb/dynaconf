.PHONY: test

test:
	python manage.py test foo -v 2
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=foo.settings django-admin test foo -v 2
	cd ../../;python issues/867_django_lazy_recursion_error/manage.py test foo -v 2
	cd ../../;PYTHONPATH=issues/867_django_lazy_recursion_error/ DJANGO_SETTINGS_MODULE=foo.settings django-admin test foo -v 2
	PYTHONPATH=. DJANGO_SETTINGS_MODULE=foo.settings python standalone_script.py