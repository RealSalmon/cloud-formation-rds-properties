import boto3
from moto import mock_rds
from index import lambda_handler


def get_event():
    return {
        "StackId": "12345",
        "RequestId": "ohai!",
        "LogicalResourceId": "best-logical-resource-evar",
        "RequestType": "Create",
        "ResourceProperties": {"DBInstanceIdentifier": "some-db"}
    }


def test_missing_params():
    event = get_event()
    event['ResourceProperties'] = {"SomeGarbage": "DoNotWant"}
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == 'Required resource property ' \
                                 'DBInstanceIdentifier is not set'


def test_delete():
    event = get_event()
    event['RequestType'] = 'Delete'
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']


@mock_rds
def test_no_such_db():
    event = get_event()
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == 'An error occurred (DBInstanceNotFound) ' \
                                 'when calling the DescribeDBInstances ' \
                                 'operation: Database some-db not found.'


@mock_rds
def test_success():

    instance_id = 'my-rds-instance'
    database_name = 'my-database'
    engine = 'mysql'
    engine_version = '1.2.3'
    master_username = 'root'

    # Create the database instance
    client = boto3.client('rds')
    client.create_db_instance(
        DBName=database_name,
        DBInstanceIdentifier=instance_id,
        AllocatedStorage=10,
        DBInstanceClass='t2.small',
        Engine=engine,
        EngineVersion=engine_version,
        MasterUsername=master_username,
        MasterUserPassword='override all security',
        EnableIAMDatabaseAuthentication=True
    )

    event = get_event()
    event['ResourceProperties']['DBInstanceIdentifier'] = instance_id
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['PhysicalResourceId'] == instance_id
    assert response['RequestId'] == event['RequestId']

    data = response['Data']
    assert data['MasterUsername'] == master_username
    assert data['DBName'] == database_name
    assert data['Engine'] == engine
    assert data['EngineVersion'] == engine_version
    # assert data['IAMDatabaseAuthenticationEnabled'] is True
    assert 'DBInstanceArn' in data
    assert 'Endpoint.Port' in data
    assert 'Endpoint.Address' in data
    # assert 'DbiResourceId' in data
