from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_alter_user_language_alter_user_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="last_habits_report_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
