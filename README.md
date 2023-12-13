![cloud-formation-rds-properties](https://github.com/realsalmon/cloud-formation-rds-properties/actions/workflows/main.yml/badge.svg)

# cloud-formation-rds-properties

## A Lambda backed custom resource for CloudFormation that provides information about an RDS instance or cluster

### Purpose:
This custom resource provides information about an AWS RDS instance or cluster.

It might be useful in situations where your RDS resource is outside of a
CloudFormation stack where it would be helpful to have that information without
the need to enter several parameters. It might also be helpful in situations
where you need additional information about an RDS resource that the return
values for AWS::RDS::DBInstance and AWS::RDS::DBCluster do not include.

### Installation
This custom resource can be installed on your AWS account by deploying the 
CloudFormation template at cloud-formation/cloud-formation.yml, and then 
updating the Lambda function it creates with the code from python/index.py

The Lambda function's ARN, which is needed for use as a service token when
using this custom resource in your CloudFormation  templates, will be exported
as an output with the name ```${AWS::StackName}-FunctionArn```. This service
token will also be stored in
[Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-paramstore.html)
at
```/cloud-formation/service-tokens/rds-properties```

Once installed, you can test the custom resource by using the CloudFormation
template at cloud-formation/example-cloud-formation.yml, which will create a 
stack with outputs from the custom resource.

### Syntax:
The syntax for declaring this resource:

```yaml
RdsProperties:
  Type: "AWS::CloudFormation::CustomResource"
  Version: "1.0"
  Properties:
    ServiceToken: LAMDA_FUNCTION_ARN
    DBInstanceIdentifier: DB_INSTANCE_IDENTIFIER
    DBClusterIdentifier: DB_CLUSTER_IDENTIFIER,
```
### Properties

#### Service Token
##### The ARN of the Lambda function backing the custom resource
Type: String

Required: Yes

#### DBInstanceIdentifier
##### The DBInstanceIdentifier of an RDS instance to query
Type: String

Required: Conditional. Exactly one of either DBInstanceIdentifier or 
DBClusterIdentifier are required

#### DBClusterIdentifier
##### The DBClusterIdentifier of an RDS cluster to query
Type: String

Required: Conditional. Exactly one of either DBInstanceIdentifier or 
DBClusterIdentifier are required


### Return Values

#### Ref
When the logical ID of this resource is provided to the Ref intrinsic function, 
Ref returns the DBInstanceIdentifier property

#### Fn::GetAtt
Fn::GetAtt returns a value for a specified attribute of this type. The 
following are the available attributes.

##### Arn
The ARN of the RDS resource.

##### ResourceId
The AWS Region-unique, immutable identifier for the RDS resource. For 
instances, this will be the DbiResourceId. For clusters, this will be the 
DbClusterResourceId.

##### DBName
The name of the database that was created with the RDS resource

##### Endpoint.Address
The endpoint address of the RDS resource

##### Endpoint.Port
The endpoint port of the RDS resource

#### ReadEndpoint.Address
The reader endpoint for the RDS resource. For instances, this will always be
the same as Endpoint.Address

##### Engine
The engine of the RDS resource

##### EngineVersion
The engine version of the RDS resource

##### IAMDatabaseAuthenticationEnabled
True if mapping of AWS Identity and Access Management (IAM) accounts to 
database accounts is enabled, and otherwise false.

##### MasterUsername
The master username for the RDS instance
