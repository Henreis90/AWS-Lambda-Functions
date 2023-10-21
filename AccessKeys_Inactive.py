#Função AWS Lambda em Python para inativar AccessKeys que não estão sendo utilizadas a um determinado período

import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    iam = boto3.client('iam')
    
    users = iam.list_users()['Users']
    current_date = datetime.now()
    inactive_days_threshold = 10  # Defina o número de dias para desativar automaticamente as chaves não utilizadas
    
    for user in users:
        access_keys = iam.list_access_keys(UserName=user['UserName'])['AccessKeyMetadata']
        
        for access_key in access_keys:
            last_used = iam.get_access_key_last_used(AccessKeyId=access_key['AccessKeyId'])
            last_used_date = last_used['AccessKeyLastUsed'].get('LastUsedDate')
            create_date = access_key['CreateDate']
            
            if last_used_date is None:
                inactive_days = (current_date - create_date.replace(tzinfo=None)).days
            else:
                inactive_days = (current_date - last_used_date.replace(tzinfo=None)).days
            
            if inactive_days > inactive_days_threshold:
                iam.update_access_key(AccessKeyId=access_key['AccessKeyId'], UserName=user['UserName'], Status='Inactive')
                print(f"AccessKey Inactive: {access_key['AccessKeyId']} User:{user['UserName']}")
    
    return {
        'statusCode': 200,
        'body': 'Inactive Access Keys were successfully disabled.'
    }
