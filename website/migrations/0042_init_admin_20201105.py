from django.contrib.auth.models import User
from django.db import migrations
from django.utils import timezone

from website.models import Physician


def forwards_func(apps, schema_editor):
    # build the user you now have access to via Django magic
    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        # add admin
        user = User.objects.create_superuser('admin', email='contact@jz.com', password='123456',
                                             last_login=timezone.now())
        Physician.objects.create(admin=True, user=user)

def reverse_func(apps, schema_editor):
    # destroy what forward_func builds
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0041_spsample_sample_folder'),
        ('authtoken', '0002_auto_20160226_1747')
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]