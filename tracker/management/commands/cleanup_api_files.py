from django.core.management.base import BaseCommand
from main_app import MAIN


class Command(BaseCommand):
    help = 'Cleans up temporary generated API-*.xlsx files older than specified minutes (default 10) to conserve server disk space.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=10,
            help='Age threshold in minutes after which temporary files will be deleted (default: 10).'
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        seconds = minutes * 60
        self.stdout.write(f"Scanning for generated API-*.xlsx files older than {minutes} minutes ({seconds}s)...")
        deleted_count = MAIN.cleanup_old_api_files(max_age_seconds=seconds)
        self.stdout.write(self.style.SUCCESS(f"Cleanup finished. Successfully deleted {deleted_count} expired API file(s)."))
