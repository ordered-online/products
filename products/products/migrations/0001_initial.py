# Generated by Django 2.2.6 on 2019-10-26 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Additive',
            fields=[
                ('name', models.TextField(max_length=100, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('name', models.TextField(max_length=100, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('name', models.TextField(max_length=100, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_id', models.IntegerField()),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('additives', models.ManyToManyField(to='products.Additive')),
                ('categories', models.ManyToManyField(to='products.Category')),
                ('tags', models.ManyToManyField(to='products.Tag')),
            ],
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['location_id'], name='products_pr_locatio_6d2e4c_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='product',
            unique_together={('location_id', 'name')},
        ),
    ]
