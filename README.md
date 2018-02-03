# cloud-formation-rds-properties

## A Lambda backed custom resource for CloudFormation that provides information about an RDS instance


### Purpose:
This custom resource provides information about an AWS RDS instance.

It might be useful in situations where your RDS instance is outside of a
CloudFormation stack where it would be helpful to have that information without
the need to enter several parameters. It might also be helpful in situations
where you need additional information about an RDS instance that the return
values for a AWS::RDS::DBInstance type do not include.

### Installation
This custom resource can be installed on your AWS account by deploying the 
CloudFormation template at cloud-formation/cloud-formation.yml, and then 
updating the Lambda function it creates with the code from python/index.py

The CloudFormation stack will export a value as ${AWS::StackName}-FunctionArn
that can be used for retrieving the Lambda function's ARN in other templates.

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
    ServiceToken: LAMDA_FUNCTION_ARN,
    DBInstanceIdentifier: DB_INSTANCE_IDENTIFIER,
```
### Properties

#### Service Token
##### The ARN of the Lambda function backing the custom resource
Type: String

Required: Yes

#### DBInstanceIdentifier
##### The DBInstanceIdentifier of the RDS instance to query
Type: String

Required: Yes


### Return Values

#### Ref
When the logical ID of this resource is provided to the Ref intrinsic function, 
Ref returns the DBInstanceIdentifier property

#### Fn::GetAtt
Fn::GetAtt returns a value for a specified attribute of this type. The 
following are the available attributes.

##### DBInstanceArn
The ARN of the RDS instance

##### DbiResourceId
The AWS Region-unique, immutable identifier for the DB instance.

##### DBName
The name of the database that was created with the RDS instance

##### Endpoint.Address
The endpoint address of the RDS instance

##### Endpoint.Port
The endpoint port of the RDS instance

##### Engine
The engine of the RDS instance

##### EngineVersion
The engine version of the RDS instance

##### IAMDatabaseAuthenticationEnabled
True if mapping of AWS Identity and Access Management (IAM) accounts to 
database accounts is enabled, and otherwise false.

##### MasterUsername
The master username for the RDS instance
