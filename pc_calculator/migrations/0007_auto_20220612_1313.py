# Generated by Django 3.2 on 2022-06-12 10:13

from django.db import migrations


def create_default_curriculum(apps, schema_editor):
    Curriculum = apps.get_model('pc_calculator', 'Curriculum')
    Student = apps.get_model('pc_calculator', 'Student')
    Course = apps.get_model('pc_calculator', 'Course')

    default_curriculum = Curriculum.objects.create(name='Default Curriculum')
    Student.objects.update(assigned_curriculum=default_curriculum)
    default_curriculum.member_courses.add(*Course.objects.all())



def reverse_create_default_curriculum(apps, schema_editor):
    Curriculum = apps.get_model('pc_calculator', 'Curriculum')

    default_curriculum = Curriculum.objects.get(name='Default Curriculum')
    default_curriculum.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pc_calculator', '0006_auto_20220612_1313'),
    ]

    operations = [
        migrations.RunPython(create_default_curriculum, reverse_create_default_curriculum),
    ]