#Esse código em Python é uma função AWS Lambda que criptografa os snaphosts sem criptografia e em seguida apaga, evitando que existam snapshosts sem criptografia

import boto3
import logging

def process_snapshots(snapshots, ec2_client):
    encrypted_snapshots = []

    for snapshot in snapshots:
        # Verificar se o snapshot não está criptografado
        if not snapshot.get('Encrypted', False):
            # Criar um snapshot criptografado a partir do snapshot sem criptografia
            response = ec2_client.copy_snapshot(
                SourceSnapshotId=snapshot['SnapshotId'],
                SourceRegion='us-east-1',  # Substitua 'us-east-1' pela região do snapshot original
                Encrypted=True
            )

            # Obter o ID do novo snapshot criptografado
            encrypted_snapshot_id = response['SnapshotId']

            # Esperar até que o novo snapshot esteja disponível antes de prosseguir
            waiter = ec2_client.get_waiter('snapshot_completed')
            waiter.wait(SnapshotIds=[encrypted_snapshot_id])

            # Excluir o snapshot original sem criptografia
            ec2_client.delete_snapshot(SnapshotId=snapshot['SnapshotId'])

            logging.info(f'Snapshot original sem criptografia {snapshot["SnapshotId"]} criptografado com sucesso: {encrypted_snapshot_id}')
            print(f'Snapshot original sem criptografia {snapshot["SnapshotId"]} criptografado com sucesso: {encrypted_snapshot_id}')
            encrypted_snapshots.append({
                'original_snapshot_id': snapshot['SnapshotId'],
                'encrypted_snapshot_id': encrypted_snapshot_id
            })

    return encrypted_snapshots

def lambda_handler(event, context):
    # Configuração do cliente do AWS EC2
    ec2_client = boto3.client('ec2')

    try:
        # Obter todos os snapshots existentes
        response = ec2_client.describe_snapshots(OwnerIds=['self'])
        snapshots = response['Snapshots']

        # Dividir os snapshots em lotes de tamanho máximo de 10 snapshots por lote
        batch_size = 10
        for i in range(0, len(snapshots), batch_size):
            batch_snapshots = snapshots[i:i+batch_size]

            # Processar os snapshots do lote atual
            encrypted_snapshots = process_snapshots(batch_snapshots, ec2_client)

        if encrypted_snapshots:
            print('Processo concluído com sucesso!')
            
            return {
                'statusCode': 200,
                'message': 'Processo concluído com sucesso.',
                'encrypted_snapshots': encrypted_snapshots
            }
        else:
            return {
                'statusCode': 200,
                'message': 'Nenhum snapshot sem criptografia encontrado.'
            }

    except Exception as e:
        logging.error(f'Ocorreu um erro: {e}')
        return {
            'statusCode': 500,
            'error': str(e)
        }
