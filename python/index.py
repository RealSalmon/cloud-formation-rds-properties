#! /usr/bin/env python
#
# The following IAM permissions are required . . .
#
#   rds:DescribeDbInstances
#
# Test event...
"""
{
    "StackId": "12345",
    "RequestId": "ohai!",
    "LogicalResourceId": "best-logical-resource-evar",
    "RequestType": "Create",
    "ResourceProperties": {"DBInstanceIdentifier": "thing1"}
}
"""

import http.client
import json
import logging
import os
import sys
from urllib.parse import urlparse

import boto3

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())

MSG_EMPTY_PROPS = 'Empty resource properties'
MSG_AMBIGUOUS_PROPS = 'DBInstanceIdentifier and DBClusterIdentifier can not ' \
                      'both be specified in the resource properties'
MSG_MISSING_PROPS = 'Required resource property DBInstanceIdentifier or ' \
                    'DBClusterIdentifier is not set'


def get_data_value(data_key, resource, data_map):
    resource_key = data_map[data_key]
    if '.' in resource_key:
        x, y = resource_key.split('.')
        return resource[x][y]
    else:
        return resource.get(resource_key)


def send_response(request, response, status=None, reason=None):
    """ Send our response to the pre-signed URL supplied by CloudFormation
    If no ResponseURL is found in the request, there is no place to send a
    response. This may be the case if the supplied event was for testing.
    """
    log = logging.getLogger(__name__)
    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    log.debug("Response body is: %s", response)

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urlparse(request['ResponseURL'])
        body = json.dumps(response)
        https = http.client.HTTPSConnection(url.hostname)
        log.debug("Sending response to %s", request['ResponseURL'])
        https.request('PUT', url.path + '?' + url.query, body)
    else:
        log.debug("No response sent (ResponseURL was empty)")

    return response


def send_fail(request, response, reason=None):
    if reason is not None:
        logger.error(reason)
    else:
        reason = 'Unknown Error - See CloudWatch log stream of the Lambda ' \
                 'function backing this custom resource for details'

    return send_response(request, response, 'FAILED', reason)


def lambda_handler(event, context=None):

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Status': 'SUCCESS'
    }

    # Make sure resource properties are there
    props = None
    try:
        props = event['ResourceProperties']
    except KeyError:
        return send_fail(event, response, MSG_EMPTY_PROPS)

    # Make sure that we have one of DBInstanceIdentifier or DBClusterIdentifier
    # but not both
    inputs = ('DBInstanceIdentifier', 'DBClusterIdentifier')
    arg_chk = [k in props for k in inputs]
    if all(arg_chk):
        return send_fail(event, response, MSG_AMBIGUOUS_PROPS)
    elif not any(arg_chk):
        return send_fail(event, response, MSG_MISSING_PROPS)

    # At this point it is known that only one of these is a thing
    isc = False
    try:
        resource_id = props['DBClusterIdentifier']
        fxname = 'describe_db_clusters'
        fxargs = {'DBClusterIdentifier': resource_id}
        response_key = 'DBClusters'
    except KeyError:
        resource_id = props['DBInstanceIdentifier']
        fxname = 'describe_db_instances'
        fxargs = {'DBInstanceIdentifier': resource_id}
        response_key = 'DBInstances'
        isc = True

    # PhysicalResourceId is meaningless here, but CloudFormation requires it
    # returning the RDS instance ID seems to make the most sense...
    response['PhysicalResourceId'] = resource_id

    # There is nothing to do for a delete request as no actual resources
    # are being managed
    if event['RequestType'] == 'Delete':
        return send_response(event, response)

    # Lookup the resource details
    try:
        client = boto3.client('rds')
        fx = getattr(client, fxname)
        resources = fx(**fxargs)
        logger.info("AWS response was: %s", resources)
        resource = resources[response_key][0]
    except Exception as E:
        return send_fail(event, response, str(E))

    # map CF response data to query response keys
    data_map = {
        'Engine': 'Engine',
        'EngineVersion': 'EngineVersion',
        'MasterUsername': 'MasterUsername',
        'IAMDatabaseAuthenticationEnabled': 'IAMDatabaseAuthenticationEnabled',
        'DBName': 'DBName' if isc else 'DatabaseName',
        'Endpoint.Address': 'Endpoint.Address' if isc else 'Endpoint',
        'Endpoint.Port': 'Endpoint.Port' if isc else 'Port',
        'ReadEndpoint.Address': 'Endpoint.Address' if isc else 'ReaderEndpoint',
        'ResourceId': 'DbiResourceId' if isc else 'DbClusterResourceId',
        'Arn': 'DBInstanceArn' if isc else 'DBClusterArn'
    }

    # the moto library does not currently include these keys in its
    # mock of the describe_db_instances response so we'll ignore them
    # during testing
    #
    # https://github.com/spulec/moto/issues/1465
    if 'pytest' in sys.modules:
        del data_map['IAMDatabaseAuthenticationEnabled']
        del data_map['ResourceId']

    # Set the response data
    try:
        response['Data'] = {
            data_key:get_data_value(data_key, resource, data_map)
            for data_key in data_map
        }
    except Exception as E:
        return send_fail(event, response, str(E))

    return send_response(event, response)
