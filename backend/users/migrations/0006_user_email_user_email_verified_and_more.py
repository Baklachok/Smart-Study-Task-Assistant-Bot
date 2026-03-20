from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def set_unusable_password_for_legacy_telegram_users(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(password="").update(password=make_password(None))


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_user_last_habits_report_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="user",
            name="telegram_id",
            field=models.BigIntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
        migrations.RunPython(
            set_unusable_password_for_legacy_telegram_users,
            migrations.RunPython.noop,
        ),
    ]
