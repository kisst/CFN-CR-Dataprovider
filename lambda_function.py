import json
import logging
import boto3
import cfnresponse

log = logging.getLogger()
# log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)

def flat_out_filter(cfn_filter):
    """ Flat out the filter structure """
    flat_filter = []
    for key in cfn_filter:
        condition = {}
        condition["Name"] = key
        condition["Values"] = []
        condition["Values"].append(cfn_filter[key])
        flat_filter.append(condition)
    return flat_filter


def handler(event, context):
    """Main Lambda Function"""
    response_data = {}

    log.debug("Received event: %s", json.dumps(event))
    filters = flat_out_filter(event["ResourceProperties"]["Filter"])
    log.debug("Where filters are: %s", filters)
    # Let's init the boto2 clients
    ec2 = boto3.client("ec2")

    if event["RequestType"] == "Delete":
        response_status = cfnresponse.SUCCESS
        cfnresponse.send(event, context, response_status, response_data)
        return

    if event["ResourceType"] == "Custom::Subnet":
        log.debug("Subnet lookup")
        search = ec2.describe_subnets(Filters=filters)
        if len(search["Subnets"]) == 1:
            subnet = search["Subnets"][0]
            response_status = cfnresponse.SUCCESS
            cfnresponse.send(event, context, response_status, subnet, subnet["SubnetId"])
        else:
            response_status = cfnresponse.FAILED
            cfnresponse.send(event, context, response_status, response_data)

    elif event["ResourceType"] == "Custom::VPC":
        log.debug("VPC lookup")
        search = ec2.describe_vpcs(Filters=filters)
        if len(search["Vpcs"]) == 1:
            vpc = search["Vpcs"][0]
            response_status = cfnresponse.SUCCESS
            cfnresponse.send(event, context, response_status, vpc, vpc["VpcId"])
        else:
            response_status = cfnresponse.FAILED
            cfnresponse.send(event, context, response_status, response_data)
    else:
        log.error("Unsupported resource lookup")
        response_status = cfnresponse.FAILED
        cfnresponse.send(event, context, response_status, response_data)
