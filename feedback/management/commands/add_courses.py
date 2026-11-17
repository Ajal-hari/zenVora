from django.core.management.base import BaseCommand
from feedback.models import Course


class Command(BaseCommand):
    help = "Add MCA, MBA and BBA courses"

    def handle(self, *args, **kwargs):

        courses = {

            "MCA": {
                "1": [
                    "Java & Web Programming",
                    "Mathematical Foundations for Computer Science",
                    "Data Structures and Algorithm",
                    "Advanced Database Management System",
                    "Java Practical",
                    "ADBMS Practical",
                    "DSA Practical",
                    "Python Programming",
                ],

                "2": [
                    "Machine Learning",
                    "Machine Learning Practical",
                    "Web Technology",
                    "Advanced Operating Systems",
                    "Data Analytics",
                    "Data Analytics Practical",
                ],

                "3": [
                    "Digital Analytics",
                    "Cloud Computing",
                    "Research Methodology",
                    "Mobile Application Development",
                    "Stock Market Analytics",
                    "Enterprise Computing Project",
                ],

                "4": [
                    "Artificial Intelligence",
                    "Big Data Analytics",
                    "Cyber Security",
                    "Project Work",
                    "Internship",
                ],
            },

            "MBA": {
                "1": [
                    "Principles of Management",
                    "Managerial Economics",
                    "Financial Accounting",
                    "Business Communication",
                    "Marketing Management",
                    "Human Resource Management",
                    "Business Statistics",
                    "Organizational Behaviour",
                ],

                "2": [
                    "Financial Management",
                    "Operations Management",
                    "Human Resource Management",
                    "Marketing Research",
                    "Business Research Methods",
                    "Management Information Systems",
                    "Business Analytics",
                    "Corporate Finance",
                ],

                "3": [
                    "Strategic Management",
                    "Digital Marketing",
                    "Consumer Behaviour",
                    "Investment Management",
                    "Supply Chain Management",
                    "Entrepreneurship Development",
                    "Data Analytics for Business",
                    "Project Management",
                ],

                "4": [
                    "International Business",
                    "Business Intelligence",
                    "Leadership and Management",
                    "Corporate Governance",
                    "Strategic Human Resource Management",
                    "Internship",
                    "Major Project",
                ],
            },

            "BBA": {
                "1": [
                    "Principles of Management",
                    "Business Economics",
                    "Financial Accounting",
                    "Business Communication",
                    "Business Mathematics",
                    "Computer Applications",
                    "Organizational Behaviour",
                ],

                "2": [
                    "Marketing Management",
                    "Human Resource Management",
                    "Cost Accounting",
                    "Business Statistics",
                    "Business Law",
                    "Financial Management",
                    "Entrepreneurship",
                ],

                "3": [
                    "Digital Marketing",
                    "Consumer Behaviour",
                    "Operations Management",
                    "Investment Management",
                    "Business Analytics",
                    "Banking and Finance",
                    "Research Methodology",
                ],

                "4": [
                    "Strategic Management",
                    "International Business",
                    "Business Intelligence",
                    "Project Management",
                    "Corporate Governance",
                    "Internship",
                    "Major Project",
                ],
            },
        }

        created_count = 0

        for department, semesters in courses.items():

            for semester, course_list in semesters.items():

                for course_name in course_list:

                    course, created = Course.objects.get_or_create(
                        name=course_name,
                        semester=semester,
                        department=department
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                "Added: {} - {} - Semester {}".format(
                                    department,
                                    course_name,
                                    semester
                                )
                            )
                        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Courses added successfully!"
            )
        )

        self.stdout.write(
            "New courses added: {}".format(created_count)
        )