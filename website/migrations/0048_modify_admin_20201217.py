from django.contrib.auth.models import User
from django.db import migrations
from django.utils import timezone

from website.models import Physician


def forwards_func(apps, schema_editor):
    # build the user you now have access to via Django magic
    try:
        user = User.objects.get(username='admin')
        phy = Physician.objects.get(user=user)
        phy.admin = True
        phy.edit = True
        phy.operator = True
        phy.submit = True
        phy.review = True
        phy.save()
    except User.DoesNotExist:
        # add admin
        user = User.objects.create_superuser('admin', email='contact@jz.com', password='123456',
                                             last_login=timezone.now())
        Physician.objects.create(admin=True, edit=True, operator=True, submit=True, review=True, user=user)
    except Physician.DoesNotExist:
        user = User.objects.get(username='admin')
        Physician.objects.create(admin=True, edit=True, operator=True, submit=True, review=True, user=user)

def reverse_func(apps, schema_editor):
    # destroy what forward_func builds
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('website', '0047_auto_20201124_1510'),
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]