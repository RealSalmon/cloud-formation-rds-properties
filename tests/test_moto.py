import boto3
from moto import mock_rds


@mock_rds
def test_describe_db_instances():
    # Create the database instance
    client = boto3.client('rds')
    client.create_db_instance(
        DBName='best-database-evar',
        DBInstanceIdentifier='best-instance-evar',
        AllocatedStorage=10,
        DBInstanceClass='t2.small',
        Engine='mysql',
        EngineVersion='42',
        MasterUsername='root',
        MasterUserPassword='override all security',
        EnableIAMDatabaseAuthentication=True
    )

    response = client.describe_db_instances(DBInstanceIdentifier='best-instance-evar')
    instance = response['DBInstances'][0]

    assert instance['DBInstanceIdentifier'] == 'best-instance-evar'

    # these keys are missing in the response from moto
    # we actually want them to be there, but this test is looking for the
    # opposite because I want to keep a reminder of it without breaking
    # tests
    #
    # https://github.com/spulec/moto/issues/1465
    assert 'IAMDatabaseAuthenticationEnabled' not in instance
    assert 'DbiResourceId' not in instance
