# Generated by Django 4.2.6 on 2023-12-31 03:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sheet_api", "0002_composer_first_scanned_composer_last_scanned_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="composer",
            constraint=models.UniqueConstraint(
                fields=("full_name", "first_name", "last_name"),
                name="unique_full_name_first_name_last_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="work",
            constraint=models.UniqueConstraint(
                fields=("work_title", "opus", "opus_number"),
                name="unique_work_title_opus_opus_number",
            ),
        ),
    ]
