import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Portfolio", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("name", models.CharField(max_length=100)),
            ("slug", models.SlugField(max_length=110, unique=True)),
            ("description", models.CharField(blank=True, max_length=500)),
            ("portfolio_type", models.CharField(choices=[("personal","Personnel"),("professional","Professionnel"),("business","Entreprise")],default="personal",max_length=20)),
            ("status", models.CharField(default="draft", editable=False,max_length=16)),
            ("visibility", models.CharField(default="private", editable=False,max_length=16)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="portfolios", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering":["-updated_at","-created_at"]}),
        migrations.AddConstraint(model_name="portfolio", constraint=models.CheckConstraint(condition=models.Q(status="draft"),name="port001_draft_only")),
        migrations.AddConstraint(model_name="portfolio", constraint=models.CheckConstraint(condition=models.Q(visibility="private"),name="port001_private_only")),
    ]
