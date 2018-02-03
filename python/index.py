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

    # Make sure the correct params were sent
    try:
        rds_id = event['ResourceProperties']['DBInstanceIdentifier']
    except KeyError:
        return send_fail(
            event,
            response,
            'Required resource property DBInstanceIdentifier is not set'
        )

    # PhysicalResourceId is meaningless here, but CloudFormation requires it
    # returning the RDS instance ID seems to make the most sense...
    response['PhysicalResourceId'] = rds_id

    # There is nothing to do for a delete request as no actual resources
    # are being managed
    if event['RequestType'] == 'Delete':
        return send_response(event, response)

    # Lookup the instance details
    try:
        client = boto3.client('rds')
        instances = client.describe_db_instances(DBInstanceIdentifier=rds_id)
        logger.info("AWS response was: %s", instances)
        instance = instances['DBInstances'][0]
    except Exception as E:
        return send_fail(event, response, str(E))

    # Set the response data
    response['Data'] = {}
    props = [
        'Engine', 'EngineVersion',
        'DBName', 'MasterUsername', 'DBInstanceArn',
        'Endpoint.Address', 'Endpoint.Port',
    ]

    # the moto library does not currently include these keys in its
    # mock of the describe_db_instances response so we'll ignore them
    # during testing
    #
    # https://github.com/spulec/moto/issues/1465
    if 'pytest' not in sys.modules:
        props += ['IAMDatabaseAuthenticationEnabled', 'DbiResourceId']

    for prop in props:
        if '.' in prop:
            x, y = prop.split('.')
            val = instance[x][y]
        else:
            val = instance[prop]

        response['Data'][prop] = val

    return send_response(event, response)
