from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('portfolios','0001_initial'),('accounts','0002_provision_personal_accounts')]
    operations=[
        migrations.AddField(model_name='portfolio',name='account',field=models.ForeignKey(to='accounts.account',null=True,on_delete=django.db.models.deletion.PROTECT,related_name='portfolios')),
        migrations.AddField(model_name='portfolio',name='management_state',field=models.CharField(max_length=12,default='active')),
        migrations.AddField(model_name='portfolio',name='version',field=models.PositiveBigIntegerField(default=1)),
        migrations.AddField(model_name='portfolio',name='source_template_id',field=models.CharField(max_length=100,null=True,blank=True)),
        migrations.AddField(model_name='portfolio',name='source_template_version',field=models.CharField(max_length=30,null=True,blank=True)),
        migrations.AddField(model_name='portfolio',name='initial_theme_id',field=models.CharField(max_length=100,default='studio-neutral')),
        migrations.AddField(model_name='portfolio',name='initial_theme_version',field=models.CharField(max_length=30,default='1.0.0')),
    ]
