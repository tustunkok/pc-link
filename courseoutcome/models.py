from django.db import models

class Semester(models.Model):
    year_interval = models.CharField(max_length=9)
    period_name = models.CharField(max_length=6)

    def __str__(self):
        return self.year_interval + " " + self.period_name

class Department(models.Model):
    code = models.CharField(max_length=6)
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.code + " - " + self.name

class CourseOutcome(models.Model):
    code = models.CharField(max_length=5)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.code + " - " + self.department.code

class Course(models.Model):
    code = models.CharField(max_length=9)
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.code

class Student(models.Model):
    no = models.CharField(max_length=11)
    name = models.CharField(max_length=60)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    vertical_transfer = models.BooleanField(default=False)
    double_major_student = models.BooleanField(default=False)
    graduated_on = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

class CourseOutcomeResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    course_outcome = models.ForeignKey(CourseOutcome, on_delete=models.CASCADE)
    satisfaction = models.IntegerField()
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return self.student.name + " - " + self.course.code + " - [" + \
            self.course_outcome.code + "-" + self.course_outcome.department.code + \
            "] - " + str(self.semester) + " - " + str(self.satisfaction)