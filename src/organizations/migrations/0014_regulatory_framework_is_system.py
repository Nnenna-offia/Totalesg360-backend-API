from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0013_organizationesgsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='regulatoryframework',
            name='is_system',
            field=models.BooleanField(default=True, help_text='Whether this framework is system-managed and not user-created'),
        ),
    ]