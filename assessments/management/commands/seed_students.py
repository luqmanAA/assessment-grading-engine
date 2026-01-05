from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

class Command(BaseCommand):
    help = 'Seeds the database with student users and returns their login credentials.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of students to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f"Seeding {count} students...")

        students_data = []
        default_password = "password123"
        
        with transaction.atomic():
            for i in range(1, count + 1):
                username = f"student_{i}"
                email = f"student_{i}@example.com"
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email': email}
                )
                
                if created:
                    user.set_password(default_password)
                    user.save()
                    status = "Created"
                else:
                    status = "Existing"
                
                students_data.append({
                    'username': username,
                    'email': email,
                    'password': default_password,
                    'status': status
                })

        # Display results in a formatted table-like structure
        separator = "=" * 75
        self.stdout.write("\n" + separator)
        self.stdout.write(
            f"{ 'Username':<15} | { 'Email':<25} | { 'Password':<15} | { 'Status':<10}"
        )
        self.stdout.write("-" * 75)
        
        for data in students_data:
            self.stdout.write(
                f"{data['username']:<15} | {data['email']:<25} | {data['password']:<15} | {data['status']:<10}"
            )
        
        self.stdout.write(separator)
        self.stdout.write(self.style.SUCCESS(f"\nSeeding complete for {count} students."))
