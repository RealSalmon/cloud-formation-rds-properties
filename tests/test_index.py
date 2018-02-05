import boto3
from moto import mock_rds
from index import lambda_handler
from index import MSG_EMPTY_PROPS, MSG_AMBIGUOUS_PROPS, MSG_MISSING_PROPS


def get_event():
    return {
        "StackId": "12345",
        "RequestId": "ohai!",
        "LogicalResourceId": "best-logical-resource-evar",
        "RequestType": "Create",
        "ResourceProperties": {"DBInstanceIdentifier": "some-db"}
    }


def test_empty_params():
    event = get_event()
    del event['ResourceProperties']
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == MSG_EMPTY_PROPS


def test_ambiguous_params():
    event = get_event()
    event['ResourceProperties']['DBClusterIdentifier'] = 'my-cluster'
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == MSG_AMBIGUOUS_PROPS


def test_missing_params():
    event = get_event()
    event['ResourceProperties'] = {'SomeGarbage': 'DoNotWant'}
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == MSG_MISSING_PROPS


def test_delete():
    event = get_event()
    event['RequestType'] = 'Delete'
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']


@mock_rds
def test_no_such_instance():
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
def test_success_instance():

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
    assert 'Arn' in data
    assert 'Endpoint.Port' in data
    assert 'Endpoint.Address' in data
    assert 'ReadEndpoint.Address' in data
    assert data['ReadEndpoint.Address'] == data['Endpoint.Address']

    # These are not supported by moto
    # assert data['IAMDatabaseAuthenticationEnabled'] is True
    # assert 'ResourceId' in data


# moto has not implemented create_db_cluster so we'll skip these for now

@mock_rds
def skip_test_no_such_cluster():
    event = get_event()
    event["ResourceProperties"] = {"DBClusterIdentifier": "some-cluster"}
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == 'An error occurred (DBClusterNotFound) ' \
                                 'when calling the DescribeDBClusters ' \
                                 'operation: Cluster some-cluster not found.'


@mock_rds
def skip_test_success_cluster():

    cluster_id = 'my-rds-cluster'
    database_name = 'my-database'
    engine = 'mysql'
    engine_version = '1.2.3'
    master_username = 'root'

    # Create the database cluster
    client = boto3.client('rds')
    client.create_db_cluster(
        DatabaseName=database_name,
        DBClusterIdentifier=cluster_id,
        Engine=engine,
        EngineVersion=engine_version,
        MasterUsername=master_username,
        MasterUserPassword='override all security',
        EnableIAMDatabaseAuthentication=True
    )

    event = get_event()
    event['ResourceProperties']['DBClusterIdentifier'] = cluster_id
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['PhysicalResourceId'] == cluster_id
    assert response['RequestId'] == event['RequestId']

    data = response['Data']
    assert data['MasterUsername'] == master_username
    assert data['DatabaseName'] == database_name
    assert data['Engine'] == engine
    assert data['EngineVersion'] == engine_version
    assert 'Arn' in data
    assert 'Endpoint.Port' in data
    assert 'Endpoint.Address' in data
    assert 'ReadEndpoint.Address' in data

    # These are not supported by moto
    # assert data['IAMDatabaseAuthenticationEnabled'] is True
    # assert 'ResourceId' in data
