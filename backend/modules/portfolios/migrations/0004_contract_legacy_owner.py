from django.db import migrations

class Migration(migrations.Migration):
    dependencies=[('portfolios','0003_backfill_and_constrain')]
    operations=[migrations.RemoveField(model_name='portfolio',name='owner')]
