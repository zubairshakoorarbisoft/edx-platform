import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from openedx.core.djangoapps.external_user_ids.models import ExternalId

class Command(BaseCommand):
    help = "Export user emails and usernames for given external_user_ids from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            'input_csv', type=str, help='Path to the input CSV file containing external_user_id'
        )
        parser.add_argument(
            'output_csv', type=str, help='Path to the output CSV file where emails and usernames will be written'
        )
        parser.add_argument(
            'external_id_field_name', type=str, help='Path to the output CSV file where emails and usernames will be written'
        )

    def handle(self, *args, **kwargs):
        input_csv = kwargs['input_csv']
        output_csv = kwargs['output_csv']
        external_id_field_name = kwargs['external_id_field_name']

        with open(input_csv, mode='r') as infile, open(output_csv, mode='w', newline='') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = ['external_user_id', 'username', 'email']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            writer.writeheader()

            for row in reader:
                external_user_id = row[external_id_field_name]

                try:
                    external_id = ExternalId.objects.get(external_user_id=external_user_id)
                    user = external_id.user

                    writer.writerow({
                        'external_user_id': external_user_id,
                        'username': user.username,
                        'email': user.email
                    })

                except ExternalId.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"ExternalId with ID {external_user_id} does not exist."))
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"User for ExternalId {external_user_id} does not exist."))

        self.stdout.write(self.style.SUCCESS(f"Export complete. Data saved to {output_csv}"))
