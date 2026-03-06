from django.conf import settings
import boto3
import json


def convert_value(value):
    try:
        return json.loads(value)
    except Exception as e:
        return value


def get_aws_env(value, default=None):
    name = None
    try:
        ssm = boto3.client('ssm')
        name = f'/backend/{settings.ENVIRONMENT}/{value}'
        content = ssm.get_parameter(Name=name, WithDecryption=True)
        return convert_value(content['Parameter']['Value'])
    except Exception as e:
        if not default:
            raise ValueError(f'Error loading {name} from store: {e}')
        return default
